"""
Health check endpoint for service monitoring.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session, db_manager
from ..config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.

    Returns service status and basic information.
    """
    return {
        "status": "healthy",
        "service": "sso-svc",
        "version": "0.1.0",
        "environment": settings.environment
    }


@router.get("/health/detailed")
async def detailed_health_check(session: AsyncSession = Depends(get_session)):
    """
    Detailed health check including database connectivity.

    Returns comprehensive service health information including
    database connectivity and configuration status.
    """
    health_status = {
        "status": "healthy",
        "service": "sso-svc",
        "version": "0.1.0",
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # Check database connectivity
    try:
        db_healthy = await db_manager.health_check()
        health_status["checks"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "response_time_ms": None  # Could add timing here
        }
        if not db_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # Check Redis connectivity (if configured)
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(settings.get_redis_url())
        await redis_client.ping()
        await redis_client.close()

        health_status["checks"]["redis"] = {
            "status": "healthy"
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    # Check configuration
    try:
        config_issues = []

        # Check required SAML configuration
        if not settings.saml_certificate_file:
            config_issues.append("SAML certificate file not configured")
        if not settings.saml_private_key_file:
            config_issues.append("SAML private key file not configured")

        health_status["checks"]["configuration"] = {
            "status": "healthy" if not config_issues else "warning",
            "issues": config_issues
        }

        if config_issues and health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    except Exception as e:
        health_status["checks"]["configuration"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # Return appropriate HTTP status
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    elif health_status["status"] == "degraded":
        raise HTTPException(status_code=200, detail=health_status)

    return health_status


@router.get("/ready")
async def readiness_check(session: AsyncSession = Depends(get_session)):
    """
    Kubernetes readiness probe endpoint.

    Checks if the service is ready to receive traffic.
    """
    try:
        # Test database connection
        await session.execute("SELECT 1")

        return {
            "status": "ready",
            "service": "sso-svc"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e)
            }
        )


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.

    Simple check to verify the service is alive.
    """
    return {
        "status": "alive",
        "service": "sso-svc"
    }
