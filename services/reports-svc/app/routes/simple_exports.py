"""Simplified exports routes for testing."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session, Export

router = APIRouter()

@router.get("/")
async def list_exports(db: AsyncSession = Depends(get_db_session)):
    """List all exports."""
    return {"exports": [], "total": 0}

@router.get("/health")
async def exports_health():
    """Exports health check."""
    return {"status": "healthy", "module": "exports"}
