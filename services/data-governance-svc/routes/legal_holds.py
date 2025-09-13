"""
Legal Holds API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_db
from ..models import LegalHoldStatus, EntityType
from ..schemas.legal_holds import (
    LegalHoldCreate, LegalHoldUpdate, LegalHoldResponse,
    LegalHoldListResponse, LegalHoldImpactResponse
)
from ..services.legal_hold_service import LegalHoldService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("", response_model=LegalHoldResponse)
@limiter.limit("10/minute")
async def create_legal_hold(
    request,
    hold_data: LegalHoldCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new legal hold."""
    service = LegalHoldService(db)

    hold = await service.create_hold(hold_data)
    return hold


@router.get("", response_model=LegalHoldListResponse)
@limiter.limit("30/minute")
async def list_legal_holds(
    request,
    status_filter: Optional[LegalHoldStatus] = Query(None, alias="status", description="Filter by status"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    case_number: Optional[str] = Query(None, description="Filter by case number"),
    entity_type: Optional[EntityType] = Query(None, description="Filter by entity type"),
    active_only: bool = Query(False, description="Show only active holds"),
    limit: int = Query(50, ge=1, le=100, description="Number of holds to return"),
    offset: int = Query(0, ge=0, description="Number of holds to skip"),
    db: AsyncSession = Depends(get_db)
):
    """List legal holds with filtering and pagination."""
    service = LegalHoldService(db)

    holds, total = await service.list_holds(
        status=status_filter,
        tenant_id=tenant_id,
        case_number=case_number,
        entity_type=entity_type,
        active_only=active_only,
        limit=limit,
        offset=offset
    )

    return LegalHoldListResponse(
        holds=holds,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{hold_id}", response_model=LegalHoldResponse)
@limiter.limit("30/minute")
async def get_legal_hold(
    request,
    hold_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific legal hold by ID."""
    service = LegalHoldService(db)

    hold = await service.get_hold(hold_id)
    if not hold:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal hold not found"
        )

    return hold


@router.put("/{hold_id}", response_model=LegalHoldResponse)
@limiter.limit("10/minute")
async def update_legal_hold(
    request,
    hold_id: str,
    hold_data: LegalHoldUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update legal hold."""
    service = LegalHoldService(db)

    hold = await service.update_hold(hold_id, hold_data)
    if not hold:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal hold not found"
        )

    return hold


@router.delete("/{hold_id}")
@limiter.limit("5/minute")
async def release_legal_hold(
    request,
    hold_id: str,
    release_reason: Optional[str] = Query(None, description="Reason for releasing the hold"),
    db: AsyncSession = Depends(get_db)
):
    """Release (deactivate) a legal hold."""
    service = LegalHoldService(db)

    success = await service.release_hold(hold_id, release_reason)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal hold not found or already released"
        )

    return {"message": "Legal hold released successfully"}


@router.get("/{hold_id}/impact", response_model=LegalHoldImpactResponse)
@limiter.limit("20/minute")
async def get_hold_impact(
    request,
    hold_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get impact analysis of legal hold (blocked deletions, affected data)."""
    service = LegalHoldService(db)

    impact = await service.get_hold_impact(hold_id)
    if not impact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal hold not found"
        )

    return impact


@router.post("/{hold_id}/extend")
@limiter.limit("10/minute")
async def extend_legal_hold(
    request,
    hold_id: str,
    new_expiry_date: Optional[str] = Query(None, description="New expiry date (ISO format)"),
    extension_reason: Optional[str] = Query(None, description="Reason for extension"),
    db: AsyncSession = Depends(get_db)
):
    """Extend the expiry date of a legal hold."""
    service = LegalHoldService(db)

    from datetime import datetime
    expiry_datetime = None
    if new_expiry_date:
        try:
            expiry_datetime = datetime.fromisoformat(new_expiry_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )

    success = await service.extend_hold(hold_id, expiry_datetime, extension_reason)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal hold not found or cannot be extended"
        )

    return {"message": "Legal hold extended successfully"}


@router.get("/{hold_id}/blocked-requests")
@limiter.limit("30/minute")
async def get_blocked_requests(
    request,
    hold_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get DSR requests blocked by this legal hold."""
    service = LegalHoldService(db)

    blocked_requests = await service.get_blocked_requests(hold_id)
    return {
        "hold_id": hold_id,
        "blocked_requests": blocked_requests,
        "count": len(blocked_requests)
    }


@router.post("/check-conflicts")
@limiter.limit("20/minute")
async def check_deletion_conflicts(
    request,
    subject_ids: List[str],
    entity_types: List[EntityType],
    tenant_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Check if subjects have active legal holds that would block deletion."""
    service = LegalHoldService(db)

    conflicts = await service.check_deletion_conflicts(
        subject_ids=subject_ids,
        entity_types=entity_types,
        tenant_id=tenant_id
    )

    return {
        "conflicts": conflicts,
        "has_conflicts": len(conflicts) > 0
    }


@router.get("/active/summary")
@limiter.limit("20/minute")
async def get_active_holds_summary(
    request,
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get summary of all active legal holds."""
    service = LegalHoldService(db)

    summary = await service.get_active_holds_summary(tenant_id=tenant_id)
    return summary


@router.post("/bulk-release")
@limiter.limit("5/minute")
async def bulk_release_holds(
    request,
    hold_ids: List[str],
    release_reason: str,
    db: AsyncSession = Depends(get_db)
):
    """Release multiple legal holds at once."""
    service = LegalHoldService(db)

    if len(hold_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 holds allowed per bulk release"
        )

    results = await service.bulk_release_holds(hold_ids, release_reason)

    return {
        "released_holds": [r for r in results if r["success"]],
        "failed_holds": [r for r in results if not r["success"]],
        "total_released": len([r for r in results if r["success"]])
    }
