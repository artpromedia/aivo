"""Database models for coursework ingest service."""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""


class ProcessingStatus(str, Enum):
    """Status of coursework processing."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"


class ContentType(str, Enum):
    """Type of uploaded content."""

    PDF = "pdf"
    IMAGE = "image"


class CourseworkItem(Base):
    """Model for uploaded coursework items."""

    __tablename__ = "coursework_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(
        String(50), nullable=False
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    s3_key: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True
    )

    # Processing status
    status: Mapped[ProcessingStatus] = mapped_column(
        String(50),
        nullable=False,
        default=ProcessingStatus.UPLOADED,
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    # OCR results
    ocr_text: Mapped[str | None] = mapped_column(Text)
    ocr_confidence: Mapped[float | None] = mapped_column(Float)

    # Content moderation
    moderation_score: Mapped[float | None] = mapped_column(Float)
    moderation_approved: Mapped[bool | None] = mapped_column()
    moderation_flags: Mapped[dict | None] = mapped_column(JSON)

    # PII detection and masking
    pii_detected: Mapped[bool | None] = mapped_column()
    pii_entities: Mapped[dict | None] = mapped_column(JSON)
    masked_text: Mapped[str | None] = mapped_column(Text)

    # Topic extraction
    topics: Mapped[dict | None] = mapped_column(JSON)
    topic_confidence: Mapped[float | None] = mapped_column(Float)

    # Consent and media gates
    consent_required: Mapped[bool] = mapped_column(default=False)
    consent_given: Mapped[bool | None] = mapped_column()
    consent_given_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    media_approval_required: Mapped[bool] = mapped_column(default=False)
    media_approved: Mapped[bool | None] = mapped_column()
    media_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    media_approved_by: Mapped[str | None] = mapped_column(String(255))

    # Metadata
    uploaded_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<CourseworkItem(id={self.id}, "
            f"filename='{self.filename}', status='{self.status}')>"
        )


class ProcessingLog(Base):
    """Model for processing logs and audit trail."""

    __tablename__ = "processing_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coursework_item_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    step: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict | None] = mapped_column(JSON)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ProcessingLog(id={self.id}, "
            f"item_id={self.coursework_item_id}, step='{self.step}')>"
        )
