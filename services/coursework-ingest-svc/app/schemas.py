"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import ContentType, ProcessingStatus


class CourseworkItemBase(BaseModel):
    """Base schema for coursework items."""

    filename: str
    content_type: ContentType
    uploaded_by: str | None = None


class CourseworkItemCreate(CourseworkItemBase):
    """Schema for creating a coursework item."""

    file_size: int
    original_filename: str
    s3_key: str


class CourseworkItemUpdate(BaseModel):
    """Schema for updating a coursework item."""

    status: ProcessingStatus | None = None
    ocr_text: str | None = None
    ocr_confidence: float | None = None
    moderation_score: float | None = None
    moderation_approved: bool | None = None
    moderation_flags: dict[str, Any] | None = None
    pii_detected: bool | None = None
    pii_entities: dict[str, Any] | None = None
    masked_text: str | None = None
    topics: dict[str, Any] | None = None
    topic_confidence: float | None = None
    consent_given: bool | None = None
    media_approved: bool | None = None
    error_message: str | None = None


class CourseworkItemResponse(CourseworkItemBase):
    """Schema for coursework item responses."""

    id: int
    file_size: int
    original_filename: str
    s3_key: str
    status: ProcessingStatus
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None
    error_message: str | None = None

    # OCR results
    ocr_text: str | None = None
    ocr_confidence: float | None = None

    # Content moderation
    moderation_score: float | None = None
    moderation_approved: bool | None = None
    moderation_flags: dict[str, Any] | None = None

    # PII detection and masking
    pii_detected: bool | None = None
    pii_entities: dict[str, Any] | None = None
    masked_text: str | None = None

    # Topic extraction
    topics: dict[str, Any] | None = None
    topic_confidence: float | None = None

    # Consent and media gates
    consent_required: bool
    consent_given: bool | None = None
    consent_given_at: datetime | None = None
    media_approval_required: bool
    media_approved: bool | None = None
    media_approved_at: datetime | None = None
    media_approved_by: str | None = None

    # Metadata
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class CourseworkItemSummary(BaseModel):
    """Summary schema for coursework items."""

    id: int
    filename: str
    content_type: ContentType
    status: ProcessingStatus
    created_at: datetime
    topics: dict[str, Any] | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class UploadResponse(BaseModel):
    """Response schema for file uploads."""

    id: int
    filename: str
    status: ProcessingStatus
    message: str = "File uploaded successfully"


class ProcessingLogResponse(BaseModel):
    """Schema for processing log responses."""

    id: int
    coursework_item_id: int
    step: str
    status: str
    message: str | None = None
    details: dict[str, Any] | None = None
    duration_ms: int | None = None
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ReanalyzeRequest(BaseModel):
    """Schema for reanalyze requests."""

    force: bool = Field(
        default=False, description="Force reanalysis even if completed"
    )
    steps: list[str] | None = Field(
        default=None,
        description="Specific steps to rerun (ocr, moderation, pii, topics)",
    )


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    service: str
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    detail: str | None = None
    timestamp: datetime
