"""Data models for notification service."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class NotificationChannel(str, Enum):
    """Available notification channels."""

    WEBSOCKET = "websocket"
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"


class NotificationType(str, Enum):
    """Types of notifications."""

    IEP_REMINDER = "iep_reminder"
    MEETING_ALERT = "meeting_alert"
    DOCUMENT_UPDATE = "document_update"
    SYSTEM_MESSAGE = "system_message"
    URGENT_ALERT = "urgent_alert"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PushSubscription(BaseModel):
    """Web Push subscription model."""

    endpoint: str
    keys: dict[str, str]
    expiration_time: datetime | None = None

    @field_validator("keys")
    @classmethod
    def validate_keys(cls, v: dict[str, str]) -> dict[str, str]:
        """Ensure required keys are present."""
        required = {"p256dh", "auth"}
        if not required.issubset(v.keys()):
            raise ValueError(f"Missing required keys: {required - v.keys()}")
        return v


class WebSocketMessage(BaseModel):
    """WebSocket message format."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Any
    metadata: dict[str, Any] | None = None


class NotificationRequest(BaseModel):
    """Notification request model."""

    user_id: str
    notification_type: NotificationType
    channels: list[NotificationChannel]
    template_id: str
    data: dict[str, Any]
    locale: str = "en"
    priority: NotificationPriority = NotificationPriority.MEDIUM
    phone_number: str | None = None
    queue_if_offline: bool = True
    ttl: int = 86400  # 24 hours in seconds

    @field_validator("channels")
    @classmethod
    def validate_channels(
        cls, v: list[NotificationChannel]
    ) -> list[NotificationChannel]:
        """Ensure at least one channel is specified."""
        if not v:
            raise ValueError("At least one channel must be specified")
        return v


class NotificationTemplate(BaseModel):
    """Notification template model."""

    id: str
    name: str
    type: NotificationType
    locales: dict[str, dict[str, str]]
    variables: list[str]
    created_at: datetime
    updated_at: datetime


class NotificationLog(BaseModel):
    """Notification delivery log."""

    id: str
    user_id: str
    notification_type: NotificationType
    channels_attempted: list[NotificationChannel]
    channels_successful: list[NotificationChannel]
    template_id: str
    data: dict[str, Any]
    priority: NotificationPriority
    created_at: datetime
    delivered_at: datetime | None = None
    error: str | None = None
