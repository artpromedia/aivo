"""Simplified reports routes for testing."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session, Report

router = APIRouter()

@router.get("/")
async def list_reports(db: AsyncSession = Depends(get_db_session)):
    """List all reports."""
    # This is a simplified version for testing
    return {"reports": [], "total": 0}

@router.get("/health")
async def reports_health():
    """Reports health check."""
    return {"status": "healthy", "module": "reports"}
