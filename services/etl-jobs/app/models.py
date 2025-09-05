"""Pydantic models for ETL data structures."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawEvent(BaseModel):
    """Raw event model matching the event collector output."""

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

    # ETL metadata
    processed_at: datetime | None = Field(
        None, description="When this event was processed by ETL"
    )
    partition_date: str | None = Field(
        None, description="Partition date (YYYY-MM-DD)"
    )
    s3_path: str | None = Field(None, description="S3 path of source file")


class ProcessingBatch(BaseModel):
    """Batch of events for processing."""

    batch_id: str = Field(..., description="Unique batch identifier")
    events: List[RawEvent] = Field(..., description="Events in this batch")
    created_at: datetime = Field(..., description="Batch creation timestamp")
    partition_date: str = Field(..., description="Target partition date")
    s3_key: Optional[str] = Field(None, description="S3 key for this batch")
    status: str = Field(default="pending", description="Batch status")


class MinuteMetrics(BaseModel):
    """Minute-level aggregated metrics."""

    learner_id: str = Field(..., description="Learner identifier")
    minute_timestamp: datetime = Field(..., description="Minute timestamp")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # Event counts
    total_events: int = Field(default=0, description="Total events in minute")
    page_views: int = Field(default=0, description="Page view events")
    interactions: int = Field(default=0, description="Interaction events")
    assessments_started: int = Field(default=0, description="Assessments started")
    assessments_completed: int = Field(default=0, description="Assessments completed")
    lessons_started: int = Field(default=0, description="Lessons started")
    lessons_completed: int = Field(default=0, description="Lessons completed")
    errors: int = Field(default=0, description="Error events")
    
    # Timing metrics
    time_spent_seconds: float = Field(default=0.0, description="Time spent")
    
    # Meta
    created_at: datetime = Field(..., description="Record creation time")
    partition_date: str = Field(..., description="Partition date")


class SessionMetrics(BaseModel):
    """Session-level aggregated metrics."""

    session_id: str = Field(..., description="Session identifier")
    learner_id: str = Field(..., description="Learner identifier")
    session_start: datetime = Field(..., description="Session start time")
    session_end: Optional[datetime] = Field(None, description="Session end time")
    
    # Duration
    duration_seconds: Optional[float] = Field(
        None, description="Session duration"
    )
    
    # Activity metrics
    total_events: int = Field(default=0, description="Total events in session")
    unique_pages: int = Field(default=0, description="Unique pages visited")
    total_interactions: int = Field(default=0, description="Total interactions")
    
    # Learning metrics
    lessons_attempted: int = Field(default=0, description="Lessons attempted")
    lessons_completed: int = Field(default=0, description="Lessons completed")
    assessments_attempted: int = Field(default=0, description="Assessments attempted")
    assessments_completed: int = Field(default=0, description="Assessments completed")
    
    # Performance
    avg_assessment_score: Optional[float] = Field(
        None, description="Average assessment score"
    )
    completion_rate: float = Field(
        default=0.0, description="Completion rate for attempted content"
    )
    
    # Meta
    is_active: bool = Field(default=True, description="Is session still active")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    created_at: datetime = Field(..., description="Record creation time")
    updated_at: datetime = Field(..., description="Record update time")
    partition_date: str = Field(..., description="Partition date")


class MasteryDelta(BaseModel):
    """Mastery level changes for learners."""

    learner_id: str = Field(..., description="Learner identifier")
    content_id: str = Field(..., description="Content/skill identifier")
    content_type: str = Field(..., description="Type of content (lesson, skill, etc)")
    
    # Mastery tracking
    previous_mastery: Optional[float] = Field(
        None, description="Previous mastery level (0-1)"
    )
    current_mastery: float = Field(..., description="Current mastery level (0-1)")
    mastery_delta: float = Field(..., description="Change in mastery")
    
    # Context
    trigger_event_id: str = Field(..., description="Event that triggered change")
    trigger_event_type: str = Field(..., description="Type of trigger event")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # Metadata
    confidence_score: Optional[float] = Field(
        None, description="Confidence in mastery calculation"
    )
    evidence_count: int = Field(
        default=1, description="Number of evidence points"
    )
    
    # Meta
    timestamp: datetime = Field(..., description="When mastery changed")
    created_at: datetime = Field(..., description="Record creation time")
    partition_date: str = Field(..., description="Partition date")


class ETLJobStatus(BaseModel):
    """Status tracking for ETL jobs."""

    job_id: str = Field(..., description="Unique job identifier")
    job_type: str = Field(..., description="Type of ETL job")
    status: str = Field(..., description="Job status")
    
    # Timing
    started_at: datetime = Field(..., description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    
    # Metrics
    records_processed: int = Field(default=0, description="Records processed")
    records_failed: int = Field(default=0, description="Records failed")
    bytes_processed: int = Field(default=0, description="Bytes processed")
    
    # Error tracking
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retries")
    
    # Meta
    created_at: datetime = Field(..., description="Record creation time")
    updated_at: datetime = Field(..., description="Record update time")
