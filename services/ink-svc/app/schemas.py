"""
Pydantic models for ink capture service API schemas.

This module defines the request/response models for the digital ink capture
API, including stroke data structures, session management, and event payloads.
"""

from datetime import datetime
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, Field, validator


class Point(BaseModel):
    """
    A single point in a digital ink stroke.

    Represents a coordinate with pressure and timing information captured
    from stylus or finger input.
    """

    x: float = Field(..., description="X coordinate", ge=0)
    y: float = Field(..., description="Y coordinate", ge=0)
    pressure: float = Field(default=1.0, description="Pressure value", ge=0.0, le=1.0)
    timestamp: int = Field(..., description="Timestamp in milliseconds since stroke start")


class Stroke(BaseModel):
    """
    A collection of points forming a continuous stroke.

    Represents a single drawing stroke with metadata about the input device
    and drawing context.
    """

    stroke_id: UUID = Field(..., description="Unique identifier for the stroke")
    points: list[Point] = Field(
        ..., description="Ordered list of points in the stroke", min_items=1
    )
    tool_type: str = Field(default="pen", description="Input tool type: pen, finger, eraser")
    color: str = Field(default="#000000", description="Stroke color in hex format")
    width: float = Field(default=2.0, description="Stroke width in pixels", gt=0)
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Stroke creation timestamp"
    )

    @validator("tool_type")
    @classmethod
    def validate_tool_type(cls: type[Self], v: str) -> str:  # noqa: N805
        """Validate tool type is supported."""
        allowed_tools = {"pen", "finger", "eraser", "highlighter"}
        if v not in allowed_tools:
            raise ValueError(f"Tool type must be one of: {allowed_tools}")
        return v

    @validator("color")
    @classmethod
    def validate_color(cls: type[Self], v: str) -> str:  # noqa: N805
        """Validate color is a valid hex color."""
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Color must be a 7-character hex string starting with #")
        try:
            int(v[1:], 16)
        except ValueError as exc:
            raise ValueError("Invalid hex color format") from exc
        return v


class StrokeRequest(BaseModel):
    """
    Request model for submitting digital ink strokes.

    Contains session information and a batch of strokes to be processed
    and stored.
    """

    session_id: UUID = Field(..., description="Unique session identifier")
    learner_id: UUID = Field(..., description="Learner who created the strokes")
    subject: str = Field(..., description="Subject area (math, science, etc.)", min_length=1)
    strokes: list[Stroke] = Field(..., description="List of strokes to submit", min_items=1)
    page_number: int = Field(default=1, description="Page number within the session", ge=1)
    canvas_width: float = Field(..., description="Canvas width in pixels", gt=0)
    canvas_height: float = Field(..., description="Canvas height in pixels", gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator("strokes")
    @classmethod
    def validate_stroke_count(  # noqa: N805
        cls: type[Self], v: list[Stroke]
    ) -> list[Stroke]:
        """Validate stroke count doesn't exceed limits."""
        max_strokes = 1000  # Could be made configurable
        if len(v) > max_strokes:
            raise ValueError(f"Too many strokes. Maximum allowed: {max_strokes}")
        return v


class StrokeResponse(BaseModel):
    """Response model for stroke submission."""

    session_id: UUID = Field(..., description="Session identifier")
    page_id: UUID = Field(..., description="Generated page identifier")
    s3_key: str = Field(..., description="S3 storage key for the page data")
    stroke_count: int = Field(..., description="Number of strokes processed")
    recognition_job_id: UUID | None = Field(
        default=None, description="ID of triggered recognition job"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class InkSession(BaseModel):
    """Model representing an active ink capture session."""

    session_id: UUID = Field(..., description="Unique session identifier")
    learner_id: UUID = Field(..., description="Learner ID")
    subject: str = Field(..., description="Subject area")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Session creation time"
    )
    last_activity: datetime = Field(
        default_factory=datetime.utcnow, description="Last activity timestamp"
    )
    page_count: int = Field(default=0, description="Number of pages in session")
    status: str = Field(default="active", description="Session status")

    @validator("status")
    @classmethod
    def validate_status(cls: type[Self], v: str) -> str:  # noqa: N805
        """Validate session status."""
        allowed_statuses = {"active", "completed", "expired", "cancelled"}
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v


class InkPageData(BaseModel):
    """
    Complete page data structure for NDJSON storage.

    This is the format stored in S3 and used for recognition processing.
    """

    page_id: UUID = Field(..., description="Unique page identifier")
    session_id: UUID = Field(..., description="Session identifier")
    learner_id: UUID = Field(..., description="Learner ID")
    subject: str = Field(..., description="Subject area")
    page_number: int = Field(..., description="Page number in session")
    canvas_width: float = Field(..., description="Canvas dimensions")
    canvas_height: float = Field(..., description="Canvas dimensions")
    strokes: list[Stroke] = Field(..., description="All strokes on the page")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Page creation time")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class InkReadyEvent(BaseModel):
    """Event payload for INK_READY events."""

    event_type: str = Field(default="INK_READY", description="Event type")
    session_id: UUID = Field(..., description="Session identifier")
    page_id: UUID = Field(..., description="Page identifier")
    learner_id: UUID = Field(..., description="Learner ID")
    subject: str = Field(..., description="Subject area")
    s3_key: str = Field(..., description="S3 storage key")
    stroke_count: int = Field(..., description="Number of strokes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Health check timestamp"
    )
    version: str = Field(..., description="Service version")
    dependencies: dict[str, str] = Field(default_factory=dict, description="Dependency status")
