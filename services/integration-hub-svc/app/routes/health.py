"""Health check endpoints."""

from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.database import get_db
from app.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.project_name,
        "version": settings.version,
        "environment": settings.environment,
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Readiness check with database connectivity."""
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1"))
        db_status = "healthy" if result.scalar() == 1 else "unhealthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "unhealthy"

    return {
        "status": "ready" if db_status == "healthy" else "not ready",
        "service": settings.project_name,
        "version": settings.version,
        "environment": settings.environment,
        "checks": {
            "database": db_status,
        },
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes."""
    return {
        "status": "alive",
        "service": settings.project_name,
        "version": settings.version,
    }
