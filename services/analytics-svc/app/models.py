"""Pydantic models for Analytics Service."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class AnalyticsResponse(BaseModel, Generic[T]):
    """Generic analytics response wrapper."""

    data: T = Field(..., description="The analytics data")
    tenant_id: str = Field(..., description="Tenant ID")
    generated_at: datetime = Field(..., description="Response generation time")
    cache_hit: bool = Field(..., description="Whether response was from cache")


class SummaryMetrics(BaseModel):
    """Summary learning metrics."""

    total_learners: int = Field(..., description="Total number of learners")
    active_learners_today: int = Field(
        ..., description="Learners active today"
    )
    active_learners_week: int = Field(
        ..., description="Learners active this week"
    )
    total_sessions: int = Field(..., description="Total learning sessions")
    avg_session_duration_minutes: float = Field(
        ..., description="Average session duration in minutes"
    )
    total_correct_answers: int = Field(
        ..., description="Total correct answers"
    )
    total_incorrect_answers: int = Field(
        ..., description="Total incorrect answers"
    )
    overall_accuracy: float = Field(
        ..., description="Overall accuracy percentage"
    )
    concepts_mastered: int = Field(
        ..., description="Total concepts mastered"
    )
    avg_mastery_score: float = Field(
        ..., description="Average mastery score"
    )


class MasteryMetrics(BaseModel):
    """Mastery progression metrics."""

    learner_id: str = Field(..., description="Learner identifier")
    concept_id: str = Field(..., description="Concept identifier")
    concept_name: str = Field(..., description="Concept name")
    mastery_score: float = Field(..., description="Mastery score (0-1)")
    attempts: int = Field(..., description="Number of attempts")
    correct_answers: int = Field(..., description="Correct answers")
    incorrect_answers: int = Field(..., description="Incorrect answers")
    accuracy: float = Field(..., description="Accuracy percentage")
    first_attempt: datetime = Field(..., description="First attempt timestamp")
    last_attempt: datetime = Field(..., description="Last attempt timestamp")
    mastery_achieved_at: datetime | None = Field(
        None, description="Mastery achievement timestamp"
    )


class StreakMetrics(BaseModel):
    """Learning streak metrics."""

    learner_id: str = Field(..., description="Learner identifier")
    current_streak: int = Field(..., description="Current learning streak")
    longest_streak: int = Field(..., description="Longest learning streak")
    total_learning_days: int = Field(
        ..., description="Total days with learning activity"
    )
    streak_start_date: datetime = Field(
        ..., description="Current streak start date"
    )
    last_learning_date: datetime = Field(
        ..., description="Last learning activity date"
    )
    avg_sessions_per_day: float = Field(
        ..., description="Average sessions per learning day"
    )
