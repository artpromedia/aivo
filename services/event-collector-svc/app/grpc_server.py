"""gRPC server implementation for event collection."""
# pylint: disable=no-member,invalid-overridden-method
# pylint: disable=broad-exception-caught,protected-access

import asyncio

import grpc
import structlog
from grpc import aio

from app.config import settings
from app.models import LearnerEvent
from app.services.event_processor import EventProcessor

# type: ignore[attr-defined] applied to suppress pylint warnings about
# generated protobuf classes
from protos import (  # type: ignore[attr-defined]
    event_collector_pb2,
    event_collector_pb2_grpc,
)

logger = structlog.get_logger(__name__)


class EventCollectorServicer(
    event_collector_pb2_grpc.EventCollectorServiceServicer
):
    """gRPC service implementation for event collection."""

    def __init__(self) -> None:
        """Initialize the servicer."""
        self.processor: EventProcessor | None = None

    async def start(self) -> None:
        """Start the servicer and processor."""
        self.processor = EventProcessor()
        await self.processor.start()
        logger.info("gRPC event collector servicer started")

    async def stop(self) -> None:
        """Stop the servicer and processor."""
        if self.processor:
            await self.processor.stop()
        logger.info("gRPC event collector servicer stopped")

    def CollectEvents(
        self,
        request_iterator,  # type: ignore[no-untyped-def]
        context: grpc.ServicerContext,
    ):  # type: ignore[no-untyped-def]
        """Stream events with real-time processing."""
        if not self.processor:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Service not ready")
            return

        event_count = 0

        try:
            for request in request_iterator:
                try:
                    # Process events from the request
                    events = []
                    for event_proto in request.events:
                        # Convert protobuf to Pydantic model
                        timestamp_str = (
                            event_proto.timestamp.ToDatetime().isoformat()
                            + "Z"
                        )
                        metadata = (
                            dict(event_proto.metadata)
                            if event_proto.metadata
                            else {}
                        )

                        event_data = {
                            "learner_id": event_proto.learner_id,
                            "course_id": event_proto.data.get(
                                "course_id", ""
                            ),
                            "lesson_id": event_proto.data.get(
                                "lesson_id", ""
                            ),
                            "event_type": event_proto.event_type,
                            "event_data": dict(event_proto.data),
                            "timestamp": timestamp_str,
                            "session_id": event_proto.session_id or None,
                            "metadata": metadata,
                        }

                        event = LearnerEvent(**event_data)
                        events.append(event)
                        event_count += 1

                    # Process the batch
                    if events:
                        # Run async processor in sync context
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            result = loop.run_until_complete(
                                self.processor.collect_events(events)
                            )
                        finally:
                            loop.close()

                        message = (
                            f"Processed {result['accepted']}"
                            f"/{len(events)} events"
                        )
                        yield event_collector_pb2.EventResponse(  # type: ignore[attr-defined]  # noqa: E501
                            success=result["accepted"] > 0,
                            batch_id=result["batch_id"],
                            accepted=result["accepted"],
                            rejected=result["rejected"],
                            message=message,
                        )

                except (ValueError, KeyError, TypeError) as e:
                    logger.error(
                        "Error processing event batch",
                        error=str(e),
                        event_count=event_count,
                    )
                    yield event_collector_pb2.EventResponse(  # type: ignore[attr-defined]  # noqa: E501
                        success=False,
                        message=f"Error processing batch: {str(e)}",
                    )

            logger.info("Event stream completed", total_events=event_count)

        except (grpc.RpcError, RuntimeError) as e:
            logger.error(
                "Error in event stream",
                error=str(e),
                total_events=event_count,
            )
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Stream error: {str(e)}")

    def Health(
        self,
        request,  # type: ignore[no-untyped-def]
        context: grpc.ServicerContext,
    ):  # type: ignore[no-untyped-def]
        """Health check endpoint."""
        try:
            if not self.processor:
                return event_collector_pb2.HealthResponse(  # type: ignore[attr-defined]  # noqa: E501
                    status="unhealthy",
                    message="Service not ready - processor not initialized",
                )

            # Run async health check in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                checks = loop.run_until_complete(
                    self.processor.health_check()
                )
            finally:
                loop.close()

            status = (
                "healthy" if checks.get("status") == "healthy" else "unhealthy"
            )

            return event_collector_pb2.HealthResponse(  # type: ignore[attr-defined]  # noqa: E501
                status=status,
                message=checks.get("message", ""),
                timestamp=checks.get("timestamp", ""),
            )

        except (ValueError, RuntimeError, ConnectionError) as e:
            logger.error("Error in health check", error=str(e))
            return event_collector_pb2.HealthResponse(  # type: ignore[attr-defined]  # noqa: E501
                status="unhealthy",
                message=f"Health check failed: {str(e)}",
            )

    def Readiness(
        self,
        request,  # type: ignore[no-untyped-def]
        context: grpc.ServicerContext,
    ):  # type: ignore[no-untyped-def]
        """Perform readiness check."""
        try:
            if not self.processor:
                return event_collector_pb2.ReadinessResponse(  # type: ignore[attr-defined]  # noqa: E501
                    ready=False,
                    service=settings.service_name,
                )

            ready = self.processor.is_ready()
            kafka_connected = self.processor.kafka.is_connected()

            return event_collector_pb2.ReadinessResponse(  # type: ignore[attr-defined]  # noqa: E501
                ready=ready and kafka_connected,
                service=settings.service_name,
            )

        except (ValueError, RuntimeError, ConnectionError) as e:
            logger.error("Error in gRPC readiness check", error=str(e))
            return event_collector_pb2.ReadinessResponse(  # type: ignore[attr-defined]  # noqa: E501
                ready=False,
                service=settings.service_name,
            )


async def create_grpc_server() -> aio.Server:
    """Create and configure the gRPC server."""
    # Create servicer
    servicer = EventCollectorServicer()

    # Create server
    server = aio.server(
        options=[
            ("grpc.keepalive_time_ms", 30000),
            ("grpc.keepalive_timeout_ms", 5000),
            ("grpc.keepalive_permit_without_calls", True),
            ("grpc.http2.max_pings_without_data", 0),
            ("grpc.http2.min_time_between_pings_ms", 10000),
            ("grpc.http2.min_ping_interval_without_data_ms", 300000),
        ]
    )

    # Add servicer to server
    event_collector_pb2_grpc.add_EventCollectorServiceServicer_to_server(
        servicer, server
    )

    # Configure listen address
    listen_addr = f"{settings.grpc_host}:{settings.grpc_port}"
    server.add_insecure_port(listen_addr)

    logger.info("gRPC server configured", address=listen_addr)

    # Store servicer reference for lifecycle management
    # pylint: disable=protected-access
    server._servicer = servicer  # type: ignore

    return server


async def start_grpc_server(server: aio.Server) -> None:
    """Start the gRPC server."""
    # pylint: disable=protected-access
    await server._servicer.start()  # type: ignore
    await server.start()
    logger.info("gRPC server started", port=settings.grpc_port)


async def stop_grpc_server(server: aio.Server) -> None:
    """Stop the gRPC server."""
    await server.stop(grace=5.0)
    # pylint: disable=protected-access
    await server._servicer.stop()  # type: ignore
    logger.info("gRPC server stopped")


async def serve_grpc() -> None:
    """Main function to run the gRPC server."""
    server = await create_grpc_server()

    try:
        await start_grpc_server(server)
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
    finally:
        await stop_grpc_server(server)


if __name__ == "__main__":
    asyncio.run(serve_grpc())
