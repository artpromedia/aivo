"""
Health check API endpoints.

Service health monitoring and system status reporting.
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_db, get_settings, is_database_healthy


router = APIRouter()


def get_service_info() -> Dict[str, Any]:
    """Get basic service information."""
    settings = get_settings()
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "development" if settings.DEBUG else "production"
    }


async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and health."""
    try:
        healthy = await is_database_healthy()
        return {
            "status": "healthy" if healthy else "unhealthy",
            "type": "postgresql",
            "connection": "ok" if healthy else "failed"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "type": "postgresql",
            "connection": "failed",
            "error": str(e)
        }


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": get_service_info()
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with dependencies."""
    database_health = await check_database_health()
    
    overall_status = "healthy" if database_health["status"] == "healthy" else "unhealthy"
    
    return {
        "status": overall_status,
        "service": get_service_info(),
        "dependencies": {
            "database": database_health
        }
    }


@router.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    db_healthy = await is_database_healthy()
    
    if not db_healthy:
        return {"status": "not ready", "reason": "database unavailable"}, 503
    
    return {"status": "ready"}


@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
