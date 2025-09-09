"""Database models for Problem Session Orchestrator."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()


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


class ProblemSession(Base):
    """Database model for problem sessions."""

    __tablename__ = "problem_sessions"

    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    learner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default=SessionStatus.PLANNING, nullable=False, index=True
    )
    current_phase: Mapped[str] = mapped_column(
        String(20), default=SessionPhase.PLAN, nullable=False
    )

    # Session metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    # Activity planning data
    activity_plan_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    planned_activities: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    current_activity_index: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # Session configuration
    session_duration_minutes: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
    )
    canvas_width: Mapped[int] = mapped_column(
        Integer, default=800, nullable=False
    )
    canvas_height: Mapped[int] = mapped_column(
        Integer, default=600, nullable=False
    )

    # Session results
    total_problems_attempted: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    total_problems_correct: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    average_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # External service references
    ink_session_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    brain_runtime_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )


class ProblemAttempt(Base):
    """Database model for individual problem attempts within a session."""

    __tablename__ = "problem_attempts"

    attempt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    activity_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Problem data
    problem_type: Mapped[str] = mapped_column(String(50), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Attempt timing
    presented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    ink_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ink_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recognized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    graded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    feedback_provided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Recognition results
    ink_page_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    recognition_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    recognized_expression: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    recognition_ast: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )

    # Grading results
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    grade_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Final status
    attempt_status: Mapped[str] = mapped_column(
        String(30), default="presented", nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
