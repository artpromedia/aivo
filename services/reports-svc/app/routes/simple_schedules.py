"""Simplified schedules routes for testing."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session, Schedule

router = APIRouter()

@router.get("/")
async def list_schedules(db: AsyncSession = Depends(get_db_session)):
    """List all schedules."""
    return {"schedules": [], "total": 0}

@router.get("/health")
async def schedules_health():
    """Schedules health check."""
    return {"status": "healthy", "module": "schedules"}
