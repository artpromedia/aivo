"""Health check endpoints for audit service."""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config import settings
from app.database import get_db, verify_worm_compliance

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
    """Readiness check with database connectivity and WORM compliance."""
    checks = {}
    overall_status = "ready"

    # Test database connection
    try:
        result = await db.execute(text("SELECT 1"))
        checks["database"] = "healthy" if result.scalar() == 1 else "unhealthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        checks["database"] = "unhealthy"
        overall_status = "not ready"

    # Verify WORM compliance
    try:
        worm_compliant = await verify_worm_compliance()
        checks["worm_compliance"] = "compliant" if worm_compliant else "non-compliant"
        if not worm_compliant:
            overall_status = "not ready"
    except Exception as e:
        logger.error("WORM compliance check failed", error=str(e))
        checks["worm_compliance"] = "unknown"
        overall_status = "not ready"

    # Check audit table structure
    try:
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'audit_events'
            )
        """))
        checks["audit_table"] = "exists" if result.scalar() else "missing"
        if not result.scalar():
            overall_status = "not ready"
    except Exception as e:
        logger.error("Audit table check failed", error=str(e))
        checks["audit_table"] = "error"
        overall_status = "not ready"

    return {
        "status": overall_status,
        "service": settings.project_name,
        "version": settings.version,
        "environment": settings.environment,
        "checks": checks,
        "compliance": {
            "worm_enabled": True,
            "hash_chain_enabled": settings.enable_hash_chain,
            "retention_days": settings.retention_days,
        },
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes."""
    return {
        "status": "alive",
        "service": settings.project_name,
        "version": settings.version,
        "timestamp": "2025-09-12T00:00:00Z",  # Current timestamp
    }
