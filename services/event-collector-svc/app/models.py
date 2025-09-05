"""Pydantic models for event validation and API schemas."""
# pylint: disable=no-self-argument

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator


class LearnerEvent(BaseModel):
    """Individual learner event model."""

    learner_id: str = Field(..., description="Unique learner identifier")
    event_type: str = Field(..., description="Type of event")
    event_id: str = Field(..., description="Unique event identifier")
    session_id: str | None = Field(None, description="Session identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: dict[str, Any] = Field(
        default_factory=dict, description="Event data payload"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Event metadata"
    )
    version: str = Field(default="1.0", description="Event schema version")

    @validator("event_type")
    def validate_event_type(cls, v: str) -> str:
        """Validate event type."""
        allowed_types = {
            "page_view",
            "interaction",
            "assessment_start",
            "assessment_complete",
            "lesson_start",
            "lesson_complete",
            "resource_access",
            "error",
            "custom",
        }
        if v not in allowed_types:
            raise ValueError(f"Invalid event type: {v}")
        return v

    @validator("learner_id")
    def validate_learner_id(cls, v: str) -> str:
        """Validate learner ID format."""
        if not v or len(v) > 255:
            raise ValueError("learner_id must be non-empty and ≤ 255 chars")
        return v

    @validator("event_id")
    def validate_event_id(cls, v: str) -> str:
        """Validate event ID format."""
        if not v or len(v) > 255:
            raise ValueError("event_id must be non-empty and ≤ 255 chars")
        return v


class EventBatch(BaseModel):
    """Batch of learner events."""

    events: list[LearnerEvent] = Field(
        ..., description="List of events in the batch"
    )
    batch_id: str | None = Field(None, description="Batch identifier")
    source: str | None = Field(None, description="Source of the batch")
    received_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the batch was received",
    )

    @validator("events")
    def validate_events_not_empty(
        cls, v: list[LearnerEvent]
    ) -> list[LearnerEvent]:
        """Validate that events list is not empty."""
        if not v:
            raise ValueError("Events list cannot be empty")
        return v


class CollectResponse(BaseModel):
    """Response model for event collection endpoints."""

    accepted: int = Field(..., description="Number of events accepted")
    rejected: int = Field(default=0, description="Number of events rejected")
    batch_id: str | None = Field(None, description="Assigned batch ID")
    message: str = Field(
        default="Events received", description="Response message"
    )
    errors: list[str] = Field(
        default_factory=list, description="List of validation errors"
    )


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Check timestamp")
    checks: dict[str, Any] = Field(
        default_factory=dict, description="Individual health checks"
    )


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    ready: bool = Field(..., description="Service readiness status")
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(..., description="Check timestamp")
    dependencies: dict[str, bool] = Field(
        default_factory=dict, description="Dependency readiness status"
    )


class MetricsInfo(BaseModel):
    """Metrics information model."""

    events_received_total: int = Field(
        default=0, description="Total events received"
    )
    events_published_total: int = Field(
        default=0, description="Total events published to Kafka"
    )
    events_dlq_total: int = Field(
        default=0, description="Total events sent to DLQ"
    )
    events_buffered_current: int = Field(
        default=0, description="Current buffered events count"
    )
    buffer_size_bytes: int = Field(
        default=0, description="Current buffer size in bytes"
    )
    kafka_errors_total: int = Field(
        default=0, description="Total Kafka errors"
    )
    processing_duration_seconds: float = Field(
        default=0.0, description="Average processing duration"
    )


class BufferStats(BaseModel):
    """Buffer statistics model."""

    total_events: int = Field(..., description="Total events in buffer")
    size_bytes: int = Field(..., description="Buffer size in bytes")
    oldest_event: datetime | None = Field(
        None, description="Timestamp of oldest event"
    )
    newest_event: datetime | None = Field(
        None, description="Timestamp of newest event"
    )
    files_count: int = Field(..., description="Number of buffer files")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    timestamp: datetime = Field(..., description="Error timestamp")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error details"
    )
