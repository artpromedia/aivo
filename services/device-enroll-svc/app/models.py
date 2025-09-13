"""Database models for Device Enrollment Service."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""


class DeviceStatus(str, Enum):
    """Device enrollment status."""

    PENDING = "pending"
    ENROLLED = "enrolled"
    ATTESTED = "attested"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AttestationStatus(str, Enum):
    """Attestation verification status."""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


class Device(Base):
    """Device enrollment record."""

    __tablename__ = "devices"

    device_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    serial_number: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hardware_fingerprint: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    device_model: Mapped[str] = mapped_column(String(100), nullable=False, default="aivo-pad")
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[DeviceStatus] = mapped_column(
        String(20), nullable=False, default=DeviceStatus.PENDING
    )

    # Enrollment data
    enrollment_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    bootstrap_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bootstrap_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Certificate data
    public_key_pem: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_certificate_pem: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_serial: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    certificate_issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    certificate_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    enrollment_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )


class AttestationChallenge(Base):
    """Attestation challenge records."""

    __tablename__ = "attestation_challenges"

    challenge_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    device_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    nonce: Mapped[str] = mapped_column(String(512), nullable=False)
    challenge_data: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AttestationStatus] = mapped_column(
        String(20), nullable=False, default=AttestationStatus.PENDING
    )

    # Response data
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attestation_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    verification_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timing
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )


class DeviceAuditLog(Base):
    """Audit log for device operations."""

    __tablename__ = "device_audit_logs"

    log_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    device_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    operation: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class AlertRuleCondition(str, Enum):
    """Alert rule condition types."""

    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"


class AlertRuleAction(str, Enum):
    """Alert rule action types."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    DEVICE_LOCK = "device_lock"
    DEVICE_WIPE = "device_wipe"


class AlertRule(Base):
    """Alert rules for fleet health monitoring."""

    __tablename__ = "alert_rules"

    rule_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Rule configuration
    metric: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    condition: Mapped[AlertRuleCondition] = mapped_column(String(20), nullable=False)
    threshold: Mapped[str] = mapped_column(String(100), nullable=False)  # Can be numeric or string
    window_minutes: Mapped[int] = mapped_column(Integer, default=15)

    # Targeting
    tenant_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    device_filter: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Device selection criteria

    # Actions
    actions: Mapped[list[AlertRuleAction]] = mapped_column(JSON, nullable=False)
    action_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Action-specific config

    # State
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )


class AlertTrigger(Base):
    """Alert trigger history."""

    __tablename__ = "alert_triggers"

    trigger_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    rule_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Trigger context
    metric_value: Mapped[str] = mapped_column(String(100), nullable=False)
    affected_devices: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    trigger_reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Actions taken
    actions_executed: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    action_results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True
    )


class DeviceAction(Base):
    """Remote device actions (wipe, reboot, lock)."""

    __tablename__ = "device_actions"

    action_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    device_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # wipe, reboot, lock

    # Action details
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Execution
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, sent, completed, failed
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    initiated_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
