"""
FastAPI application for digital ink capture service.

This module provides the main FastAPI application with endpoints for
capturing stylus/finger strokes, storing them in S3, and triggering
recognition jobs.
"""
import logging
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from . import __version__
from .config import settings
from .database import create_tables, get_db, health_check
from .schemas import (
    ErrorResponse,
    HealthResponse,
    StrokeRequest,
    StrokeResponse,
)
from .services import InkCaptureService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Set up standard logging to work with structlog
logging.basicConfig(
    format="%(message)s",
    stream=None,
    level=getattr(logging, settings.log_level.upper()),
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[misc] # noqa: ANN201
    """
    Application lifespan context manager.

    Handles startup and shutdown operations including database
    table creation and cleanup tasks.
    """
    # Startup
    logger.info("Starting ink capture service", version=__version__)
    await create_tables()
    logger.info("Service startup complete")

    yield

    # Shutdown
    logger.info("Shutting down ink capture service")


# Create FastAPI application
app = FastAPI(
    title="Ink Capture Service",
    description=(
        "Digital ink capture service for stylus and finger input. "
        "Captures strokes, stores NDJSON pages in S3, and emits "
        "recognition events."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ink_service = InkCaptureService()


@app.get("/healthz", response_model=HealthResponse)
async def health_check_endpoint() -> HealthResponse:
    """
    Health check endpoint.

    Returns service health status and dependency information.
    """
    dependencies = await health_check()

    return HealthResponse(
        status="healthy" if all(
            status == "healthy" for status in dependencies.values()
        ) else "unhealthy",
        version=__version__,
        dependencies=dependencies,
    )


@app.post(
    "/strokes",
    response_model=StrokeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def submit_strokes(
    stroke_request: StrokeRequest,
    db: AsyncSession = Depends(get_db),
) -> StrokeResponse:
    """
    Submit digital ink strokes for processing.

    Processes a batch of digital ink strokes from stylus or finger input,
    validates consent and media policies, stores the data in S3 as NDJSON,
    and triggers recognition processing by emitting an INK_READY event.

    Args:
        stroke_request: Request containing session info and stroke data
        db: Database session dependency

    Returns:
        StrokeResponse with processing results including S3 storage key
        and recognition job ID

    Raises:
        HTTPException: If validation fails or processing encounters errors
    """
    try:
        logger.info(
            "Processing stroke submission",
            session_id=stroke_request.session_id,
            learner_id=stroke_request.learner_id,
            subject=stroke_request.subject,
            stroke_count=len(stroke_request.strokes),
            page_number=stroke_request.page_number,
        )

        response = await ink_service.process_strokes(stroke_request, db)

        logger.info(
            "Stroke submission processed successfully",
            session_id=response.session_id,
            page_id=response.page_id,
            stroke_count=response.stroke_count,
            recognition_job_id=response.recognition_job_id,
        )

        return response

    except ValueError as e:
        logger.warning(
            "Validation failed for stroke submission",
            session_id=stroke_request.session_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_failed", "message": str(e)},
        ) from e

    except RuntimeError as e:
        logger.error(
            "Processing failed for stroke submission",
            session_id=stroke_request.session_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "processing_failed", "message": str(e)},
        ) from e

    except Exception as e:
        logger.error(
            "Unexpected error processing stroke submission",
            session_id=stroke_request.session_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred",
            },
        ) from e


@app.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Get status information for an ink capture session.

    Args:
        session_id: Session identifier
        db: Database session dependency

    Returns:
        Dictionary with session status information

    Raises:
        HTTPException: If session not found
    """
    try:
        from uuid import UUID

        from sqlalchemy import select

        from .models import InkSession

        session_uuid = UUID(session_id)
        result = await db.execute(
            select(InkSession).where(InkSession.session_id == session_uuid)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "session_not_found",
                    "message": "Session not found"
                },
            )

        return {
            "session_id": str(session.session_id),
            "learner_id": str(session.learner_id),
            "subject": session.subject,
            "status": session.status,
            "page_count": session.page_count,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_session_id", "message": str(e)},
        ) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
