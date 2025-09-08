"""
Enums for the assessment service.
"""

from enum import Enum


class SubjectType(Enum):
    """Subject types for assessment."""

    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    ENGLISH = "english"
    HISTORY = "history"
    GEOGRAPHY = "geography"


class LevelType(Enum):
    """Learning levels L0-L4."""

    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class SessionStatus(Enum):
    """Assessment session status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class QuestionType(Enum):
    """Question types."""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"


class AnswerResult(Enum):
    """Answer evaluation result."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"


class EventType(Enum):
    """Event types for assessment."""

    BASELINE_COMPLETE = "BASELINE_COMPLETE"
    SESSION_STARTED = "SESSION_STARTED"
    QUESTION_ANSWERED = "QUESTION_ANSWERED"
