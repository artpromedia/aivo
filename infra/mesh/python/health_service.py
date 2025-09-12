"""
Health Check Service for gRPC Mesh Services.

Provides standardized health checking functionality for services in the mesh.
"""

import asyncio
import logging
import time

import grpc
from grpc import aio
from grpc_health.v1 import health_pb2, health_pb2_grpc

logger = logging.getLogger(__name__)


class HealthStatus:
    """Health status tracking for services."""

    def __init__(self) -> None:
        """Initialize health status."""
        self.serving = True
        self.last_check = time.time()
        self.check_count = 0
        self.error_count = 0
        self.dependencies: dict[str, bool] = {}

    def mark_healthy(self) -> None:
        """Mark service as healthy."""
        self.serving = True
        self.last_check = time.time()
        self.check_count += 1

    def mark_unhealthy(self) -> None:
        """Mark service as unhealthy."""
        self.serving = False
        self.last_check = time.time()
        self.error_count += 1

    def set_dependency_status(self, dependency: str, healthy: bool) -> None:
        """Set health status for a dependency."""
        self.dependencies[dependency] = healthy

    def is_healthy(self) -> bool:
        """Check if service is healthy including dependencies."""
        if not self.serving:
            return False

        # Check if any critical dependencies are unhealthy
        return all(self.dependencies.values())


class AsyncHealthServicer(health_pb2_grpc.HealthServicer):
    """Async implementation of gRPC health check service."""

    def __init__(self) -> None:
        """Initialize health servicer."""
        self._status = HealthStatus()
        self._service_status: dict[str, HealthStatus] = {}
        self._watchers: dict[str, list] = {}

    async def Check(
        self,
        request: health_pb2.HealthCheckRequest,
        context: grpc.aio.ServicerContext,
    ) -> health_pb2.HealthCheckResponse:
        """Handle health check requests."""
        service = request.service or ""

        try:
            if service == "":
                # Overall service health
                status = self._status
            else:
                # Specific service component health
                status = self._service_status.get(service, self._status)

            if status.is_healthy():
                response_status = health_pb2.HealthCheckResponse.SERVING
            else:
                response_status = health_pb2.HealthCheckResponse.NOT_SERVING

            logger.debug(
                "Health check for service '%s': %s",
                service,
                response_status,
            )

            return health_pb2.HealthCheckResponse(status=response_status)

        except Exception as e:
            logger.error("Health check error for service '%s': %s", service, e)
            await context.abort(grpc.StatusCode.INTERNAL, f"Health check failed: {e}")

    async def Watch(
        self,
        request: health_pb2.HealthCheckRequest,
        context: grpc.aio.ServicerContext,
    ) -> None:
        """Handle streaming health check requests."""
        service = request.service or ""

        try:
            # Add watcher for this service
            if service not in self._watchers:
                self._watchers[service] = []

            queue = asyncio.Queue()
            self._watchers[service].append(queue)

            # Send initial status
            if service == "":
                status = self._status
            else:
                status = self._service_status.get(service, self._status)

            initial_status = (
                health_pb2.HealthCheckResponse.SERVING
                if status.is_healthy()
                else health_pb2.HealthCheckResponse.NOT_SERVING
            )

            await context.write(health_pb2.HealthCheckResponse(status=initial_status))

            # Listen for status changes
            try:
                while True:
                    new_status = await queue.get()
                    await context.write(health_pb2.HealthCheckResponse(status=new_status))
            except asyncio.CancelledError:
                # Client disconnected
                pass
            finally:
                # Remove watcher
                if service in self._watchers:
                    try:
                        self._watchers[service].remove(queue)
                    except ValueError:
                        pass

        except Exception as e:
            logger.error("Health watch error for service '%s': %s", service, e)
            await context.abort(grpc.StatusCode.INTERNAL, f"Health watch failed: {e}")

    def set_serving(self, service: str = "") -> None:
        """Set service as serving."""
        if service == "":
            self._status.mark_healthy()
        else:
            if service not in self._service_status:
                self._service_status[service] = HealthStatus()
            self._service_status[service].mark_healthy()

        self._notify_watchers(service, health_pb2.HealthCheckResponse.SERVING)

    def set_not_serving(self, service: str = "") -> None:
        """Set service as not serving."""
        if service == "":
            self._status.mark_unhealthy()
        else:
            if service not in self._service_status:
                self._service_status[service] = HealthStatus()
            self._service_status[service].mark_unhealthy()

        self._notify_watchers(service, health_pb2.HealthCheckResponse.NOT_SERVING)

    def set_dependency_status(self, dependency: str, healthy: bool, service: str = "") -> None:
        """Set dependency health status."""
        if service == "":
            self._status.set_dependency_status(dependency, healthy)
        else:
            if service not in self._service_status:
                self._service_status[service] = HealthStatus()
            self._service_status[service].set_dependency_status(dependency, healthy)

    def _notify_watchers(
        self,
        service: str,
        status: health_pb2.HealthCheckResponse.ServingStatus,
    ) -> None:
        """Notify all watchers of status change."""
        if service in self._watchers:
            for queue in self._watchers[service]:
                try:
                    queue.put_nowait(status)
                except asyncio.QueueFull:
                    logger.warning("Health watcher queue full for service: %s", service)


class SyncHealthServicer(health_pb2_grpc.HealthServicer):
    """Synchronous implementation of gRPC health check service."""

    def __init__(self) -> None:
        """Initialize health servicer."""
        self._status = HealthStatus()
        self._service_status: dict[str, HealthStatus] = {}

    def Check(
        self,
        request: health_pb2.HealthCheckRequest,
        context: grpc.ServicerContext,
    ) -> health_pb2.HealthCheckResponse:
        """Handle health check requests."""
        service = request.service or ""

        try:
            if service == "":
                status = self._status
            else:
                status = self._service_status.get(service, self._status)

            if status.is_healthy():
                response_status = health_pb2.HealthCheckResponse.SERVING
            else:
                response_status = health_pb2.HealthCheckResponse.NOT_SERVING

            return health_pb2.HealthCheckResponse(status=response_status)

        except Exception as e:
            logger.error("Health check error for service '%s': %s", service, e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Health check failed: {e}")
            return health_pb2.HealthCheckResponse(status=health_pb2.HealthCheckResponse.NOT_SERVING)

    def set_serving(self, service: str = "") -> None:
        """Set service as serving."""
        if service == "":
            self._status.mark_healthy()
        else:
            if service not in self._service_status:
                self._service_status[service] = HealthStatus()
            self._service_status[service].mark_healthy()

    def set_not_serving(self, service: str = "") -> None:
        """Set service as not serving."""
        if service == "":
            self._status.mark_unhealthy()
        else:
            if service not in self._service_status:
                self._service_status[service] = HealthStatus()
            self._service_status[service].mark_unhealthy()


def add_health_servicer(server: grpc.Server) -> SyncHealthServicer:
    """Add health servicer to a gRPC server."""
    health_servicer = SyncHealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    return health_servicer


async def add_async_health_servicer(server: aio.Server) -> AsyncHealthServicer:
    """Add async health servicer to a gRPC server."""
    health_servicer = AsyncHealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    return health_servicer


class DependencyHealthChecker:
    """Periodic health checker for service dependencies."""

    def __init__(
        self,
        health_servicer: AsyncHealthServicer,
        check_interval: float = 30.0,
    ) -> None:
        """Initialize dependency health checker."""
        self.health_servicer = health_servicer
        self.check_interval = check_interval
        self.dependencies: dict[str, str] = {}  # name -> endpoint
        self._running = False
        self._task: asyncio.Task | None = None

    def add_dependency(self, name: str, endpoint: str) -> None:
        """Add a dependency to monitor."""
        self.dependencies[name] = endpoint
        logger.info("Added dependency health check: %s -> %s", name, endpoint)

    def remove_dependency(self, name: str) -> None:
        """Remove a dependency from monitoring."""
        if name in self.dependencies:
            del self.dependencies[name]
            logger.info("Removed dependency health check: %s", name)

    async def start(self) -> None:
        """Start periodic health checking."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._check_loop())
        logger.info("Started dependency health checker")

    async def stop(self) -> None:
        """Stop periodic health checking."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped dependency health checker")

    async def _check_loop(self) -> None:
        """Main health checking loop."""
        while self._running:
            try:
                await self._check_all_dependencies()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in health check loop: %s", e)
                await asyncio.sleep(min(self.check_interval, 10.0))

    async def _check_all_dependencies(self) -> None:
        """Check health of all dependencies."""
        if not self.dependencies:
            return

        # Check all dependencies concurrently
        tasks = [
            self._check_dependency(name, endpoint) for name, endpoint in self.dependencies.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for (name, _), result in zip(self.dependencies.items(), results):
            if isinstance(result, Exception):
                logger.warning("Health check failed for %s: %s", name, result)
                self.health_servicer.set_dependency_status(name, False)
            else:
                self.health_servicer.set_dependency_status(name, result)

    async def _check_dependency(self, name: str, endpoint: str) -> bool:
        """Check health of a single dependency."""
        try:
            # Create insecure channel for internal health checks
            async with aio.insecure_channel(endpoint) as channel:
                stub = health_pb2_grpc.HealthStub(channel)
                request = health_pb2.HealthCheckRequest()

                response = await stub.Check(request, timeout=5.0)
                healthy = response.status == health_pb2.HealthCheckResponse.SERVING

                if healthy:
                    logger.debug("Dependency %s is healthy", name)
                else:
                    logger.warning("Dependency %s is not serving", name)

                return healthy

        except Exception as e:
            logger.warning("Failed to check dependency %s: %s", name, e)
            return False


# Example usage
async def example_usage() -> None:
    """Example of how to use the health check service."""
    # Create async server
    server = aio.server()

    # Add health servicer
    health_servicer = await add_async_health_servicer(server)

    # Set up dependency monitoring
    dep_checker = DependencyHealthChecker(health_servicer)
    dep_checker.add_dependency("database", "postgres:5432")
    dep_checker.add_dependency("cache", "redis:6379")

    # Start server and dependency checker
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)

    await server.start()
    await dep_checker.start()

    # Mark service as serving
    health_servicer.set_serving()

    logger.info("Health check service started on %s", listen_addr)

    try:
        await server.wait_for_termination()
    finally:
        await dep_checker.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())
