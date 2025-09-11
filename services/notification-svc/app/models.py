"""Enhanced data models for notification service with IEP support."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class NotificationChannel(str, Enum):
    """Available notification delivery channels."""

    WEBSOCKET = "websocket"
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class IEPReminderType(str, Enum):
    """Specific IEP reminder notification types."""

    MEETING_REMINDER = "iep_meeting_reminder"
    DEADLINE_WARNING = "iep_deadline_warning"
    DOCUMENT_READY = "iep_document_ready"
    PARENT_CONSENT = "iep_parent_consent"
    REVIEW_DUE = "iep_review_due"
    ANNUAL_REVIEW = "iep_annual_review"
    TRANSITION_PLANNING = "iep_transition_planning"
    PROGRESS_REPORT = "iep_progress_report"


class NotificationType(str, Enum):
    """General notification categories."""

    IEP_REMINDER = "iep_reminder"
    MEETING_ALERT = "meeting_alert"
    DEADLINE_WARNING = "deadline_warning"
    DOCUMENT_NOTIFICATION = "document_notification"
    SYSTEM_MESSAGE = "system_message"
    URGENT_ALERT = "urgent_alert"
    GENERAL = "general"


class PushSubscription(BaseModel):
    """Web Push subscription data."""

    endpoint: str = Field(..., description="Push service endpoint URL")
    keys: dict[str, str] = Field(..., description="Encryption keys")

    @field_validator("keys")
    @classmethod
    def validate_keys(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate push subscription keys."""
        required_keys = {"p256dh", "auth"}
        if not all(key in v for key in required_keys):
            raise ValueError(f"Missing required keys: {required_keys - set(v.keys())}")
        return v


class NotificationData(BaseModel):
    """Base notification data structure."""

    # IEP-specific fields
    student_name: str | None = Field(None, description="Student name for IEP notifications")
    student_id: str | None = Field(None, description="Student identifier")
    meeting_date: datetime | None = Field(None, description="IEP meeting date/time")
    deadline_date: datetime | None = Field(None, description="IEP deadline date")
    location: str | None = Field(None, description="Meeting location")
    attendees: list[str] | None = Field(None, description="Meeting attendees")
    action_required: str | None = Field(None, description="Required action")
    days_remaining: int | None = Field(None, description="Days until deadline")

    # General notification fields
    title: str | None = Field(None, description="Notification title")
    message: str | None = Field(None, description="Notification message")
    url: str | None = Field(None, description="Associated URL")
    document_type: str | None = Field(None, description="Document type")

    # Custom data
    custom_fields: dict[str, Any] | None = Field(None, description="Additional custom data")


class NotificationRequest(BaseModel):
    """Request to send a notification."""

    user_id: str = Field(..., description="Target user ID")
    template_id: str = Field(..., description="Notification template identifier")
    notification_type: NotificationType = Field(..., description="Type of notification")
    channels: list[NotificationChannel] = Field(..., description="Preferred delivery channels")
    data: NotificationData = Field(..., description="Notification data")

    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL, description="Notification priority level"
    )
    locale: str = Field(default="en-US", description="Locale for message localization")
    phone_number: str | None = Field(None, description="Phone number for SMS fallback")
    ttl: int = Field(default=86400, description="Time to live in seconds")
    queue_if_offline: bool = Field(default=True, description="Queue message if user is offline")

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, v: list[NotificationChannel]) -> list[NotificationChannel]:
        """Validate notification channels."""
        if not v:
            raise ValueError("At least one notification channel is required")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str | None) -> str | None:
        """Validate phone number format."""
        if v is not None:
            # Basic phone number validation (international format)
            import re

            if not re.match(r"^\+[1-9]\d{1,14}$", v):
                raise ValueError("Phone number must be in international format (+1234567890)")
        return v


class NotificationResponse(BaseModel):
    """Response from notification sending."""

    notification_id: str = Field(..., description="Unique notification identifier")
    channels: dict[str, str] = Field(..., description="Delivery status for each channel")
    timestamp: str = Field(..., description="Notification timestamp")
    queued: bool | None = Field(None, description="Whether message was queued")
    estimated_delivery: str | None = Field(None, description="Estimated delivery time")
    websocket_connections: int | None = Field(
        None, description="Number of WebSocket connections reached"
    )
    replay_id: str | None = Field(None, description="Message replay ID for WebSocket")


class NotificationTemplate(BaseModel):
    """Notification template definition."""

    id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Human-readable template name")
    category: str = Field(..., description="Template category")
    description: str = Field(..., description="Template description")
    required_data: list[str] = Field(..., description="Required data fields")
    supported_locales: list[str] = Field(..., description="Supported locale codes")
    channel_support: dict[str, bool] = Field(
        ..., description="Supported channels for this template"
    )

    # Template content
    websocket_template: str | None = Field(None, description="WebSocket message template")
    push_template: dict[str, str] | None = Field(None, description="Push notification template")
    sms_template: str | None = Field(None, description="SMS message template")
    email_template: dict[str, str] | None = Field(None, description="Email template")


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Message ID")
    type: str = Field(..., description="Message type")
    data: dict[str, Any] = Field(..., description="Message payload")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(), description="Message timestamp"
    )
    replay_id: str | None = Field(None, description="Sequence ID for replay")
    user_id: str | None = Field(None, description="Target user ID")


class ChannelStats(BaseModel):
    """Statistics for a notification channel."""

    sent: int = Field(default=0, description="Total messages sent")
    delivered: int = Field(default=0, description="Messages successfully delivered")
    failed: int = Field(default=0, description="Failed deliveries")
    success_rate: float = Field(default=0.0, description="Delivery success rate", ge=0.0, le=1.0)


class NotificationAnalytics(BaseModel):
    """Notification analytics data."""

    total_notifications: int = Field(..., description="Total notifications sent")
    delivery_stats: dict[str, ChannelStats] = Field(
        ..., description="Delivery statistics by channel"
    )
    notification_types: dict[str, int] = Field(..., description="Count by notification type")
    response_times: dict[str, float] = Field(..., description="Response time metrics")
    connection_stats: dict[str, Any] | None = Field(
        None, description="WebSocket connection statistics"
    )


class IEPNotificationData(NotificationData):
    """Enhanced notification data specifically for IEP reminders."""

    iep_id: str | None = Field(None, description="IEP document identifier")
    case_manager: str | None = Field(None, description="IEP case manager name")
    parent_guardian: str | None = Field(None, description="Parent/guardian name")
    school_district: str | None = Field(None, description="School district")
    grade_level: str | None = Field(None, description="Student grade level")
    disability_category: str | None = Field(None, description="Primary disability category")

    # Meeting-specific
    meeting_type: str | None = Field(None, description="Type of IEP meeting")
    agenda_items: list[str] | None = Field(None, description="Meeting agenda items")
    preparation_required: bool | None = Field(None, description="Preparation required flag")

    # Progress tracking
    goals_reviewed: int | None = Field(None, description="Number of goals reviewed")
    objectives_met: int | None = Field(None, description="Number of objectives met")
    services_hours: float | None = Field(None, description="Service hours per week")

    # Compliance
    compliance_status: str | None = Field(None, description="Compliance status")
    risk_level: str | None = Field(None, description="Risk assessment level")


class SMSMessage(BaseModel):
    """SMS message structure."""

    to: str = Field(..., description="Recipient phone number")
    body: str = Field(..., description="Message body", max_length=160)
    from_: str | None = Field(None, alias="from", description="Sender phone number")

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        """Validate SMS message body length."""
        if len(v) > 160:
            raise ValueError("SMS message body cannot exceed 160 characters")
        return v


class PushMessage(BaseModel):
    """Push notification message structure."""

    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    icon: str | None = Field(None, description="Notification icon URL")
    badge: str | None = Field(None, description="Badge icon URL")
    url: str | None = Field(None, description="Action URL")
    actions: list[dict[str, str]] | None = Field(None, description="Notification actions")
    data: dict[str, Any] | None = Field(None, description="Custom data")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate notification title length."""
        if len(v) > 100:
            raise ValueError("Notification title cannot exceed 100 characters")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        """Validate notification body length."""
        if len(v) > 300:
            raise ValueError("Notification body cannot exceed 300 characters")
        return v


class NotificationError(BaseModel):
    """Error response structure."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(), description="Error timestamp"
    )
    notification_id: str | None = Field(None, description="Associated notification ID")
