"""Database models for content moderation system."""

import enum
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Enum,
    Integer,
    Boolean,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class ContentType(enum.Enum):
    """Types of content that can be moderated."""
    OCR_UPLOAD = "ocr_upload"
    CHAT_MESSAGE = "chat_message"
    INK_IMAGE = "ink_image"
    AUDIO_RECORDING = "audio_recording"
    VIDEO_SUBMISSION = "video_submission"
    TEXT_SUBMISSION = "text_submission"

class ModerationStatus(enum.Enum):
    """Status of moderation queue items."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SOFT_BLOCKED = "soft_blocked"
    HARD_BLOCKED = "hard_blocked"
    APPEALED = "appealed"
    EXPIRED = "expired"

class DecisionType(enum.Enum):
    """Types of moderation decisions."""
    APPROVE = "approve"
    SOFT_BLOCK = "soft_block"
    HARD_BLOCK = "hard_block"
    ESCALATE = "escalate"
    APPEAL_APPROVED = "appeal_approved"
    APPEAL_DENIED = "appeal_denied"

class SeverityLevel(enum.Enum):
    """Severity levels for content flags."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FlagReason(enum.Enum):
    """Reasons for content being flagged."""
    INAPPROPRIATE_LANGUAGE = "inappropriate_language"
    VIOLENCE = "violence"
    HATE_SPEECH = "hate_speech"
    HARASSMENT = "harassment"
    SPAM = "spam"
    COPYRIGHT_VIOLATION = "copyright_violation"
    PERSONAL_INFO = "personal_info"
    ACADEMIC_DISHONESTY = "academic_dishonesty"
    SAFETY_CONCERN = "safety_concern"
    OTHER = "other"

class ModerationQueueItem(Base):
    """Represents an item in the moderation queue."""

    __tablename__ = "moderation_queue_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id = Column(String(255), nullable=False, index=True)
    content_type = Column(Enum(ContentType), nullable=False, index=True)
    content_url = Column(Text, nullable=True)
    content_preview = Column(Text, nullable=True)
    content_metadata = Column(JSON, nullable=True)

    # User and context information
    user_id = Column(String(255), nullable=False, index=True)
    tenant_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True)

    # Flagging information
    flag_reason = Column(Enum(FlagReason), nullable=False)
    flag_details = Column(Text, nullable=True)
    severity_level = Column(Enum(SeverityLevel), nullable=False, index=True)
    confidence_score = Column(Integer, nullable=True)  # 0-100

    # Status and timestamps
    status = Column(Enum(ModerationStatus), nullable=False, default=ModerationStatus.PENDING, index=True)
    flagged_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Flagging source
    flagged_by_system = Column(Boolean, nullable=False, default=True)
    flagged_by_user_id = Column(String(255), nullable=True)

    # Relationships
    decisions = relationship("ModerationDecision", back_populates="queue_item", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="queue_item", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_queue_status_flagged', 'status', 'flagged_at'),
        Index('idx_queue_severity_type', 'severity_level', 'content_type'),
        Index('idx_queue_user_tenant', 'user_id', 'tenant_id'),
    )

class ModerationDecision(Base):
    """Represents a moderation decision made on a queue item."""

    __tablename__ = "moderation_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    queue_item_id = Column(UUID(as_uuid=True), ForeignKey("moderation_queue_items.id"), nullable=False)

    # Decision details
    decision_type = Column(Enum(DecisionType), nullable=False)
    reason = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)

    # Moderator information
    moderator_id = Column(String(255), nullable=False)
    moderator_name = Column(String(255), nullable=True)

    # Timing and expiration
    decided_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Decision metadata
    confidence_level = Column(Integer, nullable=True)  # 0-100
    escalation_required = Column(Boolean, nullable=False, default=False)
    appeal_deadline = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    queue_item = relationship("ModerationQueueItem", back_populates="decisions")
    audit_logs = relationship("AuditLog", back_populates="decision", cascade="all, delete-orphan")

class AuditLog(Base):
    """Audit trail for all moderation actions."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Entity references
    queue_item_id = Column(UUID(as_uuid=True), ForeignKey("moderation_queue_items.id"), nullable=True)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("moderation_decisions.id"), nullable=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Actor information
    actor_id = Column(String(255), nullable=False)
    actor_type = Column(String(50), nullable=False)  # 'user', 'system', 'moderator'
    actor_name = Column(String(255), nullable=True)

    # Context and metadata
    context = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Relationships
    queue_item = relationship("ModerationQueueItem", back_populates="audit_logs")
    decision = relationship("ModerationDecision", back_populates="audit_logs")

    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_actor', 'actor_id', 'actor_type'),
        Index('idx_audit_action', 'action'),
    )

class ModerationAppeal(Base):
    """Represents an appeal for a moderation decision."""

    __tablename__ = "moderation_appeals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("moderation_decisions.id"), nullable=False)

    # Appeal details
    reason = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    evidence_urls = Column(JSON, nullable=True)

    # Appellant information
    appellant_id = Column(String(255), nullable=False)
    appellant_name = Column(String(255), nullable=True)
    appellant_email = Column(String(255), nullable=True)

    # Status and timing
    status = Column(String(50), nullable=False, default="pending")
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Resolution
    resolution = Column(Text, nullable=True)
    resolver_id = Column(String(255), nullable=True)
    resolver_name = Column(String(255), nullable=True)

    # Relationships
    decision = relationship("ModerationDecision")

class ModerationRule(Base):
    """Configurable moderation rules and policies."""

    __tablename__ = "moderation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Rule identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(100), nullable=False)  # 'keyword', 'ml_model', 'pattern', etc.

    # Rule configuration
    config = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Targeting
    content_types = Column(JSON, nullable=True)  # Array of content types this applies to
    severity_level = Column(Enum(SeverityLevel), nullable=False)
    auto_action = Column(Enum(DecisionType), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_by = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_by = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False, default=1)
