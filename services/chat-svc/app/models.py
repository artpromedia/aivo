"""
Database models for chat service.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class UserRole(str, Enum):
    """User roles in the system."""

    LEARNER = "learner"
    TEACHER = "teacher"
    PARENT = "parent"
    AI_COACH = "ai_coach"
    AI_TUTOR = "ai_tutor"


class ChatType(str, Enum):
    """Types of chat conversations."""

    PARENT_TEACHER = "parent_teacher"
    PARENT_AI_COACH = "parent_ai_coach"
    LEARNER_AI_TUTOR = "learner_ai_tutor"
    TEACHER_AI_COACH = "teacher_ai_coach"


class MessageStatus(str, Enum):
    """Message processing status."""

    PENDING = "pending"
    APPROVED = "approved"
    BLOCKED = "blocked"
    FLAGGED = "flagged"
    ARCHIVED = "archived"


class ModerationAction(str, Enum):
    """Moderation actions."""

    APPROVED = "approved"
    SOFT_BLOCK = "soft_block"
    HARD_BLOCK = "hard_block"
    HUMAN_REVIEW = "human_review"
    PII_SCRUBBED = "pii_scrubbed"


class ChatSession(Base):
    """Chat session model."""

    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    chat_type: Mapped[ChatType] = mapped_column(SQLEnum(ChatType), nullable=False)
    participants: Mapped[List[UUID]] = mapped_column(JSON, nullable=False)
    learner_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    parent_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    teacher_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # Parental controls
    parental_controls_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_tutor_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    moderation_level: Mapped[str] = mapped_column(String(20), default="strict")

    # Session metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Archive settings
    auto_archive_days: Mapped[int] = mapped_column(Integer, default=30)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_chat_sessions_learner_id", "learner_id"),
        Index("ix_chat_sessions_parent_id", "parent_id"),
        Index("ix_chat_sessions_teacher_id", "teacher_id"),
        Index("ix_chat_sessions_created_at", "created_at"),
        Index("ix_chat_sessions_active", "is_active"),
    )


class ChatMessage(Base):
    """Chat message model."""

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False
    )
    sender_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    sender_role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)

    # Message content
    original_content: Mapped[str] = mapped_column(Text, nullable=False)
    processed_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256

    # Message metadata
    message_type: Mapped[str] = mapped_column(String(20), default="text")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Moderation
    status: Mapped[MessageStatus] = mapped_column(
        SQLEnum(MessageStatus), default=MessageStatus.PENDING
    )
    moderation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    moderation_action: Mapped[Optional[ModerationAction]] = mapped_column(
        SQLEnum(ModerationAction), nullable=True
    )

    # PII detection
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    pii_types: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    moderation_logs = relationship(
        "ModerationLog", back_populates="message", cascade="all, delete-orphan"
    )
    audit_entries = relationship(
        "AuditEntry", back_populates="message", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id"),
        Index("ix_chat_messages_sender_id", "sender_id"),
        Index("ix_chat_messages_created_at", "created_at"),
        Index("ix_chat_messages_status", "status"),
        Index("ix_chat_messages_content_hash", "content_hash"),
    )


class ModerationLog(Base):
    """Moderation log for audit trail."""

    __tablename__ = "moderation_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False
    )

    # Moderation details
    moderation_service: Mapped[str] = mapped_column(String(50), nullable=False)
    moderation_version: Mapped[str] = mapped_column(String(20), nullable=False)
    toxicity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threat_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profanity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    identity_attack_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Action taken
    action_taken: Mapped[ModerationAction] = mapped_column(
        SQLEnum(ModerationAction), nullable=False
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Timing
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processing_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    message = relationship("ChatMessage", back_populates="moderation_logs")

    __table_args__ = (
        Index("ix_moderation_logs_message_id", "message_id"),
        Index("ix_moderation_logs_processed_at", "processed_at"),
        Index("ix_moderation_logs_action", "action_taken"),
    )


class AuditEntry(Base):
    """Audit entry for Merkle chain."""

    __tablename__ = "audit_entries"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False
    )

    # Merkle chain data
    block_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    previous_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    merkle_root: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Data integrity
    data_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Export tracking
    exported_to_s3: Mapped[bool] = mapped_column(Boolean, default=False)
    s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    parquet_exported: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    message = relationship("ChatMessage", back_populates="audit_entries")

    __table_args__ = (
        Index("ix_audit_entries_message_id", "message_id"),
        Index("ix_audit_entries_timestamp", "timestamp"),
        Index("ix_audit_entries_block_hash", "block_hash"),
        Index("ix_audit_entries_exported", "exported_to_s3"),
    )


class ParentalControl(Base):
    """Parental control settings."""

    __tablename__ = "parental_controls"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    learner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # AI Tutor controls
    ai_tutor_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_tutor_time_limits: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Content controls
    content_filter_level: Mapped[str] = mapped_column(String(20), default="strict")
    allowed_topics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    blocked_topics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Monitoring settings
    monitor_all_chats: Mapped[bool] = mapped_column(Boolean, default=True)
    real_time_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_summaries: Mapped[bool] = mapped_column(Boolean, default=True)

    # Data retention
    chat_retention_days: Mapped[int] = mapped_column(Integer, default=365)
    auto_delete_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_parental_controls_parent_id", "parent_id"),
        Index("ix_parental_controls_learner_id", "learner_id"),
        Index("ix_parental_controls_unique", "parent_id", "learner_id", unique=True),
    )
