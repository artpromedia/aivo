"""Database models for Device Policy Service."""
# flake8: noqa: E501

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""


class PolicyType(str, Enum):
    """Policy type enumeration."""

    KIOSK = "kiosk"
    NETWORK = "network"
    DNS = "dns"
    STUDY_WINDOW = "study_window"
    ALLOWLIST = "allowlist"


class PolicyStatus(str, Enum):
    """Policy deployment status."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class SyncStatus(str, Enum):
    """Device policy sync status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SYNCED = "synced"
    FAILED = "failed"
    OUTDATED = "outdated"


class Policy(Base):
    """Policy configuration records."""

    __tablename__ = "policies"

    policy_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_type: Mapped[PolicyType] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[PolicyStatus] = mapped_column(
        String(20), nullable=False, default=PolicyStatus.DRAFT
    )

    # Policy configuration
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    # Target criteria
    target_criteria: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Priority (higher number = higher priority)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Scheduling
    effective_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Metadata
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

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

    # Relationships
    device_policies: Mapped[list["DevicePolicy"]] = relationship(
        "DevicePolicy", back_populates="policy", cascade="all, delete-orphan"
    )


class DevicePolicy(Base):
    """Device-specific policy assignments."""

    __tablename__ = "device_policies"

    assignment_id: Mapped[UUID] = mapped_column(
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
    policy_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("policies.policy_id"),
        nullable=False,
        index=True,
    )

    # Sync status
    sync_status: Mapped[SyncStatus] = mapped_column(
        String(20), nullable=False, default=SyncStatus.PENDING
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sync_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Versioning
    applied_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    applied_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Metadata
    assigned_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    policy: Mapped["Policy"] = relationship("Policy", back_populates="device_policies")


class PolicySyncLog(Base):
    """Policy synchronization audit log."""

    __tablename__ = "policy_sync_logs"

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
    policy_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Sync details
    sync_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # 'full', 'diff', 'patch'
    sync_status: Mapped[SyncStatus] = mapped_column(String(20), nullable=False)
    sync_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Version tracking
    from_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    to_version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Error details
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class AllowlistEntry(Base):
    """Network allowlist entries."""

    __tablename__ = "allowlist_entries"

    entry_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    # Entry details
    entry_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # 'domain', 'url', 'ip', 'subnet'
    value: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Categorization
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Configuration
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Metadata
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

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
