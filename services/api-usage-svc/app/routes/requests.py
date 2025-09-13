"""Quota increase request endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import QuotaIncreaseRequest, RequestStatus

router = APIRouter(prefix="/requests", tags=["requests"])


# Request/Response Models
class QuotaIncreaseCreateRequest(BaseModel):
    """Request model for creating a quota increase request."""

    tenant_id: str = Field(..., description="Tenant ID")
    service_name: str = Field(..., description="Service name")
    route_pattern: str = Field(..., description="Route pattern")
    current_limit: int = Field(..., ge=0, description="Current limit value")
    requested_limit: int = Field(..., gt=0, description="Requested limit value")
    limit_type: str = Field(..., description="Type of limit being increased")
    justification: str = Field(..., min_length=10, description="Business justification")
    business_impact: Optional[str] = Field(None, description="Business impact description")
    expected_usage_pattern: Optional[str] = Field(None, description="Expected usage pattern")
    duration_needed: Optional[str] = Field("permanent", description="Duration: temporary, permanent")
    requested_by: str = Field(..., description="Requester name/ID")


class QuotaIncreaseUpdateRequest(BaseModel):
    """Request model for updating a quota increase request."""

    justification: Optional[str] = Field(None, min_length=10, description="Updated justification")
    business_impact: Optional[str] = Field(None, description="Business impact description")
    expected_usage_pattern: Optional[str] = Field(None, description="Expected usage pattern")
    duration_needed: Optional[str] = Field(None, description="Duration needed")


class QuotaIncreaseReviewRequest(BaseModel):
    """Request model for reviewing a quota increase request."""

    status: RequestStatus = Field(..., description="Review decision")
    approved_limit: Optional[int] = Field(None, gt=0, description="Approved limit (if approved)")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason (if rejected)")
    reviewed_by: str = Field(..., description="Reviewer name/ID")


class QuotaIncreaseImplementRequest(BaseModel):
    """Request model for implementing a quota increase."""

    implementation_notes: Optional[str] = Field(None, description="Implementation notes")
    implemented_by: str = Field(..., description="Implementer name/ID")


class QuotaIncreaseResponse(BaseModel):
    """Response model for quota increase request."""

    id: str
    tenant_id: str
    service_name: str
    route_pattern: str
    current_limit: int
    requested_limit: int
    limit_type: str
    justification: str
    business_impact: Optional[str]
    expected_usage_pattern: Optional[str]
    duration_needed: Optional[str]
    status: str
    requested_by: str
    requested_at: datetime
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    approved_limit: Optional[int]
    rejection_reason: Optional[str]
    implemented_by: Optional[str]
    implemented_at: Optional[datetime]
    implementation_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequestSummaryResponse(BaseModel):
    """Summary of quota increase requests."""

    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    implemented_requests: int
    average_processing_time_hours: float
    recent_requests: List[QuotaIncreaseResponse]


@router.post("/", response_model=QuotaIncreaseResponse, status_code=status.HTTP_201_CREATED)
async def create_quota_increase_request(
    request: QuotaIncreaseCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new quota increase request."""
    try:
        # Validate that requested limit is higher than current limit
        if request.requested_limit <= request.current_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested limit must be higher than current limit"
            )

        quota_request = QuotaIncreaseRequest(**request.model_dump())
        db.add(quota_request)
        await db.commit()
        await db.refresh(quota_request)

        return QuotaIncreaseResponse.model_validate(quota_request)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=List[QuotaIncreaseResponse])
async def list_quota_increase_requests(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    status: Optional[RequestStatus] = Query(None, description="Filter by status"),
    requested_by: Optional[str] = Query(None, description="Filter by requester"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset results"),
    db: AsyncSession = Depends(get_db),
):
    """List quota increase requests with filtering."""
    try:
        filters = []

        if tenant_id:
            filters.append(QuotaIncreaseRequest.tenant_id == tenant_id)
        if service_name:
            filters.append(QuotaIncreaseRequest.service_name == service_name)
        if status:
            filters.append(QuotaIncreaseRequest.status == status.value)
        if requested_by:
            filters.append(QuotaIncreaseRequest.requested_by == requested_by)

        result = await db.execute(
            select(QuotaIncreaseRequest)
            .where(and_(*filters) if filters else True)
            .order_by(desc(QuotaIncreaseRequest.requested_at))
            .limit(limit)
            .offset(offset)
        )

        requests = result.scalars().all()
        return [QuotaIncreaseResponse.model_validate(req) for req in requests]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{request_id}", response_model=QuotaIncreaseResponse)
async def get_quota_increase_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get quota increase request by ID."""
    try:
        result = await db.execute(
            select(QuotaIncreaseRequest).where(QuotaIncreaseRequest.id == request_id)
        )
        quota_request = result.scalar_one_or_none()

        if not quota_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quota increase request not found"
            )

        return QuotaIncreaseResponse.model_validate(quota_request)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{request_id}", response_model=QuotaIncreaseResponse)
async def update_quota_increase_request(
    request_id: str,
    request: QuotaIncreaseUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update quota increase request (only allowed for pending requests)."""
    try:
        result = await db.execute(
            select(QuotaIncreaseRequest).where(QuotaIncreaseRequest.id == request_id)
        )
        quota_request = result.scalar_one_or_none()

        if not quota_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quota increase request not found"
            )

        # Only allow updates for pending requests
        if quota_request.status != RequestStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only update pending requests"
            )

        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(quota_request, field, value)

        quota_request.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(quota_request)

        return QuotaIncreaseResponse.model_validate(quota_request)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{request_id}/review", response_model=QuotaIncreaseResponse)
async def review_quota_increase_request(
    request_id: str,
    review: QuotaIncreaseReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Review a quota increase request (approve/reject)."""
    try:
        result = await db.execute(
            select(QuotaIncreaseRequest).where(QuotaIncreaseRequest.id == request_id)
        )
        quota_request = result.scalar_one_or_none()

        if not quota_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quota increase request not found"
            )

        # Only allow review for pending requests
        if quota_request.status != RequestStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only review pending requests"
            )

        # Validate review data
        if review.status == RequestStatus.APPROVED and not review.approved_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approved limit is required when approving request"
            )

        if review.status == RequestStatus.REJECTED and not review.rejection_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason is required when rejecting request"
            )

        # Update request
        quota_request.status = review.status.value
        quota_request.reviewed_by = review.reviewed_by
        quota_request.reviewed_at = datetime.utcnow()
        quota_request.updated_at = datetime.utcnow()

        if review.status == RequestStatus.APPROVED:
            quota_request.approved_limit = review.approved_limit
        elif review.status == RequestStatus.REJECTED:
            quota_request.rejection_reason = review.rejection_reason

        await db.commit()
        await db.refresh(quota_request)

        return QuotaIncreaseResponse.model_validate(quota_request)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{request_id}/implement", response_model=QuotaIncreaseResponse)
async def implement_quota_increase_request(
    request_id: str,
    implement: QuotaIncreaseImplementRequest,
    db: AsyncSession = Depends(get_db),
):
    """Mark a quota increase request as implemented."""
    try:
        result = await db.execute(
            select(QuotaIncreaseRequest).where(QuotaIncreaseRequest.id == request_id)
        )
        quota_request = result.scalar_one_or_none()

        if not quota_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quota increase request not found"
            )

        # Only allow implementation for approved requests
        if quota_request.status != RequestStatus.APPROVED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only implement approved requests"
            )

        # Update request
        quota_request.status = RequestStatus.IMPLEMENTED.value
        quota_request.implemented_by = implement.implemented_by
        quota_request.implemented_at = datetime.utcnow()
        quota_request.implementation_notes = implement.implementation_notes
        quota_request.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(quota_request)

        return QuotaIncreaseResponse.model_validate(quota_request)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quota_increase_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete quota increase request (only allowed for pending/rejected requests)."""
    try:
        result = await db.execute(
            select(QuotaIncreaseRequest).where(QuotaIncreaseRequest.id == request_id)
        )
        quota_request = result.scalar_one_or_none()

        if not quota_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quota increase request not found"
            )

        # Only allow deletion for pending or rejected requests
        if quota_request.status not in [RequestStatus.PENDING.value, RequestStatus.REJECTED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only delete pending or rejected requests"
            )

        await db.delete(quota_request)
        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/summary/overview", response_model=RequestSummaryResponse)
async def get_requests_summary(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get summary of quota increase requests."""
    try:
        filters = []
        if tenant_id:
            filters.append(QuotaIncreaseRequest.tenant_id == tenant_id)

        # Overall stats
        result = await db.execute(
            select(
                func.count(QuotaIncreaseRequest.id).label("total_requests"),
                func.sum(func.case((QuotaIncreaseRequest.status == RequestStatus.PENDING.value, 1), else_=0)).label("pending_requests"),
                func.sum(func.case((QuotaIncreaseRequest.status == RequestStatus.APPROVED.value, 1), else_=0)).label("approved_requests"),
                func.sum(func.case((QuotaIncreaseRequest.status == RequestStatus.REJECTED.value, 1), else_=0)).label("rejected_requests"),
                func.sum(func.case((QuotaIncreaseRequest.status == RequestStatus.IMPLEMENTED.value, 1), else_=0)).label("implemented_requests"),
            )
            .where(and_(*filters) if filters else True)
        )

        summary = result.fetchone()

        # Calculate average processing time for completed requests
        processing_time_result = await db.execute(
            select(
                func.avg(
                    func.extract("epoch", QuotaIncreaseRequest.reviewed_at - QuotaIncreaseRequest.requested_at) / 3600
                ).label("avg_processing_hours")
            )
            .where(
                and_(
                    QuotaIncreaseRequest.reviewed_at.is_not(None),
                    *filters if filters else [True]
                )
            )
        )

        avg_processing_time = processing_time_result.scalar() or 0.0

        # Recent requests
        recent_result = await db.execute(
            select(QuotaIncreaseRequest)
            .where(and_(*filters) if filters else True)
            .order_by(desc(QuotaIncreaseRequest.requested_at))
            .limit(10)
        )

        recent_requests = recent_result.scalars().all()

        return RequestSummaryResponse(
            total_requests=summary.total_requests or 0,
            pending_requests=summary.pending_requests or 0,
            approved_requests=summary.approved_requests or 0,
            rejected_requests=summary.rejected_requests or 0,
            implemented_requests=summary.implemented_requests or 0,
            average_processing_time_hours=round(avg_processing_time, 2),
            recent_requests=[QuotaIncreaseResponse.model_validate(req) for req in recent_requests],
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/pending/assignments", response_model=List[QuotaIncreaseResponse])
async def get_pending_assignments(
    reviewer: Optional[str] = Query(None, description="Filter by reviewer assignments"),
    db: AsyncSession = Depends(get_db),
):
    """Get pending quota increase requests for review."""
    try:
        filters = [QuotaIncreaseRequest.status == RequestStatus.PENDING.value]

        if reviewer:
            # This could be enhanced to include assignment logic
            pass

        result = await db.execute(
            select(QuotaIncreaseRequest)
            .where(and_(*filters))
            .order_by(QuotaIncreaseRequest.requested_at)  # FIFO processing
        )

        pending_requests = result.scalars().all()
        return [QuotaIncreaseResponse.model_validate(req) for req in pending_requests]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
