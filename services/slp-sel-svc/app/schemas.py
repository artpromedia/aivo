"""Pydantic models for SLP/SEL service."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class ArticulationLevel(str, Enum):
    """Articulation difficulty levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class DrillType(str, Enum):
    """Types of speech drills."""

    PHONEME = "phoneme"
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"


class SentimentType(str, Enum):
    """Sentiment analysis results."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class PrivacyLevel(str, Enum):
    """Journal entry privacy levels."""

    PRIVATE = "private"
    THERAPIST_ONLY = "therapist_only"
    TEAM_SHARED = "team_shared"


# Speech Recognition and Articulation Models


class PhonemeTimingData(BaseModel):
    """Phoneme timing data from ASR."""

    phoneme: str = Field(..., description="IPA phoneme symbol")
    start_time: float = Field(..., description="Start time in seconds", ge=0.0)
    end_time: float = Field(..., description="End time in seconds", ge=0.0)
    confidence: float = Field(
        ..., description="Confidence score", ge=0.0, le=1.0
    )
    expected_phoneme: str | None = Field(
        default=None, description="Expected phoneme for comparison"
    )

    @validator("end_time", always=True)
    @classmethod
    def end_time_after_start(cls, v: float, values: dict[str, Any]) -> float:
        """Validate end time is after start time."""
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("end_time must be greater than start_time")
        return v


class AudioProcessingRequest(BaseModel):
    """Request for audio processing and articulation analysis."""

    audio_data: bytes = Field(..., description="Audio file data")
    target_phonemes: list[str] = Field(
        ..., description="Target phonemes to analyze"
    )
    drill_type: DrillType = Field(
        default=DrillType.PHONEME, description="Type of drill"
    )
    student_id: UUID | None = Field(
        default=None, description="Student identifier"
    )
    session_id: UUID | None = Field(
        default=None, description="Session identifier"
    )

    @validator("target_phonemes")
    @classmethod
    def validate_phonemes(cls, v: list[str]) -> list[str]:
        """Validate phoneme list is not empty."""
        if not v:
            raise ValueError("target_phonemes cannot be empty")
        return v


class ArticulationScore(BaseModel):
    """Articulation scoring results."""

    phoneme: str = Field(..., description="Evaluated phoneme")
    accuracy_score: float = Field(
        ..., description="Accuracy score", ge=0.0, le=1.0
    )
    timing_score: float = Field(
        ..., description="Timing score", ge=0.0, le=1.0
    )
    consistency_score: float = Field(
        ..., description="Consistency score", ge=0.0, le=1.0
    )
    fluency_score: float = Field(
        ..., description="Fluency score", ge=0.0, le=1.0
    )
    overall_score: float = Field(
        ..., description="Overall weighted score", ge=0.0, le=1.0
    )
    feedback: list[str] = Field(
        default_factory=list, description="Feedback messages"
    )


class DrillSession(BaseModel):
    """Speech drill session."""

    session_id: UUID = Field(default_factory=uuid4)
    student_id: UUID = Field(..., description="Student identifier")
    drill_type: DrillType = Field(..., description="Type of drill")
    target_phonemes: list[str] = Field(
        ..., description="Target phonemes for session"
    )
    articulation_level: ArticulationLevel = Field(
        ..., description="Difficulty level"
    )
    scores: list[ArticulationScore] = Field(
        default_factory=list, description="Articulation scores"
    )
    session_duration_seconds: float | None = Field(
        default=None, description="Session duration in seconds", ge=0.0
    )
    completed_at: datetime | None = Field(
        default=None, description="Session completion time"
    )
    notes: str = Field(default="", description="Session notes")


class DrillSessionResponse(BaseModel):
    """Response for drill session creation/analysis."""

    session: DrillSession = Field(..., description="Drill session data")
    overall_performance: float = Field(
        ..., description="Overall session performance", ge=0.0, le=1.0
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Improvement recommendations"
    )
    next_level_ready: bool = Field(
        default=False, description="Ready for next difficulty level"
    )


# SEL Journaling Models


class JournalEntry(BaseModel):
    """SEL journal entry."""

    entry_id: UUID = Field(default_factory=uuid4)
    student_id: UUID = Field(..., description="Student identifier")
    title: str = Field(..., description="Entry title", max_length=200)
    content: str = Field(..., description="Entry content", max_length=5000)
    privacy_level: PrivacyLevel = Field(
        default=PrivacyLevel.PRIVATE, description="Privacy level"
    )
    mood_rating: int | None = Field(
        default=None, description="Mood rating 1-10", ge=1, le=10
    )
    tags: list[str] = Field(default_factory=list, description="Entry tags")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp"
    )

    @validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content is not empty."""
        if not v.strip():
            raise ValueError("content cannot be empty")
        return v


class JournalEntryRequest(BaseModel):
    """Request to create/update journal entry."""

    title: str = Field(..., description="Entry title", max_length=200)
    content: str = Field(..., description="Entry content", max_length=5000)
    privacy_level: PrivacyLevel = Field(
        default=PrivacyLevel.PRIVATE, description="Privacy level"
    )
    mood_rating: int | None = Field(
        default=None, description="Mood rating 1-10", ge=1, le=10
    )
    tags: list[str] = Field(default_factory=list, description="Entry tags")


class SentimentAnalysis(BaseModel):
    """Sentiment analysis results."""

    sentiment: SentimentType = Field(..., description="Overall sentiment")
    confidence: float = Field(
        ..., description="Confidence score", ge=0.0, le=1.0
    )
    positive_score: float = Field(
        ..., description="Positive sentiment score", ge=0.0, le=1.0
    )
    negative_score: float = Field(
        ..., description="Negative sentiment score", ge=0.0, le=1.0
    )
    neutral_score: float = Field(
        ..., description="Neutral sentiment score", ge=0.0, le=1.0
    )
    key_emotions: list[str] = Field(
        default_factory=list, description="Detected emotions"
    )


class JournalEntryResponse(BaseModel):
    """Response for journal entry operations."""

    entry: JournalEntry = Field(..., description="Journal entry")
    sentiment_analysis: SentimentAnalysis | None = Field(
        default=None, description="Sentiment analysis results"
    )
    word_count: int = Field(..., description="Word count", ge=0)
    reading_time_minutes: float = Field(
        ..., description="Estimated reading time in minutes", ge=0.0
    )


class JournalHistoryRequest(BaseModel):
    """Request for journal history."""

    student_id: UUID = Field(..., description="Student identifier")
    start_date: datetime | None = Field(
        default=None, description="Start date filter"
    )
    end_date: datetime | None = Field(
        default=None, description="End date filter"
    )
    privacy_levels: list[PrivacyLevel] = Field(
        default_factory=lambda: list(PrivacyLevel),
        description="Privacy levels to include",
    )
    tags: list[str] = Field(default_factory=list, description="Filter by tags")
    limit: int = Field(
        default=50, description="Maximum results", ge=1, le=1000
    )
    offset: int = Field(default=0, description="Pagination offset", ge=0)


class JournalHistoryResponse(BaseModel):
    """Response for journal history."""

    entries: list[JournalEntryResponse] = Field(
        default_factory=list, description="Journal entries"
    )
    total_count: int = Field(..., description="Total number of entries", ge=0)
    page_count: int = Field(..., description="Total number of pages", ge=0)
    current_page: int = Field(..., description="Current page number", ge=0)
    has_more: bool = Field(default=False, description="More entries available")
    sentiment_trends: dict[str, Any] = Field(
        default_factory=dict, description="Sentiment analysis trends"
    )


# Health and Status Models


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service status")
    service_name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    dependencies: dict[str, str] = Field(
        default_factory=dict, description="Dependency status"
    )
