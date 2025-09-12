"""
API endpoints for the Approval Service.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .approval_service import approval_service
from .database import get_db
from .enums import ApprovalStatus, ApprovalType, Priority
from .schemas import (
    ApprovalCreateInput,
    ApprovalCreationResult,
    ApprovalListQuery,
    ApprovalListResponse,
    ApprovalResponse,
    DecisionInput,
    DecisionResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("", response_model=ApprovalCreationResult)
async def create_approval(
    approval_data: ApprovalCreateInput, db: AsyncSession = Depends(get_db)
) -> ApprovalCreationResult:
    """Create a new approval request."""
    try:
        approval = await approval_service.create_approval(db, approval_data)

        return ApprovalCreationResult(
            success=True,
            message="Approval created successfully",
            approval_id=approval.id,
        )

    except ValueError as e:
        logger.warning("Validation error creating approval: %s", e)
        return ApprovalCreationResult(success=False, message="Validation error", errors=[str(e)])
    except Exception as e:
        logger.error("Failed to create approval: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: UUID,
    tenant_id: str | None = Query(None, description="Tenant ID for filtering"),
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    """Get approval by ID."""
    approval = await approval_service.get_approval(db, approval_id, tenant_id)

    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    return approval


@router.get("", response_model=ApprovalListResponse)
async def list_approvals(
    tenant_id: str | None = Query(None, description="Tenant ID for filtering"),
    status: ApprovalStatus | None = Query(None, description="Filter by status"),
    approval_type: ApprovalType | None = Query(None, description="Filter by type"),
    priority: Priority | None = Query(None, description="Filter by priority"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    created_by: str | None = Query(None, description="Filter by creator"),
    participant_user_id: str | None = Query(None, description="Filter by participant"),
    expires_before: datetime | None = Query(None, description="Filter by expiry before date"),
    expires_after: datetime | None = Query(None, description="Filter by expiry after date"),
    created_before: datetime | None = Query(None, description="Filter by creation before date"),
    created_after: datetime | None = Query(None, description="Filter by creation after date"),
    limit: int = Query(default=50, ge=1, le=1000, description="Number of items to return"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    order_by: str = Query(default="created_at", description="Field to order by"),
    order_desc: bool = Query(default=True, description="Order in descending order"),
    db: AsyncSession = Depends(get_db),
) -> ApprovalListResponse:
    """List approvals with filtering and pagination."""
    query = ApprovalListQuery(
        tenant_id=tenant_id,
        status=status,
        approval_type=approval_type,
        priority=priority,
        resource_type=resource_type,
        created_by=created_by,
        participant_user_id=participant_user_id,
        expires_before=expires_before,
        expires_after=expires_after,
        created_before=created_before,
        created_after=created_after,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_desc=order_desc,
    )

    result = await approval_service.list_approvals(db, query)

    return ApprovalListResponse(**result)


@router.post("/{approval_id}/decision", response_model=DecisionResult)
async def make_decision(
    approval_id: UUID,
    decision_data: DecisionInput,
    user_id: str = Query(..., description="ID of the user making the decision"),
    tenant_id: str | None = Query(None, description="Tenant ID for filtering"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
) -> DecisionResult:
    """Make a decision (approve/reject) on an approval request."""
    # Extract request metadata
    request_metadata = {}
    if request:
        request_metadata = {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

    result = await approval_service.make_decision(
        db, approval_id, user_id, decision_data, tenant_id, request_metadata
    )

    if not result.success:
        if "not found" in result.message.lower():
            raise HTTPException(status_code=404, detail=result.message)
        elif "expired" in result.message.lower():
            raise HTTPException(status_code=410, detail=result.message)
        elif "already" in result.message.lower():
            raise HTTPException(status_code=409, detail=result.message)
        else:
            raise HTTPException(status_code=400, detail=result.message)

    return result


@router.post("/{approval_id}/cancel")
async def cancel_approval(
    approval_id: UUID,
    user_id: str = Query(  # pylint: disable=unused-argument
        ..., description="ID of the user cancelling the approval"
    ),
    tenant_id: str | None = Query(None, description="Tenant ID for filtering"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Cancel an approval request."""
    # This is a simplified version - in a real implementation you'd want to:
    # 1. Check permissions (only creator or admin can cancel)
    # 2. Update the approval status to CANCELLED
    # 3. Send notifications
    # 4. Send webhooks

    approval = await approval_service.get_approval(db, approval_id, tenant_id)

    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel approval with status " f"{approval.status.value}",
        )

    # NOTE: Cancellation logic is pending implementation
    # Future implementation should:
    # 1. Check permissions (only creator or admin can cancel)
    # 2. Update the approval status to CANCELLED
    # 3. Send notifications and webhooks
    return {"message": "Approval cancellation not yet implemented"}


@router.get("/{approval_id}/status")
async def get_approval_status(
    approval_id: UUID,
    tenant_id: str | None = Query(None, description="Tenant ID for filtering"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get approval status and progress."""
    approval = await approval_service.get_approval(db, approval_id, tenant_id)

    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    return {
        "approval_id": approval.id,
        "status": approval.status,
        "is_expired": approval.is_expired,
        "expires_at": approval.expires_at,
        "completed_at": approval.completed_at,
        "approval_progress": approval.approval_progress,
        "participants_summary": [
            {
                "user_id": p.user_id,
                "role": p.role,
                "has_responded": p.has_responded,
                "has_approved": p.has_approved,
                "has_rejected": p.has_rejected,
            }
            for p in approval.participants
        ],
    }
