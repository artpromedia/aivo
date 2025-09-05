"""FastAPI HTTP endpoints for event collection."""
# pylint: disable=import-error,no-name-in-module,no-member
# pylint: disable=broad-exception-caught,global-statement
# pylint: disable=global-variable-not-assigned,redefined-outer-name

import gzip
from datetime import datetime
from typing import Any

import orjson
import structlog
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import (
    CollectResponse,
    ErrorResponse,
    EventBatch,
    HealthResponse,
    LearnerEvent,
    ReadinessResponse,
)
from app.services.event_processor import EventProcessor

logger = structlog.get_logger(__name__)

# Global processor instance
processor: EventProcessor | None = None


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Event Collector Service",
        description="Collect learner events via HTTP and gRPC to Redpanda",
        version=settings.version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Startup/shutdown events
    @app.on_event("startup")
    async def startup_event() -> None:
        """Initialize services on startup."""
        global processor
        try:
            processor = EventProcessor()
            await processor.start()
            logger.info("Event collector service started")
        except Exception as e:
            logger.error(
                "Failed to start event collector service",
                error=str(e)
            )
            raise

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Cleanup on shutdown."""
        global processor
        if processor:
            await processor.stop()
            logger.info("Event collector service stopped")

    return app


app = create_app()


async def verify_api_key(request: Request) -> None:
    """Verify API key if configured."""
    if settings.api_key:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )

        token = auth_header.split(" ", 1)[1]
        if token != settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )


@app.post(
    "/collect",
    response_model=CollectResponse,
    summary="Collect batch of learner events",
    description=(
        "Accept a batch of learner events with optional gzip compression"
    )
)
async def collect_events(
    request: Request,
    response: Response
) -> CollectResponse:
    """Collect learner events via HTTP POST."""
    if not processor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

    try:
        # Verify API key if configured
        await verify_api_key(request)

        # Read request body
        body = await request.body()

        # Handle gzip compression
        content_encoding = request.headers.get("content-encoding", "").lower()
        if content_encoding == "gzip":
            try:
                body = gzip.decompress(body)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid gzip compression: {str(e)}"
                ) from e

        # Parse JSON
        try:
            if body:
                data = orjson.loads(body)
            else:
                raise ValueError("Empty request body")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON: {str(e)}"
            ) from e

        # Validate request size
        if len(body) > settings.max_batch_size_bytes:
            max_size = settings.max_batch_size_bytes
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Batch size exceeds limit of {max_size} bytes"
            )

        # Parse events
        try:
            if isinstance(data, list):
                # Direct list of events
                events = [LearnerEvent(**event_data) for event_data in data]
            elif isinstance(data, dict) and "events" in data:
                # EventBatch format
                batch = EventBatch(**data)
                events = batch.events
            else:
                raise ValueError("Invalid request format")

            # Validate batch size
            if len(events) > settings.max_batch_size:
                max_size = settings.max_batch_size
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=(
                        f"Batch contains {len(events)} events, "
                        f"max allowed: {max_size}"
                    )
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Event validation failed: {str(e)}"
            ) from e

        # Process events
        result = await processor.collect_events(events)

        # Set response status
        if result["accepted"] == 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
        elif result["rejected"] > 0:
            response.status_code = status.HTTP_207_MULTI_STATUS

        logger.info(
            "HTTP events collected",
            accepted=result["accepted"],
            rejected=result["rejected"],
            batch_id=result["batch_id"],
            source_ip=request.client.host if request.client else "unknown",
        )

        return CollectResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in collect endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) from e


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Get detailed health status of the service and its dependencies"
    )
)
async def health_check() -> HealthResponse:
    """Get service health status."""
    try:
        if not processor:
            checks = {
                "processor": {
                    "status": "unhealthy",
                    "error": "Not initialized"
                }
            }
            status_val = "unhealthy"
        else:
            checks = await processor.health_check()
            status_val = checks.get("status", "unhealthy")

        return HealthResponse(
            status=status_val,
            service=settings.service_name,
            version=settings.version,
            timestamp=datetime.utcnow(),
            checks=checks,
        )

    except Exception as e:
        logger.error("Error in health check", error=str(e))
        return HealthResponse(
            status="unhealthy",
            service=settings.service_name,
            version=settings.version,
            timestamp=datetime.utcnow(),
            checks={"error": str(e)},
        )


@app.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Service readiness check",
    description="Check if service is ready to accept requests"
)
async def readiness_check() -> ReadinessResponse:
    """Get service readiness status."""
    try:
        if not processor:
            return ReadinessResponse(
                ready=False,
                service=settings.service_name,
                timestamp=datetime.utcnow(),
                dependencies={"processor": False},
            )

        # Check readiness
        ready = processor.is_ready()
        kafka_connected = processor.kafka.is_connected()

        return ReadinessResponse(
            ready=ready,
            service=settings.service_name,
            timestamp=datetime.utcnow(),
            dependencies={
                "kafka": kafka_connected,
                "processor": ready,
            },
        )

    except Exception as e:
        logger.error("Error in readiness check", error=str(e))
        return ReadinessResponse(
            ready=False,
            service=settings.service_name,
            timestamp=datetime.utcnow(),
            dependencies={"error": str(e)},
        )


@app.get(
    "/metrics",
    summary="Service metrics",
    description="Get service metrics for monitoring"
)
async def get_metrics() -> dict[str, Any]:
    """Get service metrics."""
    try:
        if not processor:
            return {"error": "Service not ready"}

        return await processor.get_metrics()

    except Exception as e:
        logger.error("Error getting metrics", error=str(e))
        return {"error": str(e)}


@app.get(
    "/buffer/stats",
    summary="Buffer statistics",
    description="Get current buffer statistics"
)
async def get_buffer_stats() -> dict[str, Any]:
    """Get buffer statistics."""
    try:
        if not processor:
            return {"error": "Service not ready"}

        stats = await processor.buffer.get_stats()
        return stats.dict()

    except Exception as e:
        logger.error("Error getting buffer stats", error=str(e))
        return {"error": str(e)}


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    error_response = ErrorResponse(
        error=exc.detail,
        code=str(exc.status_code),
        timestamp=datetime.utcnow(),
        details={"path": str(request.url.path)},
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=str(request.url.path)
    )

    error_response = ErrorResponse(
        error="Internal server error",
        code="500",
        timestamp=datetime.utcnow(),
        details={"path": str(request.url.path)},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.dict(),
    )
