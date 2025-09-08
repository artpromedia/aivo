"""
Enums for the inference gateway service.
"""

from enum import Enum


class ModerationResult(Enum):
    """Moderation result status."""

    PASSED = "passed"
    BLOCKED = "blocked"
    ERROR = "error"
