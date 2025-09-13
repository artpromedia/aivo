"""
Notification Subscription API Routes
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import IncidentSeverity, NotificationChannel
from app.services.notification_service import NotificationService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# Initialize service
notification_service = NotificationService()


# Request/Response schemas
class NotificationChannelSchema(BaseModel):
    type: NotificationChannel
    address: str = Field(..., min_length=1, description="Email, phone number, or webhook URL")
    name: Optional[str] = Field(None, description="Optional display name for the channel")


class CreateSubscriptionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    tenant_id: str = Field(..., min_length=1)
    channels: List[NotificationChannelSchema] = Field(..., min_items=1, max_items=5)
    min_severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM)
    service_filters: Optional[List[str]] = Field(
        default_factory=list,
        description="Only notify for incidents affecting these services"
    )
    user_id: Optional[str] = Field(None, description="User ID if this is a personal subscription")
    immediate_notification: bool = Field(default=True)
    digest_frequency: Optional[str] = Field(
        None,
        description="Digest frequency: daily, weekly, none"
    )
    quiet_hours_start: Optional[str] = Field(
        None,
        pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Quiet hours start time in HH:MM format"
    )
    quiet_hours_end: Optional[str] = Field(
        None,
        pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Quiet hours end time in HH:MM format"
    )
    created_by: str = Field(..., min_length=1)


class UpdateSubscriptionRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    channels: Optional[List[NotificationChannelSchema]] = Field(None, min_items=1, max_items=5)
    min_severity: Optional[IncidentSeverity] = None
    service_filters: Optional[List[str]] = None
    is_active: Optional[bool] = None
    immediate_notification: Optional[bool] = None
    digest_frequency: Optional[str] = None
    quiet_hours_start: Optional[str] = Field(
        None,
        pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    quiet_hours_end: Optional[str] = Field(
        None,
        pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    )


class SubscriptionResponse(BaseModel):
    id: str
    name: str
    tenant_id: str
    user_id: Optional[str]
    channels: List[Dict[str, Any]]
    min_severity: IncidentSeverity
    service_filters: List[str]
    is_active: bool
    immediate_notification: bool
    digest_frequency: Optional[str]
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    last_notified_at: Optional[datetime]
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    subscriptions: List[SubscriptionResponse]
    pagination: Dict[str, Any]


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: CreateSubscriptionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification subscription."""

    try:
        # Convert channel schemas to dictionaries
        channels = []
        for channel in request.channels:
            channels.append({
                "type": channel.type.value,
                "address": channel.address,
                "name": channel.name
            })

        subscription = await notification_service.create_subscription(
            db=db,
            tenant_id=request.tenant_id,
            name=request.name,
            channels=channels,
            min_severity=request.min_severity,
            service_filters=request.service_filters,
            user_id=request.user_id,
            immediate_notification=request.immediate_notification,
            digest_frequency=request.digest_frequency,
            quiet_hours_start=request.quiet_hours_start,
            quiet_hours_end=request.quiet_hours_end,
            created_by=request.created_by
        )

        logger.info(
            "Subscription created via API",
            subscription_id=str(subscription.id),
            tenant_id=subscription.tenant_id,
            channels=len(channels)
        )

        return SubscriptionResponse.model_validate(subscription)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create subscription", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )


@router.get("/", response_model=SubscriptionListResponse)
async def list_subscriptions(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    active_only: bool = Query(True, description="Show only active subscriptions"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """List notification subscriptions with filtering and pagination."""

    try:
        result = await notification_service.list_subscriptions(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            active_only=active_only,
            page=page,
            page_size=page_size
        )

        return SubscriptionListResponse(
            subscriptions=[
                SubscriptionResponse.model_validate(sub)
                for sub in result["subscriptions"]
            ],
            pagination=result["pagination"]
        )

    except Exception as e:
        logger.error("Failed to list subscriptions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list subscriptions"
        )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific subscription by ID."""

    try:
        subscription = await notification_service.get_subscription(db, subscription_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        return SubscriptionResponse.model_validate(subscription)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get subscription", subscription_id=str(subscription_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription"
        )


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: uuid.UUID,
    request: UpdateSubscriptionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing subscription."""

    try:
        # Convert channel schemas to dictionaries if provided
        channels = None
        if request.channels:
            channels = []
            for channel in request.channels:
                channels.append({
                    "type": channel.type.value,
                    "address": channel.address,
                    "name": channel.name
                })

        subscription = await notification_service.update_subscription(
            db=db,
            subscription_id=subscription_id,
            name=request.name,
            channels=channels,
            min_severity=request.min_severity,
            service_filters=request.service_filters,
            is_active=request.is_active,
            immediate_notification=request.immediate_notification,
            digest_frequency=request.digest_frequency,
            quiet_hours_start=request.quiet_hours_start,
            quiet_hours_end=request.quiet_hours_end
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        logger.info("Subscription updated via API", subscription_id=str(subscription_id))

        return SubscriptionResponse.model_validate(subscription)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update subscription", subscription_id=str(subscription_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription"
        )


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a subscription."""

    try:
        success = await notification_service.delete_subscription(db, subscription_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        logger.info("Subscription deleted via API", subscription_id=str(subscription_id))

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete subscription", subscription_id=str(subscription_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete subscription"
        )


@router.post("/{subscription_id}/test", status_code=status.HTTP_200_OK)
async def test_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Send a test notification to verify subscription channels."""

    try:
        subscription = await notification_service.get_subscription(db, subscription_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        if not subscription.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot test inactive subscription"
            )

        # Create a mock incident for testing
        from app.models import Incident, IncidentStatus

        mock_incident = type('MockIncident', (), {
            'id': uuid.uuid4(),
            'title': 'Test Notification',
            'description': 'This is a test notification to verify your subscription.',
            'status': IncidentStatus.INVESTIGATING,
            'severity': subscription.min_severity,
            'started_at': datetime.utcnow(),
            'affected_services': ['Test Service']
        })()

        # Send test notifications
        notifications_sent = 0
        for channel_config in subscription.channels:
            try:
                success = await notification_service._send_incident_notification(
                    db=db,
                    incident=mock_incident,
                    subscription=subscription,
                    channel_config=channel_config,
                    notification_type="test_notification"
                )

                if success:
                    notifications_sent += 1

            except Exception as e:
                logger.error(
                    "Failed to send test notification",
                    subscription_id=str(subscription_id),
                    channel=channel_config.get("type"),
                    error=str(e)
                )

        logger.info(
            "Test notifications sent",
            subscription_id=str(subscription_id),
            sent=notifications_sent,
            total=len(subscription.channels)
        )

        return {
            "notifications_sent": notifications_sent,
            "total_channels": len(subscription.channels),
            "success": notifications_sent > 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to test subscription", subscription_id=str(subscription_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test subscription"
        )
