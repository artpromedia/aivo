"""Database models for Device Enrollment Service."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
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
