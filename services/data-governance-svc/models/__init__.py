"""
Database models for Data Governance Service
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4
from sqlalchemy import (
    String, Integer, DateTime, Boolean, Text, JSON, ForeignKey,
    Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base


class EntityType(str, Enum):
    """Types of entities that can have retention policies."""
    USER = "user"
    STUDENT = "student"
    EMPLOYEE = "employee"
    CUSTOMER = "customer"
    TENANT = "tenant"
    SESSION = "session"
    LOG = "log"
    DOCUMENT = "document"
    MESSAGE = "message"
    TRANSACTION = "transaction"


class DSRType(str, Enum):
    """Types of Data Subject Rights requests."""
    EXPORT = "export"
    DELETE = "delete"
    PORTABILITY = "portability"
    RECTIFICATION = "rectification"
    RESTRICTION = "restriction"


class DSRStatus(str, Enum):
    """Status of DSR requests."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"  # Blocked by legal hold


class LegalHoldStatus(str, Enum):
    """Status of legal holds."""
    ACTIVE = "active"
    RELEASED = "released"
    EXPIRED = "expired"


class RetentionPolicy(Base):
    """Retention policy for different entity types."""

    __tablename__ = "retention_policies"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    entity_type: Mapped[EntityType] = mapped_column(String(50), nullable=False)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Retention settings
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    auto_delete_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    grace_period_days: Mapped[int] = mapped_column(Integer, default=30)

    # Compliance settings
    legal_basis: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    compliance_framework: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # FERPA, COPPA, GDPR

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    dsr_requests: Mapped[list["DSRRequest"]] = relationship(
        "DSRRequest", back_populates="retention_policy", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("entity_type", "tenant_id", name="uq_retention_entity_tenant"),
        Index("idx_retention_entity_type", "entity_type"),
        Index("idx_retention_tenant", "tenant_id"),
        CheckConstraint("retention_days > 0", name="ck_retention_positive"),
        CheckConstraint("grace_period_days >= 0", name="ck_grace_period_non_negative"),
    )


class DSRRequest(Base):
    """Data Subject Rights request."""

    __tablename__ = "dsr_requests"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    # Request details
    dsr_type: Mapped[DSRType] = mapped_column(String(20), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_type: Mapped[EntityType] = mapped_column(String(50), nullable=False)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Request metadata
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False)
    requester_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    legal_basis: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Processing status
    status: Mapped[DSRStatus] = mapped_column(String(20), default=DSRStatus.PENDING)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)

    # Results
    export_file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    export_download_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    export_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    deletion_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Compliance tracking
    verification_token: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    identity_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    completion_certificate: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    retention_policy_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("retention_policies.id"), nullable=True
    )
    retention_policy: Mapped[Optional[RetentionPolicy]] = relationship(
        "RetentionPolicy", back_populates="dsr_requests"
    )

    blocked_by_holds: Mapped[list["LegalHold"]] = relationship(
        "LegalHold", secondary="dsr_legal_hold_blocks", back_populates="blocked_requests"
    )

    __table_args__ = (
        Index("idx_dsr_subject", "subject_id", "subject_type"),
        Index("idx_dsr_status", "status"),
        Index("idx_dsr_type", "dsr_type"),
        Index("idx_dsr_tenant", "tenant_id"),
        Index("idx_dsr_requested_at", "requested_at"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", name="ck_progress_range"),
    )


class LegalHold(Base):
    """Legal hold that prevents data deletion."""

    __tablename__ = "legal_holds"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    # Hold details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    case_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Scope
    entity_types: Mapped[list[str]] = mapped_column(JSON, nullable=False)  # List of EntityType values
    subject_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)  # Specific subjects
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Hold status
    status: Mapped[LegalHoldStatus] = mapped_column(String(20), default=LegalHoldStatus.ACTIVE)

    # Dates
    effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Legal details
    legal_authority: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    custodian_name: Mapped[str] = mapped_column(String(200), nullable=False)
    custodian_email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    blocked_requests: Mapped[list[DSRRequest]] = relationship(
        "DSRRequest", secondary="dsr_legal_hold_blocks", back_populates="blocked_by_holds"
    )

    __table_args__ = (
        Index("idx_legal_hold_status", "status"),
        Index("idx_legal_hold_effective", "effective_date"),
        Index("idx_legal_hold_tenant", "tenant_id"),
        Index("idx_legal_hold_case", "case_number"),
    )


class DSRLegalHoldBlock(Base):
    """Many-to-many relationship between DSR requests and legal holds."""

    __tablename__ = "dsr_legal_hold_blocks"

    dsr_request_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("dsr_requests.id"), primary_key=True
    )
    legal_hold_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("legal_holds.id"), primary_key=True
    )
    blocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DataInventoryItem(Base):
    """Tracks data items for governance and DSR processing."""

    __tablename__ = "data_inventory"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    # Item identification
    entity_type: Mapped[EntityType] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Data classification
    data_category: Mapped[str] = mapped_column(String(100), nullable=False)  # PII, Educational, Financial, etc.
    sensitivity_level: Mapped[str] = mapped_column(String(20), nullable=False)  # low, medium, high, critical

    # Storage information
    storage_location: Mapped[str] = mapped_column(String(200), nullable=False)  # database, file_system, s3, etc.
    table_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    column_names: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Retention metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retention_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Flags
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_anonymized: Mapped[bool] = mapped_column(Boolean, default=False)
    has_legal_hold: Mapped[bool] = mapped_column(Boolean, default=False)

    # Audit
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "data_category", "storage_location", name="uq_inventory_item"),
        Index("idx_inventory_entity", "entity_type", "entity_id"),
        Index("idx_inventory_tenant", "tenant_id"),
        Index("idx_inventory_retention", "retention_until"),
        Index("idx_inventory_category", "data_category"),
        Index("idx_inventory_legal_hold", "has_legal_hold"),
    )
