"""
Incident Management API Routes
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import IncidentSeverity, IncidentStatus
from app.services.incident_service import IncidentService
from app.services.notification_service import NotificationService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])

# Initialize services
incident_service = IncidentService()
notification_service = NotificationService()


# Request/Response schemas
class CreateIncidentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    severity: IncidentSeverity
    affected_services: Optional[List[str]] = Field(default_factory=list)
    statuspage_incident_id: Optional[str] = None
    created_by: str = Field(..., min_length=1)
    tenant_id: str = Field(..., min_length=1)
    auto_create_banner: bool = Field(default=True)
    banner_message_override: Optional[str] = None


class UpdateIncidentRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[IncidentStatus] = None
    severity: Optional[IncidentSeverity] = None
    affected_services: Optional[List[str]] = None
    resolution_summary: Optional[str] = Field(None, max_length=1000)
    update_message: Optional[str] = Field(None, max_length=500)


class IncidentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: IncidentStatus
    severity: IncidentSeverity
    started_at: datetime
    resolved_at: Optional[datetime]
    affected_services: List[str]
    statuspage_incident_id: Optional[str]
    statuspage_status: Optional[str]
    auto_resolved: bool
    notifications_sent: bool
    last_notification_at: Optional[datetime]
    resolution_summary: Optional[str]
    created_by: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    incidents: List[IncidentResponse]
    pagination: Dict[str, Any]


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    request: CreateIncidentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new incident."""

    try:
        # Create the incident
        incident = await incident_service.create_incident(
            db=db,
            title=request.title,
            description=request.description,
            severity=request.severity,
            affected_services=request.affected_services,
            statuspage_incident_id=request.statuspage_incident_id,
            created_by=request.created_by,
            tenant_id=request.tenant_id,
            auto_create_banner=request.auto_create_banner,
            banner_message_override=request.banner_message_override
        )

        # Send notifications asynchronously
        notifications_sent = await notification_service.notify_incident_created(db, incident)

        logger.info(
            "Incident created via API",
            incident_id=str(incident.id),
            title=incident.title,
            severity=incident.severity.value,
            notifications_sent=notifications_sent
        )

        return IncidentResponse.model_validate(incident)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create incident", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create incident"
        )


@router.get("/", response_model=IncidentListResponse)
async def list_incidents(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    status: Optional[IncidentStatus] = Query(None, description="Filter by status"),
    severity: Optional[IncidentSeverity] = Query(None, description="Filter by severity"),
    service: Optional[str] = Query(None, description="Filter by affected service"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """List incidents with filtering and pagination."""

    try:
        result = await incident_service.list_incidents(
            db=db,
            tenant_id=tenant_id,
            status=status,
            severity=severity,
            affected_service=service,
            page=page,
            page_size=page_size
        )

        return IncidentListResponse(
            incidents=[IncidentResponse.model_validate(inc) for inc in result["incidents"]],
            pagination=result["pagination"]
        )

    except Exception as e:
        logger.error("Failed to list incidents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list incidents"
        )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific incident by ID."""

    try:
        incident = await incident_service.get_incident(db, incident_id)

        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )

        return IncidentResponse.model_validate(incident)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get incident", incident_id=str(incident_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get incident"
        )


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: uuid.UUID,
    request: UpdateIncidentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing incident."""

    try:
        # Get the incident first
        incident = await incident_service.get_incident(db, incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )

        # Store original status for notification logic
        original_status = incident.status

        # Update the incident
        updated_incident = await incident_service.update_incident(
            db=db,
            incident_id=incident_id,
            title=request.title,
            description=request.description,
            status=request.status,
            severity=request.severity,
            affected_services=request.affected_services,
            resolution_summary=request.resolution_summary
        )

        if not updated_incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )

        # Send notifications if there's an update message or status change
        if request.update_message or (request.status and request.status != original_status):
            message = request.update_message or f"Incident status changed to {request.status.value}"
            notifications_sent = await notification_service.notify_incident_updated(
                db, updated_incident, message
            )

            logger.info(
                "Incident update notifications sent",
                incident_id=str(incident_id),
                notifications_sent=notifications_sent
            )

        logger.info("Incident updated via API", incident_id=str(incident_id))

        return IncidentResponse.model_validate(updated_incident)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update incident", incident_id=str(incident_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update incident"
        )


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an incident (soft delete)."""

    try:
        success = await incident_service.delete_incident(db, incident_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )

        logger.info("Incident deleted via API", incident_id=str(incident_id))

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete incident", incident_id=str(incident_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete incident"
        )


@router.post("/{incident_id}/sync-statuspage", response_model=IncidentResponse)
async def sync_statuspage(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Manually sync incident with statuspage.io."""

    try:
        incident = await incident_service.get_incident(db, incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )

        success = await incident_service.sync_with_statuspage(db, incident)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to sync with statuspage"
            )

        # Refresh the incident to get updated data
        await db.refresh(incident)

        logger.info("Incident synced with statuspage", incident_id=str(incident_id))

        return IncidentResponse.model_validate(incident)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to sync statuspage", incident_id=str(incident_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync with statuspage"
        )


@router.get("/active/count")
async def get_active_incidents_count(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get count of active incidents."""

    try:
        count = await incident_service.get_active_incidents_count(db, tenant_id)

        return {"active_incidents": count}

    except Exception as e:
        logger.error("Failed to get active incidents count", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active incidents count"
        )


@router.post("/auto-resolve", status_code=status.HTTP_200_OK)
async def run_auto_resolve(
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger auto-resolution of stale incidents."""

    try:
        resolved_count = await incident_service.auto_resolve_stale_incidents(db)

        logger.info("Auto-resolve completed", resolved_count=resolved_count)

        return {"resolved_incidents": resolved_count}

    except Exception as e:
        logger.error("Failed to run auto-resolve", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run auto-resolve"
        )
