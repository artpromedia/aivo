"""Webhook models for event delivery."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .tenant import Tenant


class WebhookStatus(str, Enum):
    """Webhook status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    FAILED = "failed"


class DeliveryStatus(str, Enum):
    """Webhook delivery status enumeration."""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    EXHAUSTED = "exhausted"


class Webhook(Base, TimestampMixin):
    """Webhook endpoint configuration."""

    __tablename__ = "webhooks"

    # Foreign Keys
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic Information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Events Configuration
    events: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Security
    secret: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status
    status: Mapped[WebhookStatus] = mapped_column(
        default=WebhookStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Delivery Configuration
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    initial_delay_seconds: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_delay_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    backoff_multiplier: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)

    # Statistics
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # HTTP Configuration
    headers: Mapped[dict[str, str] | None] = mapped_column(JSON)
    user_agent: Mapped[str | None] = mapped_column(String(255))

    # Audit Fields
    created_by: Mapped[str | None] = mapped_column(String(255))
    updated_by: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="webhooks")
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        back_populates="webhook",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Webhook(id={self.id}, name='{self.name}', url='{self.url}')>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_deliveries == 0:
            return 0.0
        return (self.successful_deliveries / self.total_deliveries) * 100


class WebhookDelivery(Base, TimestampMixin):
    """Webhook delivery attempt record."""

    __tablename__ = "webhook_deliveries"

    # Foreign Keys
    webhook_id: Mapped[UUID] = mapped_column(
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("webhook_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Delivery Information
    status: Mapped[DeliveryStatus] = mapped_column(
        default=DeliveryStatus.PENDING,
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Request Details
    request_headers: Mapped[dict[str, str] | None] = mapped_column(JSON)
    request_body: Mapped[str | None] = mapped_column(Text)

    # Response Details
    response_status_code: Mapped[int | None] = mapped_column(Integer)
    response_headers: Mapped[dict[str, str] | None] = mapped_column(JSON)
    response_body: Mapped[str | None] = mapped_column(Text)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)

    # Error Information
    error_message: Mapped[str | None] = mapped_column(Text)
    error_type: Mapped[str | None] = mapped_column(String(100))

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    webhook: Mapped["Webhook"] = relationship(back_populates="deliveries")
    event: Mapped["WebhookEvent"] = relationship(back_populates="deliveries")

    def __repr__(self) -> str:
        """String representation."""
        return f"<WebhookDelivery(id={self.id}, webhook_id={self.webhook_id}, status={self.status})>"


class WebhookEvent(Base, TimestampMixin):
    """Webhook event payload."""

    __tablename__ = "webhook_events"

    # Event Information
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)

    # Payload
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Metadata
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Idempotency
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)

    # Status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<WebhookEvent(id={self.id}, event_type='{self.event_type}', tenant_id={self.tenant_id})>"
