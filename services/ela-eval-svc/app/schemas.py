"""
Pydantic models for ELA evaluator service API schemas.

This module defines the request/response models for rubric scoring,
PII moderation, and content safety evaluation.
"""

from datetime import datetime
from enum import Enum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, validator


class GradeBand(str, Enum):
    """Supported grade bands for rubric evaluation."""

    K_2 = "K-2"
    GRADES_3_5 = "3-5"
    GRADES_6_8 = "6-8"
    GRADES_9_12 = "9-12"


class RubricCriterion(str, Enum):
    """Standard ELA rubric criteria."""

    IDEAS_AND_CONTENT = "ideas_and_content"
    ORGANIZATION = "organization"
    VOICE = "voice"
    WORD_CHOICE = "word_choice"
    SENTENCE_FLUENCY = "sentence_fluency"
    CONVENTIONS = "conventions"


class ScoreLevel(int, Enum):
    """Rubric scoring levels (1-4 scale)."""

    BEGINNING = 1
    DEVELOPING = 2
    PROFICIENT = 3
    ADVANCED = 4


class PIIEntity(BaseModel):
    """Detected PII entity information."""

    entity_type: str = Field(..., description="Type of PII detected")
    text: str = Field(..., description="Original text containing PII")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    confidence: float = Field(
        ..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0
    )
    anonymized_text: str = Field(
        ..., description="Anonymized replacement text"
    )


class ContentModerationFlag(BaseModel):
    """Content moderation flag information."""

    category: str = Field(..., description="Moderation category")
    severity: str = Field(..., description="Severity level")
    confidence: float = Field(
        ..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0
    )
    description: str = Field(..., description="Description of the issue")


class RubricScore(BaseModel):
    """Individual rubric criterion score."""

    criterion: RubricCriterion = Field(..., description="Rubric criterion")
    score: ScoreLevel = Field(..., description="Score level (1-4)")
    reasoning: str = Field(..., description="Detailed scoring rationale")
    strengths: list[str] = Field(
        default_factory=list, description="Identified strengths"
    )
    areas_for_improvement: list[str] = Field(
        default_factory=list, description="Areas needing improvement"
    )


class EvaluationRequest(BaseModel):
    """Request model for ELA rubric evaluation."""

    prompt: str = Field(
        ...,
        description="Writing prompt or assignment instructions",
        max_length=5000,
    )
    submission: str = Field(
        ..., description="Student writing submission", max_length=10000
    )
    grade_band: GradeBand = Field(..., description="Grade band for evaluation")
    criteria: list[RubricCriterion] = Field(
        default_factory=lambda: list(RubricCriterion),
        description="Specific criteria to evaluate",
    )
    student_id: UUID | None = Field(
        default=None, description="Optional student identifier"
    )
    assignment_id: UUID | None = Field(
        default=None, description="Optional assignment identifier"
    )
    enable_pii_detection: bool = Field(
        default=True, description="Enable PII detection and anonymization"
    )
    enable_content_moderation: bool = Field(
        default=True, description="Enable content moderation"
    )

    @validator("submission")
    @classmethod
    def validate_submission_not_empty(cls: type[Self], v: str) -> str:
        """Validate submission is not empty or only whitespace."""
        if not v or not v.strip():
            raise ValueError("Submission cannot be empty")
        return v.strip()

    @validator("criteria")
    @classmethod
    def validate_criteria_not_empty(
        cls: type[Self], v: list[RubricCriterion]
    ) -> list[RubricCriterion]:
        """Validate at least one criterion is specified."""
        if not v:
            v = list(RubricCriterion)
        return v


class EvaluationResponse(BaseModel):
    """Response model for ELA rubric evaluation."""

    evaluation_id: UUID = Field(
        ..., description="Unique evaluation identifier"
    )
    scores: list[RubricScore] = Field(..., description="Rubric scores")
    overall_score: float = Field(
        ..., description="Overall weighted score (1.0-4.0)", ge=1.0, le=4.0
    )
    grade_band: GradeBand = Field(..., description="Grade band used")

    # Content safety and moderation
    pii_detected: bool = Field(
        default=False, description="Whether PII was detected"
    )
    pii_entities: list[PIIEntity] = Field(
        default_factory=list, description="Detected PII entities"
    )
    content_flags: list[ContentModerationFlag] = Field(
        default_factory=list, description="Content moderation flags"
    )
    is_safe: bool = Field(
        default=True, description="Overall content safety assessment"
    )

    # Teacher notes and feedback
    teacher_notes: str = Field(
        default="", description="Generated teacher feedback notes"
    )
    suggested_next_steps: list[str] = Field(
        default_factory=list, description="Suggested learning activities"
    )

    # Metadata
    processed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Processing timestamp"
    )
    processing_time_ms: int = Field(
        ..., description="Processing time in milliseconds"
    )
    model_used: str = Field(..., description="AI model used for evaluation")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service health status")
    service_name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Current timestamp")
    dependencies: dict[str, str] = Field(
        default_factory=dict, description="Dependency health status"
    )


class EvaluationHistoryRequest(BaseModel):
    """Request model for evaluation history."""

    student_id: UUID | None = Field(
        default=None, description="Filter by student ID"
    )
    assignment_id: UUID | None = Field(
        default=None, description="Filter by assignment ID"
    )
    grade_band: GradeBand | None = Field(
        default=None, description="Filter by grade band"
    )
    start_date: datetime | None = Field(
        default=None, description="Start date for filtering"
    )
    end_date: datetime | None = Field(
        default=None, description="End date for filtering"
    )
    limit: int = Field(
        default=50, description="Maximum number of results", le=1000
    )
    offset: int = Field(default=0, description="Pagination offset", ge=0)


class EvaluationSummary(BaseModel):
    """Summary model for evaluation history."""

    evaluation_id: UUID = Field(..., description="Evaluation identifier")
    student_id: UUID | None = Field(
        default=None, description="Student identifier"
    )
    assignment_id: UUID | None = Field(
        default=None, description="Assignment identifier"
    )
    grade_band: GradeBand = Field(..., description="Grade band")
    overall_score: float = Field(..., description="Overall score")
    processed_at: datetime = Field(..., description="Processing timestamp")
    has_content_flags: bool = Field(
        default=False, description="Whether content was flagged"
    )


class EvaluationHistoryResponse(BaseModel):
    """Response model for evaluation history."""

    evaluations: list[EvaluationSummary] = Field(
        default_factory=list, description="Evaluation summaries"
    )
    total_count: int = Field(..., description="Total number of evaluations")
    has_more: bool = Field(
        default=False, description="Whether more results exist"
    )
