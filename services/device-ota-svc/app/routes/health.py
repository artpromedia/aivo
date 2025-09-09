"""Health check endpoints for Device OTA & Heartbeat Service."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Check service health."""
    try:
        # Test database connection
        await db.execute("SELECT 1")
        db_status = "healthy"
    except SQLAlchemyError:
        db_status = "unhealthy"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "unhealthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        dependencies={
            "database": db_status,
        },
        metrics={
            # NOTE: Uptime tracking not implemented yet
            "uptime_seconds": 0,
        },
    )


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Check if service is ready to serve requests."""
    try:
        await db.execute("SELECT 1")
        return {"status": "ready", "timestamp": datetime.utcnow()}
    except SQLAlchemyError:
        return {"status": "not_ready", "timestamp": datetime.utcnow()}


@router.get("/live")
async def liveness_check() -> dict:
    """Check if service is alive."""
    return {"status": "alive", "timestamp": datetime.utcnow()}
