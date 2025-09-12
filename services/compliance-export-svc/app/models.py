"""
SQLAlchemy models for compliance export service.
Includes export jobs, audit logs, and encrypted file storage.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""

    pass


class ExportStatus(str, Enum):
    """Export job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(str, Enum):
    """Export format enumeration."""

    EDFACTS = "edfacts"
    CALPADS = "calpads"
    CUSTOM = "custom"


class AuditAction(str, Enum):
    """Audit log action enumeration."""

    EXPORT_CREATED = "export_created"
    EXPORT_STARTED = "export_started"
    EXPORT_COMPLETED = "export_completed"
    EXPORT_FAILED = "export_failed"
    EXPORT_DOWNLOADED = "export_downloaded"
    EXPORT_DELETED = "export_deleted"
    FILE_ENCRYPTED = "file_encrypted"
    FILE_DECRYPTED = "file_decrypted"


class ExportJob(Base):
    """Export job model for tracking compliance exports."""

    __tablename__ = "export_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    format: Mapped[ExportFormat] = mapped_column(String(50), nullable=False)
    status: Mapped[ExportStatus] = mapped_column(
        String(20), default=ExportStatus.PENDING, nullable=False
    )

    # Job metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)

    # Timing and user info
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

    # File and encryption info
    file_path: Mapped[str | None] = mapped_column(String(500))
    encrypted_file_path: Mapped[str | None] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(Integer)
    encryption_key_id: Mapped[str | None] = mapped_column(String(255))

    # Progress and results
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    total_records: Mapped[int | None] = mapped_column(Integer)
    processed_records: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Compliance metadata
    school_year: Mapped[str] = mapped_column(String(10), nullable=False)
    district_id: Mapped[str | None] = mapped_column(String(50))
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)

    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="export_job", cascade="all, delete-orphan"
    )


class AuditLog(Base):
    """Immutable audit log for tracking all export operations."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        UniqueConstraint("id"),  # Ensure immutability
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    export_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("export_jobs.id"), nullable=False
    )

    # Audit details
    action: Mapped[AuditAction] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))

    # Action details
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    previous_values: Mapped[dict | None] = mapped_column(JSON)
    new_values: Mapped[dict | None] = mapped_column(JSON)

    # Compliance tracking
    compliance_officer: Mapped[str | None] = mapped_column(String(255))
    regulatory_requirement: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    export_job: Mapped["ExportJob"] = relationship("ExportJob", back_populates="audit_logs")


class EncryptionKey(Base):
    """Encryption key storage for AES encryption at rest."""

    __tablename__ = "encryption_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Encrypted key storage (key is encrypted with master key)
    encrypted_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    salt: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    # Key metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Key rotation
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime)
    predecessor_key_id: Mapped[str | None] = mapped_column(String(255))


class ComplianceTemplate(Base):
    """Template definitions for different compliance export formats."""

    __tablename__ = "compliance_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    format: Mapped[ExportFormat] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)

    # Template metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)

    # Template configuration
    field_definitions: Mapped[dict] = mapped_column(JSON, nullable=False)
    validation_rules: Mapped[dict] = mapped_column(JSON, default=dict)
    transformation_rules: Mapped[dict] = mapped_column(JSON, default=dict)

    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ExportSchedule(Base):
    """Scheduled export jobs for automated compliance reporting."""

    __tablename__ = "export_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[ExportFormat] = mapped_column(String(50), nullable=False)

    # Schedule configuration
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)

    # Schedule metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Last execution
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
