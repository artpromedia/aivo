"""
Database models for consent and preferences ledger.

Comprehensive models for GDPR/COPPA compliance with audit trails.
"""
import enum
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class ConsentType(enum.Enum):
    """Types of consent that can be granted or revoked."""
    DATA_COLLECTION = "data_collection"
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    CHAT_MONITORING = "chat_monitoring"
    MEDIA_CAPTURE = "media_capture"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    THIRD_PARTY_SERVICES = "third_party_services"


class ConsentStatus(enum.Enum):
    """Current status of consent."""
    GRANTED = "granted"
    REVOKED = "revoked"
    PENDING = "pending"
    EXPIRED = "expired"


class ParentalRightType(enum.Enum):
    """Types of parental rights under COPPA."""
    VIEW_CHILD_DATA = "view_child_data"
    MODIFY_CONSENT = "modify_consent"
    DELETE_CHILD_DATA = "delete_child_data"
    EXPORT_CHILD_DATA = "export_child_data"
    RESTRICT_DATA_USE = "restrict_data_use"


class RequestStatus(enum.Enum):
    """Status of data export/deletion requests."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AuditAction(enum.Enum):
    """Types of audit actions."""
    CONSENT_GRANTED = "consent_granted"
    CONSENT_REVOKED = "consent_revoked"
    CONSENT_UPDATED = "consent_updated"
    PARENTAL_RIGHT_EXERCISED = "parental_right_exercised"
    DATA_EXPORT_REQUESTED = "data_export_requested"
    DATA_EXPORT_COMPLETED = "data_export_completed"
    DELETION_REQUESTED = "deletion_requested"
    DELETION_COMPLETED = "deletion_completed"
    CASCADE_DELETE_TRIGGERED = "cascade_delete_triggered"


def is_valid_email(email: str) -> bool:
    """Helper function to validate email format."""
    return "@" in email and "." in email.split("@")[1]


def is_minor_age(age: int) -> bool:
    """Helper function to check if age indicates minor status."""
    return age < 18


def requires_parental_consent(user_age: Optional[int]) -> bool:
    """Helper function to determine if parental consent is required."""
    return user_age is not None and is_minor_age(user_age)


class ConsentRecord(Base):
    """
    Primary consent record for users.
    
    Tracks all consent decisions with full audit trail.
    """
    __tablename__ = "consent_records"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    consent_type = Column(Enum(ConsentType), nullable=False)
    status = Column(Enum(ConsentStatus), nullable=False, default=ConsentStatus.PENDING)
    
    # Consent details
    granted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Legal basis and context
    legal_basis = Column(String(100), nullable=False)  # GDPR Article 6 basis
    purpose = Column(Text, nullable=False)
    data_categories = Column(JSON, nullable=False)  # List of data types
    
    # User context
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    location = Column(String(100))
    
    # Parental consent (COPPA compliance)
    requires_parental_consent = Column(Boolean, default=False)
    parental_consent_given = Column(Boolean, default=False)
    parent_email = Column(String(255))
    parent_verification_token = Column(String(255))
    parent_verified_at = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255))
    
    # Relationships
    audit_logs = relationship("AuditLog", back_populates="consent_record")
    preferences = relationship("PreferenceSettings", back_populates="consent_record")
    
    def __repr__(self) -> str:
        return f"<ConsentRecord(user_id={self.user_id}, type={self.consent_type.value}, status={self.status.value})>"


class ParentalRight(Base):
    """
    Parental rights and controls under COPPA.
    
    Manages parent-child relationships and rights.
    """
    __tablename__ = "parental_rights"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_email = Column(String(255), nullable=False, index=True)
    child_user_id = Column(String(255), nullable=False, index=True)
    
    # Rights and permissions
    right_type = Column(Enum(ParentalRightType), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Verification
    verification_token = Column(String(255))
    verified_at = Column(DateTime(timezone=True))
    verification_method = Column(String(100))  # email, phone, identity_check
    
    # Expiration
    expires_at = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<ParentalRight(parent={self.parent_email}, child={self.child_user_id}, type={self.right_type.value})>"


class PreferenceSettings(Base):
    """
    User preference settings for data handling.
    
    Granular controls for different data uses.
    """
    __tablename__ = "preference_settings"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    consent_record_id = Column(PG_UUID(as_uuid=True), ForeignKey("consent_records.id"), nullable=False)
    
    # Communication preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    push_notifications = Column(Boolean, default=True)
    
    # Data processing preferences
    analytics_tracking = Column(Boolean, default=False)
    personalization = Column(Boolean, default=True)
    marketing_use = Column(Boolean, default=False)
    
    # Third-party sharing
    share_with_partners = Column(Boolean, default=False)
    share_for_research = Column(Boolean, default=False)
    
    # Chat and media preferences
    chat_monitoring_consent = Column(Boolean, default=False)
    media_capture_consent = Column(Boolean, default=False)
    behavioral_analysis_consent = Column(Boolean, default=False)
    
    # Data retention preferences
    data_retention_period_days = Column(Integer, default=365)
    auto_delete_enabled = Column(Boolean, default=False)
    
    # Custom preferences (JSON for flexibility)
    custom_preferences = Column(JSON, default=dict)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    consent_record = relationship("ConsentRecord", back_populates="preferences")
    
    def __repr__(self) -> str:
        return f"<PreferenceSettings(consent_id={self.consent_record_id})>"


class DataExportRequest(Base):
    """
    Data export requests for GDPR Article 20 compliance.
    
    Tracks export requests with 10 day completion requirement.
    """
    __tablename__ = "data_export_requests"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    requestor_email = Column(String(255), nullable=False)
    
    # Request details
    request_type = Column(String(50), default="full_export")  # full_export, specific_data
    data_categories = Column(JSON)  # Specific data types requested
    format_preference = Column(String(20), default="json")  # json, csv, xml
    
    # Status tracking
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Export details
    export_file_path = Column(String(500))
    export_file_size_bytes = Column(Integer)
    download_url = Column(String(500))
    download_expires_at = Column(DateTime(timezone=True))
    download_count = Column(Integer, default=0)
    
    # Data sources included
    postgres_exported = Column(Boolean, default=False)
    mongodb_exported = Column(Boolean, default=False)
    s3_exported = Column(Boolean, default=False)
    snowflake_exported = Column(Boolean, default=False)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Parental request handling
    is_parental_request = Column(Boolean, default=False)
    parent_email = Column(String(255))
    parent_verified = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<DataExportRequest(user_id={self.user_id}, status={self.status.value})>"


class DeletionRequest(Base):
    """
    Data deletion requests for GDPR Article 17 compliance.
    
    Tracks deletion requests with cascaded deletes across all systems.
    """
    __tablename__ = "deletion_requests"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    requestor_email = Column(String(255), nullable=False)
    
    # Request details
    deletion_reason = Column(String(100))  # consent_withdrawn, no_longer_needed, etc.
    scope = Column(String(50), default="all_data")  # all_data, specific_categories
    data_categories = Column(JSON)  # Specific data to delete if scope is specific
    
    # Status tracking
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Deletion progress across systems
    postgres_deleted = Column(Boolean, default=False)
    mongodb_deleted = Column(Boolean, default=False)
    s3_deleted = Column(Boolean, default=False)
    snowflake_deleted = Column(Boolean, default=False)
    
    # Deletion details
    records_deleted_count = Column(Integer, default=0)
    files_deleted_count = Column(Integer, default=0)
    storage_freed_bytes = Column(Integer, default=0)
    
    # Retention exceptions
    legal_hold = Column(Boolean, default=False)
    legal_hold_reason = Column(Text)
    retention_required_until = Column(DateTime(timezone=True))
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Parental request handling
    is_parental_request = Column(Boolean, default=False)
    parent_email = Column(String(255))
    parent_verified = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<DeletionRequest(user_id={self.user_id}, status={self.status.value})>"


class AuditLog(Base):
    """
    Comprehensive audit log for all consent operations.
    
    Immutable audit trail for compliance and forensics.
    """
    __tablename__ = "audit_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Core audit info
    action = Column(Enum(AuditAction), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Subject and actor
    user_id = Column(String(255), nullable=False, index=True)
    actor_id = Column(String(255))  # Who performed the action (parent, admin, system)
    actor_type = Column(String(50))  # user, parent, admin, system
    
    # Related records
    consent_record_id = Column(PG_UUID(as_uuid=True), ForeignKey("consent_records.id"))
    export_request_id = Column(PG_UUID(as_uuid=True), ForeignKey("data_export_requests.id"))
    deletion_request_id = Column(PG_UUID(as_uuid=True), ForeignKey("deletion_requests.id"))
    
    # Action details
    details = Column(JSON)  # Structured details about the action
    old_values = Column(JSON)  # Previous state for updates
    new_values = Column(JSON)  # New state for updates
    
    # Context
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    session_id = Column(String(255))
    
    # Legal compliance
    legal_basis = Column(String(100))
    compliance_notes = Column(Text)
    
    # Integrity protection
    checksum = Column(String(64))  # SHA-256 checksum for tamper detection
    
    # Relationships
    consent_record = relationship("ConsentRecord", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action.value}, user_id={self.user_id}, timestamp={self.timestamp})>"
