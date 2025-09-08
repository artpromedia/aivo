"""Main application entry point for Event Collector service."""
# pylint: disable=unused-variable,unused-argument,broad-exception-caught

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import Any

import structlog
import uvicorn
from fastapi import FastAPI

from app.config import settings
from app.grpc_server import (
    create_grpc_server,
    start_grpc_server,
    stop_grpc_server,
)
from app.http_api import app as http_app

logger = structlog.get_logger(__name__)


class EventCollectorApp:
    """Main application orchestrator for Event Collector service."""

    def __init__(self) -> None:
        """Initialize the application."""
        self.grpc_server = None
        self.http_server = None
        self.shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start both HTTP and gRPC servers."""
        try:
            # Start gRPC server
            self.grpc_server = await create_grpc_server()
            await start_grpc_server(self.grpc_server)
            logger.info("gRPC server started", port=settings.grpc_port)

            # Configure HTTP server
            http_config = uvicorn.Config(
                app=http_app,
                host=settings.http_host,
                port=settings.http_port,
                log_level="info" if settings.debug else "warning",
                access_log=settings.debug,
                loop="asyncio",
                interface="asgi3",
            )

            # Start HTTP server
            self.http_server = uvicorn.Server(http_config)
            logger.info(
                "HTTP server starting",
                host=settings.http_host,
                port=settings.http_port,
            )

            # Create tasks for both servers
            http_task = asyncio.create_task(self.http_server.serve())
            grpc_task = asyncio.create_task(
                self.grpc_server.wait_for_termination()
            )

            logger.info(
                "Event Collector service started",
                http_port=settings.http_port,
                grpc_port=settings.grpc_port,
                version=settings.version,
            )

            # Wait for shutdown signal or server completion
            shutdown_task = asyncio.create_task(self.shutdown_event.wait())
            done, pending = await asyncio.wait(
                [http_task, grpc_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            logger.error(
                "Error starting Event Collector service", error=str(e)
            )
            raise

    async def stop(self) -> None:
        """Stop both servers gracefully."""
        logger.info("Shutting down Event Collector service...")

        try:
            # Stop HTTP server
            if self.http_server:
                self.http_server.should_exit = True
                await asyncio.sleep(0.1)  # Give it a moment to start shutdown

            # Stop gRPC server
            if self.grpc_server:
                await stop_grpc_server(self.grpc_server)

            logger.info("Event Collector service stopped")

        except Exception as e:
            logger.error(
                "Error stopping Event Collector service", error=str(e)
            )
            raise

    def signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        logger.info("Received shutdown signal", signal=signum)
        self.shutdown_event.set()


async def run_service() -> None:
    """Run the Event Collector service."""
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.INFO if not settings.debug else structlog.DEBUG
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Create and start application
    app = EventCollectorApp()

    # Setup signal handlers
    if sys.platform != "win32":
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, app.signal_handler, sig, None)
    else:
        # Windows doesn't support add_signal_handler
        signal.signal(signal.SIGTERM, app.signal_handler)
        signal.signal(signal.SIGINT, app.signal_handler)

    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Service failed", error=str(e))
        sys.exit(1)
    finally:
        await app.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for standalone HTTP server."""
    # This is used when running only the HTTP server
    logger.info("HTTP-only mode starting")
    yield
    logger.info("HTTP-only mode stopping")


# Alternative HTTP-only app for development
http_only_app = FastAPI(
    title="Event Collector Service (HTTP Only)",
    description="Event Collector HTTP API for development",
    version=settings.version,
    lifespan=lifespan,
)

# Copy routes from main HTTP app
http_only_app.router = http_app.router
http_only_app.middleware_stack = http_app.middleware_stack
http_only_app.exception_handlers = http_app.exception_handlers


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(run_service())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error("Service failed to start", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
