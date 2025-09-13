"""Audit endpoints for creating and querying audit events."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config import settings
from app.database import get_db, get_readonly_db
from app.models.audit_event import AuditEvent
from app.services.audit_service import AuditService

logger = structlog.get_logger(__name__)
router = APIRouter()
audit_service = AuditService()


# Pydantic schemas
class AuditEventCreate(BaseModel):
    """Schema for creating an audit event."""

    actor: str = Field(..., min_length=1, max_length=255, description="User ID or system identifier")
    action: str = Field(..., min_length=1, max_length=100, description="Action performed")
    resource_type: str = Field(..., min_length=1, max_length=100, description="Type of resource")
    resource_id: Optional[str] = Field(None, max_length=255, description="Resource identifier")
    before_state: Optional[Dict[str, Any]] = Field(None, description="State before change")
    after_state: Optional[Dict[str, Any]] = Field(None, description="State after change")
    actor_role: Optional[str] = Field(None, max_length=100, description="Actor's role")
    request_id: Optional[str] = Field(None, max_length=255, description="Request correlation ID")
    session_id: Optional[str] = Field(None, max_length=255, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AuditEventResponse(BaseModel):
    """Schema for audit event response."""

    id: UUID
    timestamp: datetime
    actor: str
    actor_role: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    before_state: Optional[Dict[str, Any]]
    after_state: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    current_hash: str
    previous_hash: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditEventList(BaseModel):
    """Schema for audit event list response."""

    events: List[AuditEventResponse]
    pagination: Dict[str, Any]
    filters: Dict[str, Any]


class HashChainVerification(BaseModel):
    """Schema for hash chain verification response."""

    is_valid: bool
    total_events: int
    verified_events: int
    invalid_events: List[Dict[str, Any]]
    broken_chains: List[Dict[str, Any]]
    verification_timestamp: str


def extract_request_context(request: Request) -> Dict[str, Any]:
    """Extract IP address and user agent from request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    ip_address = None

    if forwarded_for:
        # Get the first IP in case of multiple proxies
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        ip_address = getattr(request.client, "host", None)

    user_agent = request.headers.get("User-Agent")

    return {
        "ip_address": ip_address,
        "user_agent": user_agent,
    }


@router.post("/audit", response_model=AuditEventResponse, status_code=status.HTTP_201_CREATED)
async def create_audit_event(
    audit_data: AuditEventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuditEventResponse:
    """Create a new immutable audit event."""
    try:
        # Extract request context
        request_context = extract_request_context(request)

        # Create audit event
        audit_event = await audit_service.create_audit_event(
            db=db,
            actor=audit_data.actor,
            action=audit_data.action,
            resource_type=audit_data.resource_type,
            resource_id=audit_data.resource_id,
            before_state=audit_data.before_state,
            after_state=audit_data.after_state,
            actor_role=audit_data.actor_role,
            ip_address=request_context["ip_address"],
            user_agent=request_context["user_agent"],
            request_id=audit_data.request_id,
            session_id=audit_data.session_id,
            metadata=audit_data.metadata,
        )

        return AuditEventResponse.model_validate(audit_event)

    except Exception as e:
        logger.error("Failed to create audit event", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create audit event"
        )


@router.get("/audit", response_model=AuditEventList)
async def search_audit_events(
    actor: Optional[str] = Query(None, description="Filter by actor"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource: Optional[str] = Query(None, description="Filter by resource type or ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    from_date: Optional[datetime] = Query(None, alias="from", description="Start date filter (ISO format)"),
    to_date: Optional[datetime] = Query(None, alias="to", description="End date filter (ISO format)"),
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    request_id: Optional[str] = Query(None, description="Filter by request ID"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Page size"),
    db: AsyncSession = Depends(get_readonly_db),
) -> AuditEventList:
    """Search audit events with filtering and pagination."""
    try:
        # Support both S2C-05 spec parameters (from/to) and descriptive parameters
        effective_start_date = from_date or start_date
        effective_end_date = to_date or end_date
        effective_resource_type = resource or resource_type

        result = await audit_service.search_audit_events(
            db=db,
            actor=actor,
            action=action,
            resource_type=effective_resource_type,
            resource_id=resource_id,
            start_date=effective_start_date,
            end_date=effective_end_date,
            request_id=request_id,
            ip_address=ip_address,
            page=page,
            page_size=page_size,
        )

        return AuditEventList(
            events=[AuditEventResponse.model_validate(event) for event in result["events"]],
            pagination=result["pagination"],
            filters=result["filters"],
        )

    except Exception as e:
        logger.error("Failed to search audit events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search audit events"
        )


@router.get("/audit/{event_id}", response_model=AuditEventResponse)
async def get_audit_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_readonly_db),
) -> AuditEventResponse:
    """Get a specific audit event by ID."""
    from sqlalchemy import select

    try:
        stmt = select(AuditEvent).where(AuditEvent.id == event_id)
        result = await db.execute(stmt)
        audit_event = result.scalar_one_or_none()

        if not audit_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit event not found"
            )

        return AuditEventResponse.model_validate(audit_event)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get audit event", event_id=str(event_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit event"
        )


@router.post("/audit/verify", response_model=HashChainVerification)
async def verify_hash_chain(
    start_id: Optional[UUID] = Query(None, description="Start verification from this event ID"),
    end_id: Optional[UUID] = Query(None, description="End verification at this event ID"),
    db: AsyncSession = Depends(get_readonly_db),
) -> HashChainVerification:
    """Verify the integrity of the audit hash chain."""
    try:
        verification_result = await audit_service.verify_hash_chain(
            db=db,
            start_id=start_id,
            end_id=end_id,
        )

        return HashChainVerification(**verification_result)

    except Exception as e:
        logger.error("Failed to verify hash chain", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify hash chain"
        )


@router.get("/audit/stats")
async def get_audit_stats(
    db: AsyncSession = Depends(get_readonly_db),
) -> Dict[str, Any]:
    """Get audit statistics for monitoring and reporting."""
    try:
        stats = await audit_service.get_audit_stats(db)
        return stats

    except Exception as e:
        logger.error("Failed to get audit stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit statistics"
        )
