"""Pydantic schemas for Problem Session Orchestrator API."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SubjectType(str, Enum):
    """Subject types for sessions."""

    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"


class SessionPhase(str, Enum):
    """Phases within a problem session."""

    PLAN = "plan"
    PRESENT = "present"
    INK = "ink"
    RECOGNIZE = "recognize"
    GRADE = "grade"
    FEEDBACK = "feedback"


class SessionStatus(str, Enum):
    """Problem session status."""

    PLANNING = "planning"
    ACTIVE = "active"
    WAITING_INK = "waiting_ink"
    RECOGNIZING = "recognizing"
    GRADING = "grading"
    PROVIDING_FEEDBACK = "providing_feedback"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class StartSessionRequest(BaseModel):
    """Request to start a new problem session."""

    learner_id: UUID = Field(..., description="Unique learner identifier")
    subject: SubjectType = Field(..., description="Subject for the session")
    session_duration_minutes: int = Field(
        default=30, ge=5, le=120, description="Session duration in minutes"
    )
    canvas_width: int = Field(
        default=800, ge=400, le=2000, description="Canvas width in pixels"
    )
    canvas_height: int = Field(
        default=600, ge=300, le=1500, description="Canvas height in pixels"
    )
    force_refresh: bool = Field(
        default=False, description="Force refresh of activity plan"
    )


class SessionResponse(BaseModel):
    """Response containing session information."""

    session_id: UUID = Field(..., description="Unique session identifier")
    learner_id: UUID = Field(..., description="Learner identifier")
    subject: SubjectType = Field(..., description="Session subject")
    status: SessionStatus = Field(..., description="Current session status")
    current_phase: SessionPhase = Field(
        ..., description="Current phase of session"
    )
    created_at: datetime = Field(..., description="Session creation timestamp")
    started_at: datetime | None = Field(
        None, description="Session start timestamp"
    )
    completed_at: datetime | None = Field(
        None, description="Session completion timestamp"
    )
    session_duration_minutes: int = Field(
        ..., description="Planned session duration"
    )
    total_problems_attempted: int = Field(
        ..., description="Number of problems attempted"
    )
    total_problems_correct: int = Field(
        ..., description="Number of problems answered correctly"
    )
    average_confidence: float | None = Field(
        None, description="Average recognition confidence"
    )
    current_activity: dict[str, Any] | None = Field(
        None, description="Current activity details"
    )
    canvas_width: int = Field(..., description="Canvas width in pixels")
    canvas_height: int = Field(..., description="Canvas height in pixels")
    ink_session_id: UUID | None = Field(
        None, description="Associated ink session ID"
    )
    error_message: str | None = Field(
        None, description="Error message if failed"
    )


class InkSubmissionRequest(BaseModel):
    """Request to submit ink for recognition."""

    session_id: UUID = Field(..., description="Session identifier")
    page_number: int = Field(default=1, description="Page number")
    strokes: list[dict[str, Any]] = Field(..., description="Ink stroke data")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class InkSubmissionResponse(BaseModel):
    """Response from ink submission."""

    session_id: UUID = Field(..., description="Session identifier")
    page_id: UUID = Field(..., description="Ink page identifier")
    recognition_job_id: UUID | None = Field(
        None, description="Recognition job identifier"
    )
    status: str = Field(..., description="Submission status")
    message: str = Field(..., description="Status message")


class RecognitionResult(BaseModel):
    """Recognition result from math or science service."""

    success: bool = Field(..., description="Recognition success status")
    confidence: float = Field(..., description="Recognition confidence")
    expression: str | None = Field(None, description="Recognized expression")
    latex: str | None = Field(None, description="LaTeX representation")
    ast: dict[str, Any] | None = Field(
        None, description="Abstract syntax tree"
    )
    processing_time: float = Field(
        ..., description="Processing time in seconds"
    )
    error_message: str | None = Field(
        None, description="Error message if failed"
    )


class GradingResult(BaseModel):
    """Grading result from subject service."""

    is_correct: bool = Field(..., description="Answer correctness")
    score: float = Field(..., description="Numerical score (0.0-1.0)")
    feedback: str = Field(..., description="Feedback message")
    is_equivalent: bool | None = Field(
        None, description="Mathematical equivalence"
    )
    expected_answer: str | None = Field(None, description="Expected answer")
    steps: list[str] | None = Field(None, description="Solution steps")


class SessionResultEvent(BaseModel):
    """Event payload for SESSION_RESULT events."""

    event_type: str = Field(default="SESSION_RESULT", description="Event type")
    session_id: UUID = Field(..., description="Session identifier")
    learner_id: UUID = Field(..., description="Learner identifier")
    subject: SubjectType = Field(..., description="Session subject")
    status: SessionStatus = Field(..., description="Final session status")
    total_problems_attempted: int = Field(
        ..., description="Total problems attempted"
    )
    total_problems_correct: int = Field(
        ..., description="Total problems correct"
    )
    average_confidence: float | None = Field(
        None, description="Average recognition confidence"
    )
    session_duration_minutes: int = Field(
        ..., description="Actual session duration"
    )
    completed_at: datetime = Field(
        ..., description="Session completion timestamp"
    )
    performance_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Additional performance metrics"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(..., description="Response timestamp")
    dependencies: dict[str, str] = Field(
        default_factory=dict, description="Dependency status"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error details"
    )
