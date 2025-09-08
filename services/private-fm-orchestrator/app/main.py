"""
FastAPI application for Private Brain Orchestrator service.
"""

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from .database import create_tables, get_db
from .schemas import (
    ErrorResponse,
    HealthResponse,
    PrivateBrainRequestCreate,
    PrivateBrainRequestResponse,
    PrivateBrainStatus,
    PrivateBrainStatusResponse,
)
from .services import PrivateBrainOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Private Brain Orchestrator service...")
    await create_tables()
    logger.info("Database tables created/verified")

    yield

    # Shutdown
    logger.info("Shutting down Private Brain Orchestrator service...")


# Create FastAPI app
app = FastAPI(
    title="Private Brain Orchestrator",
    description="Federated AI Orchestrator for per-learner namespace & checkpoint management",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="private-fm-orchestrator",
        version="1.0.0",
        timestamp=datetime.now(UTC),
    )


@app.post("/private-brain/request", response_model=PrivateBrainRequestResponse)
async def request_private_brain(
    request_data: PrivateBrainRequestCreate, db: AsyncSession = Depends(get_db)
):
    """
    Request a private brain instance for a learner (internal endpoint).

    This endpoint is idempotent - multiple requests for the same learner
    will return the same instance and increment the request count.
    """
    try:
        orchestrator = PrivateBrainOrchestrator(db)
        instance, is_new_request = await orchestrator.request_private_brain(request_data)

        message = f"Private brain request {'created' if is_new_request else 'updated'} for learner {instance.learner_id}"

        return PrivateBrainRequestResponse(
            message=message,
            learner_id=instance.learner_id,
            status=instance.status,
            is_new_request=is_new_request,
        )

    except Exception as e:
        logger.error(f"Failed to process private brain request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process private brain request",
        )


@app.get("/private-brain/status/{learner_id}", response_model=PrivateBrainStatusResponse)
async def get_private_brain_status(learner_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get the status of a private brain instance for a learner.

    Returns the current status, namespace UID, and checkpoint hash if ready.
    """
    try:
        orchestrator = PrivateBrainOrchestrator(db)
        instance = await orchestrator.get_status(learner_id)

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No private brain instance found for learner {learner_id}",
            )

        return PrivateBrainStatusResponse.model_validate(instance)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get private brain status for learner {learner_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get private brain status",
        )


@app.get("/private-brain/status", response_model=dict[str, Any])
async def list_private_brain_instances(
    limit: int = 100,
    offset: int = 0,
    status_filter: PrivateBrainStatus = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List private brain instances (admin/monitoring endpoint).
    """
    try:
        from sqlalchemy import select

        from .models import PrivateBrainInstance

        query = select(PrivateBrainInstance)

        if status_filter:
            query = query.where(PrivateBrainInstance.status == status_filter)

        query = query.offset(offset).limit(limit).order_by(PrivateBrainInstance.created_at.desc())

        result = await db.execute(query)
        instances = result.scalars().all()

        return {
            "instances": [
                PrivateBrainStatusResponse.model_validate(instance).model_dump()
                for instance in instances
            ],
            "total": len(instances),
            "offset": offset,
            "limit": limit,
        }

    except Exception as e:
        logger.error(f"Failed to list private brain instances: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list private brain instances",
        )


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    error_response = ErrorResponse(
        error="HTTP Error", detail=exc.detail, timestamp=datetime.now(UTC)
    )
    return JSONResponse(status_code=exc.status_code, content=error_response.model_dump(mode="json"))


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    error_response = ErrorResponse(
        error="Server Error",
        detail=f"An unexpected error occurred: {exc}",
        timestamp=datetime.now(UTC),
    )
    return JSONResponse(status_code=500, content=error_response.model_dump(mode="json"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
