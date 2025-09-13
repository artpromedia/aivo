"""
Database models for Incident Center Service
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Index, String, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base model class."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class IncidentStatus(str, Enum):
    """Incident status values."""
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    POSTMORTEM = "postmortem"


class IncidentSeverity(str, Enum):
    """Incident severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BannerType(str, Enum):
    """Banner types."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    MAINTENANCE = "maintenance"


class NotificationChannel(str, Enum):
    """Notification channel types."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"


class Incident(Base, TimestampMixin):
    """Incident model."""

    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Basic incident information
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status and severity
    status: Mapped[IncidentStatus] = mapped_column(
        SQLEnum(IncidentStatus),
        nullable=False,
        default=IncidentStatus.INVESTIGATING
    )

    severity: Mapped[IncidentSeverity] = mapped_column(
        SQLEnum(IncidentSeverity),
        nullable=False,
        default=IncidentSeverity.MEDIUM
    )

    # External integration
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    statuspage_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timeline
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Impact and components
    affected_services: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    impact_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Assignment and management
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

    # Additional metadata
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Notification tracking
    notifications_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    last_notification_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    updates: Mapped[List["IncidentUpdate"]] = relationship(
        "IncidentUpdate",
        back_populates="incident",
        cascade="all, delete-orphan"
    )

    # Database indexes
    __table_args__ = (
        Index('idx_incident_status', 'status'),
        Index('idx_incident_severity', 'severity'),
        Index('idx_incident_started_at', 'started_at'),
        Index('idx_incident_external_id', 'external_id'),
        Index('idx_incident_created_by', 'created_by'),
    )

    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, title='{self.title}', status='{self.status}')>"


class IncidentUpdate(Base, TimestampMixin):
    """Incident update/status change model."""

    __tablename__ = "incident_updates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False
    )

    # Update content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Status change
    new_status: Mapped[IncidentStatus] = mapped_column(
        SQLEnum(IncidentStatus),
        nullable=False
    )

    # Update metadata
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)

    # External sync
    statuspage_update_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    # Relationship
    incident: Mapped["Incident"] = relationship("Incident", back_populates="updates")

    # Database indexes
    __table_args__ = (
        Index('idx_incident_update_incident_id', 'incident_id'),
        Index('idx_incident_update_created_at', 'created_at'),
        Index('idx_incident_update_status', 'new_status'),
    )

    def __repr__(self) -> str:
        return f"<IncidentUpdate(id={self.id}, incident_id={self.incident_id})>"


class Banner(Base, TimestampMixin):
    """Admin banner announcement model."""

    __tablename__ = "banners"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Banner content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Banner type and styling
    banner_type: Mapped[BannerType] = mapped_column(
        SQLEnum(BannerType),
        nullable=False,
        default=BannerType.INFO
    )

    # Display settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_dismissible: Mapped[bool] = mapped_column(Boolean, default=True)
    show_in_admin: Mapped[bool] = mapped_column(Boolean, default=True)
    show_in_tenant: Mapped[bool] = mapped_column(Boolean, default=False)

    # Targeting
    target_tenants: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    target_roles: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Timing
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Management
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(default=0)  # Higher = more important

    # Link to related incident
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True
    )

    # External link
    action_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    action_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Database indexes
    __table_args__ = (
        Index('idx_banner_active', 'is_active'),
        Index('idx_banner_start_time', 'start_time'),
        Index('idx_banner_end_time', 'end_time'),
        Index('idx_banner_type', 'banner_type'),
        Index('idx_banner_priority', 'priority'),
    )

    def __repr__(self) -> str:
        return f"<Banner(id={self.id}, title='{self.title}', type='{self.banner_type}')>"


class NotificationSubscription(Base, TimestampMixin):
    """Tenant notification subscription model."""

    __tablename__ = "notification_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Tenant identification
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Subscription settings
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Severity filtering
    min_severity: Mapped[IncidentSeverity] = mapped_column(
        SQLEnum(IncidentSeverity),
        nullable=False,
        default=IncidentSeverity.MEDIUM
    )

    # Service filtering
    service_filters: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Notification channels
    channels: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)

    # Timing preferences
    immediate_notification: Mapped[bool] = mapped_column(Boolean, default=True)
    digest_frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)

    # Metadata
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    last_notified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Database indexes
    __table_args__ = (
        Index('idx_subscription_tenant_id', 'tenant_id'),
        Index('idx_subscription_active', 'is_active'),
        Index('idx_subscription_severity', 'min_severity'),
        Index('idx_subscription_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<NotificationSubscription(id={self.id}, tenant_id='{self.tenant_id}')>"


class BannerDismissal(Base, TimestampMixin):
    """Track banner dismissals by users."""

    __tablename__ = "banner_dismissals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    banner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("banners.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Database indexes
    __table_args__ = (
        Index('idx_banner_dismissal_banner_user', 'banner_id', 'user_id', unique=True),
        Index('idx_banner_dismissal_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<BannerDismissal(banner_id={self.banner_id}, user_id='{self.user_id}')>"


class NotificationLog(Base, TimestampMixin):
    """Log of sent notifications for tracking and debugging."""

    __tablename__ = "notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Reference to what triggered the notification
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True
    )

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notification_subscriptions.id", ondelete="CASCADE"),
        nullable=False
    )

    # Notification details
    channel: Mapped[NotificationChannel] = mapped_column(
        SQLEnum(NotificationChannel),
        nullable=False
    )

    recipient: Mapped[str] = mapped_column(String(500), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Delivery status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0)

    # External identifiers
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Database indexes
    __table_args__ = (
        Index('idx_notification_log_incident_id', 'incident_id'),
        Index('idx_notification_log_subscription_id', 'subscription_id'),
        Index('idx_notification_log_status', 'status'),
        Index('idx_notification_log_sent_at', 'sent_at'),
    )

    def __repr__(self) -> str:
        return f"<NotificationLog(id={self.id}, channel='{self.channel}', status='{self.status}')>"
