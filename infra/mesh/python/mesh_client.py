"""
gRPC mesh client utilities for Python services.

This module provides utilities for connecting to the internal gRPC mesh
with mTLS authentication, circuit breaking, and observability.
"""

import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import grpc
from grpc import aio

# Optional imports for observability (graceful degradation if not available)
try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.instrumentation.grpc import (
        GrpcAioInstrumentorClient,
        GrpcAioInstrumentorServer,
    )
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MeshConfig:
    """Configuration for gRPC mesh connectivity."""

    service_name: str
    ca_cert_path: str = "/etc/ssl/certs/ca.crt"
    client_cert_path: str = "/etc/ssl/certs/service.crt"
    client_key_path: str = "/etc/ssl/private/service.key"
    envoy_outbound_port: int = 15001
    jaeger_endpoint: str = "http://jaeger:14268/api/traces"
    enable_tracing: bool = True
    enable_metrics: bool = True
    connection_timeout: float = 5.0
    request_timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 0.5
    keepalive_time_ms: int = 30000
    keepalive_timeout_ms: int = 5000

    def validate(self: "MeshConfig") -> None:
        """Validate configuration parameters."""
        if not self.service_name:
            msg = "service_name is required"
            raise ValueError(msg)

        cert_files = [
            self.ca_cert_path,
            self.client_cert_path,
            self.client_key_path,
        ]
        for cert_file in cert_files:
            if not Path(cert_file).exists():
                msg = f"Certificate file not found: {cert_file}"
                raise FileNotFoundError(msg)


class CircuitBreakerState:
    """Simple circuit breaker implementation for gRPC clients."""

    def __init__(
        self: "CircuitBreakerState",
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        timeout: float = 10.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call_allowed(self: "CircuitBreakerState") -> bool:
        """Check if a call is allowed based on circuit breaker state."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self: "CircuitBreakerState") -> None:
        """Record a successful operation."""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self: "CircuitBreakerState") -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
        elif self.state == "HALF_OPEN":
            self.state = "OPEN"


class MeshClient:
    """gRPC mesh client with mTLS, circuit breaking, and observability."""

    def __init__(self: "MeshClient", config: MeshConfig) -> None:
        self.config = config
        self.circuit_breakers: dict[str, CircuitBreakerState] = {}
        self._tracer = None
        self._setup_tracing()

    def _setup_tracing(self: "MeshClient") -> None:
        """Set up OpenTelemetry tracing for the mesh client."""
        if not self.config.enable_tracing or not OBSERVABILITY_AVAILABLE:
            return

        try:
            trace.set_tracer_provider(TracerProvider())
            tracer_provider = trace.get_tracer_provider()

            # Parse Jaeger endpoint
            endpoint_url = self.config.jaeger_endpoint.split("://")[1]
            jaeger_host = endpoint_url.split(":")[0]

            jaeger_exporter = JaegerExporter(
                agent_host_name=jaeger_host,
                agent_port=14268,
            )

            span_processor = BatchSpanProcessor(jaeger_exporter)
            tracer_provider.add_span_processor(span_processor)

            # Instrument gRPC clients
            GrpcAioInstrumentorClient().instrument()

            self._tracer = trace.get_tracer(__name__)
            logger.info("Tracing initialized for mesh client")

        except ImportError as e:
            logger.warning("Failed to initialize tracing: %s", e)
            self._tracer = None

    def _load_certificates(self: "MeshClient") -> grpc.ChannelCredentials:
        """Load mTLS certificates for secure communication."""
        try:
            # Load CA certificate
            ca_cert_path = Path(self.config.ca_cert_path)
            if not ca_cert_path.exists():
                msg = f"CA certificate not found: {ca_cert_path}"
                raise FileNotFoundError(msg)

            with ca_cert_path.open("rb") as f:
                ca_cert = f.read()

            # Load client certificate and key
            client_cert_path = Path(self.config.client_cert_path)
            client_key_path = Path(self.config.client_key_path)

            if not client_cert_path.exists():
                msg = f"Client certificate not found: {client_cert_path}"
                raise FileNotFoundError(msg)
            if not client_key_path.exists():
                msg = f"Client key not found: {client_key_path}"
                raise FileNotFoundError(msg)

            with client_cert_path.open("rb") as f:
                client_cert = f.read()
            with client_key_path.open("rb") as f:
                client_key = f.read()

            # Create SSL credentials
            credentials = grpc.ssl_channel_credentials(
                root_certificates=ca_cert,
                private_key=client_key,
                certificate_chain=client_cert,
            )

            logger.info("mTLS certificates loaded successfully")
            return credentials

        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error("Failed to load certificates: %s", e)
            raise

    def _get_circuit_breaker(
        self: "MeshClient", service_name: str
    ) -> CircuitBreakerState:
        """Get or create a circuit breaker for a service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreakerState()
        return self.circuit_breakers[service_name]

    @asynccontextmanager
    async def get_channel(
        self: "MeshClient", service_name: str, target_host: str | None = None
    ) -> AsyncGenerator[aio.Channel, None]:
        """
        Get a secure gRPC channel to a service through the mesh.

        Args:
            service_name: Name of the target service
            target_host: Optional override for target host

        Yields:
            Configured gRPC channel
        """
        circuit_breaker = self._get_circuit_breaker(service_name)

        if not circuit_breaker.call_allowed():
            msg = f"Circuit breaker OPEN for service: {service_name}"
            raise grpc.RpcError(msg)

        target = target_host or f"localhost:{self.config.envoy_outbound_port}"
        credentials = self._load_certificates()

        # Channel options for optimal gRPC performance
        options = [
            ("grpc.keepalive_time_ms", self.config.keepalive_time_ms),
            ("grpc.keepalive_timeout_ms", self.config.keepalive_timeout_ms),
            ("grpc.keepalive_permit_without_calls", True),
            ("grpc.http2.max_pings_without_data", 0),
            ("grpc.http2.min_time_between_pings_ms", 10000),
            ("grpc.http2.min_ping_interval_without_data_ms", 300000),
            ("grpc.so_reuseport", 1),
            ("grpc.max_message_length", 100 * 1024 * 1024),  # 100MB
            # Add Host header for Envoy routing
            (
                "grpc.primary_user_agent",
                f"mesh-client/{self.config.service_name}",
            ),
        ]

        channel = aio.secure_channel(target, credentials, options=options)

        try:
            # Test connection with timeout
            await asyncio.wait_for(
                channel.channel_ready(), timeout=self.config.connection_timeout
            )
            circuit_breaker.record_success()
            logger.debug("Connected to service: %s", service_name)

            yield channel

        except (grpc.RpcError, asyncio.TimeoutError, OSError) as e:
            circuit_breaker.record_failure()
            logger.error(
                "Failed to connect to service %s: %s", service_name, e
            )
            raise
        finally:
            await channel.close()

    async def call_with_retry(
        self: "MeshClient",
        channel: aio.Channel,
        method_name: str,
        request: Any,
        service_name: str,
        metadata: list | None = None,
    ) -> Any:
        """
        Make a gRPC call with retry logic and circuit breaking.

        Args:
            channel: gRPC channel
            method_name: Name of the gRPC method to call
            request: Request message
            service_name: Name of the target service
            metadata: Optional gRPC metadata

        Returns:
            Response from the gRPC call
        """
        circuit_breaker = self._get_circuit_breaker(service_name)
        metadata = metadata or []

        # Add tracing metadata
        if self._tracer:
            metadata.append(("service", service_name))
            metadata.append(("method", method_name))

        for attempt in range(self.config.max_retries + 1):
            if not circuit_breaker.call_allowed():
                msg = f"Circuit breaker OPEN for service: {service_name}"
                raise grpc.RpcError(msg)

            try:
                # Create the RPC method from the channel
                rpc_method = getattr(channel, method_name)

                # Make the call with timeout
                if self._tracer:
                    with self._tracer.start_as_current_span(
                        f"{service_name}.{method_name}"
                    ) as span:
                        span.set_attribute("service.name", service_name)
                        span.set_attribute("rpc.method", method_name)
                        span.set_attribute("attempt", attempt + 1)

                        response = await asyncio.wait_for(
                            rpc_method(request, metadata=metadata),
                            timeout=self.config.request_timeout,
                        )
                        span.set_attribute("success", True)
                else:
                    response = await asyncio.wait_for(
                        rpc_method(request, metadata=metadata),
                        timeout=self.config.request_timeout,
                    )

                circuit_breaker.record_success()
                logger.debug(
                    "Successful call to %s.%s", service_name, method_name
                )
                return response

            except (grpc.RpcError, TimeoutError) as e:
                circuit_breaker.record_failure()

                if attempt == self.config.max_retries:
                    logger.error(
                        "Failed call to %s.%s after %d attempts: %s",
                        service_name,
                        method_name,
                        attempt + 1,
                        e,
                    )
                    raise

                # Calculate retry delay with exponential backoff
                delay = self.config.retry_delay * (2**attempt)
                logger.warning(
                    "Call to %s.%s failed (attempt %d), retrying in %gs: %s",
                    service_name,
                    method_name,
                    attempt + 1,
                    delay,
                    e,
                )
                await asyncio.sleep(delay)

        msg = f"Max retries exceeded for {service_name}.{method_name}"
        raise grpc.RpcError(msg)


def setup_server_tracing(service_name: str, jaeger_endpoint: str) -> None:
    """Set up server-side tracing for a gRPC service."""
    try:
        trace.set_tracer_provider(TracerProvider())
        tracer_provider = trace.get_tracer_provider()

        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_endpoint.split("://")[1].split(":")[0],
            agent_port=14268,
        )

        span_processor = BatchSpanProcessor(jaeger_exporter)
        tracer_provider.add_span_processor(span_processor)

        # Instrument gRPC servers
        GrpcAioInstrumentorServer().instrument()

        logger.info("Server tracing initialized for %s", service_name)

    except ImportError as e:
        logger.warning("Failed to initialize server tracing: %s", e)


def create_mesh_config_from_env() -> MeshConfig:
    """Create MeshConfig from environment variables."""
    return MeshConfig(
        service_name=os.getenv("SERVICE_NAME", "unknown"),
        ca_cert_path=os.getenv("CA_CERT_PATH", "/etc/ssl/certs/ca.crt"),
        client_cert_path=os.getenv(
            "CLIENT_CERT_PATH", "/etc/ssl/certs/service.crt"
        ),
        client_key_path=os.getenv(
            "CLIENT_KEY_PATH", "/etc/ssl/private/service.key"
        ),
        envoy_outbound_port=int(os.getenv("ENVOY_OUTBOUND_PORT", "15001")),
        jaeger_endpoint=os.getenv(
            "JAEGER_ENDPOINT", "http://jaeger:14268/api/traces"
        ),
        enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true",
        enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
        connection_timeout=float(os.getenv("CONNECTION_TIMEOUT", "5.0")),
        request_timeout=float(os.getenv("REQUEST_TIMEOUT", "30.0")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        retry_delay=float(os.getenv("RETRY_DELAY", "0.5")),
    )


# Example usage
if __name__ == "__main__":

    async def example_usage() -> None:
        """Example of using the mesh client."""
        config = create_mesh_config_from_env()
        client = MeshClient(config)

        async with client.get_channel("event-collector-svc") as _:
            # Example: call a method on the channel
            # response = await client.call_with_retry(
            #     channel, "Health", health_request, "event-collector-svc"
            # )
            logger.info("Connected to mesh successfully")

    asyncio.run(example_usage())
