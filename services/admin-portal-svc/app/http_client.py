"""
HTTP client service with circuit breaker and OpenTelemetry tracing.
"""

import logging
from typing import Any

import httpx
from opentelemetry import trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import get_settings

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class CircuitBreakerError(Exception):
    """Circuit breaker is open."""

    pass


class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise CircuitBreakerError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True

        import time

        return (time.time() - self.last_failure_time) >= self.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self) -> None:
        """Handle failed call."""
        import time

        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class HTTPClientService:
    """HTTP client service with circuit breaker, retries, and tracing."""

    def __init__(self) -> None:
        """Initialize HTTP client service."""
        self.settings = get_settings()
        self.client: httpx.AsyncClient | None = None
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

        # Initialize OpenTelemetry instrumentation
        HTTPXClientInstrumentor().instrument()

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.settings.http_timeout),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
        logger.info("HTTP client service initialized")

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()

    def _get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(
                failure_threshold=self.settings.circuit_breaker_failure_threshold,
                recovery_timeout=self.settings.circuit_breaker_recovery_timeout,
            )
        return self.circuit_breakers[service_name]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
    )
    async def _make_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with retries."""
        if not self.client:
            raise RuntimeError("HTTP client not initialized")

        response = await self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    async def request(self, service_name: str, method: str, url: str, **kwargs) -> dict[str, Any]:
        """Make HTTP request with circuit breaker and tracing."""
        circuit_breaker = self._get_circuit_breaker(service_name)

        with tracer.start_as_current_span(
            f"http_request_{service_name}",
            attributes={"http.method": method, "http.url": url, "service.name": service_name},
        ) as span:
            try:
                response = await circuit_breaker.call(self._make_request, method, url, **kwargs)

                data = response.json()
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_size", len(response.content))

                logger.debug(f"Successful request to {service_name}: {method} {url}")
                return data

            except CircuitBreakerError as e:
                span.set_attribute("circuit_breaker.state", "open")
                span.record_exception(e)
                logger.error(f"Circuit breaker open for {service_name}")
                raise

            except httpx.HTTPStatusError as e:
                span.set_attribute("http.status_code", e.response.status_code)
                span.record_exception(e)
                logger.error(f"HTTP error from {service_name}: {e.response.status_code}")
                raise

            except Exception as e:
                span.record_exception(e)
                logger.error(f"Request failed to {service_name}: {e}")
                raise

    async def get(self, service_name: str, url: str, **kwargs) -> dict[str, Any]:
        """Make GET request."""
        return await self.request(service_name, "GET", url, **kwargs)

    async def post(self, service_name: str, url: str, **kwargs) -> dict[str, Any]:
        """Make POST request."""
        return await self.request(service_name, "POST", url, **kwargs)

    async def put(self, service_name: str, url: str, **kwargs) -> dict[str, Any]:
        """Make PUT request."""
        return await self.request(service_name, "PUT", url, **kwargs)

    async def delete(self, service_name: str, url: str, **kwargs) -> dict[str, Any]:
        """Make DELETE request."""
        return await self.request(service_name, "DELETE", url, **kwargs)

    def get_circuit_breaker_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all circuit breakers."""
        status = {}
        for service_name, cb in self.circuit_breakers.items():
            status[service_name] = {
                "state": cb.state,
                "failure_count": cb.failure_count,
                "last_failure_time": cb.last_failure_time,
            }
        return status


# Global HTTP client service instance
http_client = HTTPClientService()
