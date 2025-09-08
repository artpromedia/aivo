"""
Enums for IEP Service.
"""

from enum import Enum


class IepStatus(Enum):
    """IEP document status."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    ARCHIVED = "archived"


class GoalType(Enum):
    """Types of IEP goals."""

    ACADEMIC = "academic"
    BEHAVIORAL = "behavioral"
    FUNCTIONAL = "functional"
    SOCIAL = "social"
    COMMUNICATION = "communication"
    TRANSITION = "transition"


class GoalStatus(Enum):
    """Goal progress status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"
    DISCONTINUED = "discontinued"


class AccommodationType(Enum):
    """Types of accommodations."""

    INSTRUCTIONAL = "instructional"
    ASSESSMENT = "assessment"
    BEHAVIORAL = "behavioral"
    ENVIRONMENTAL = "environmental"
    TECHNOLOGY = "technology"
    SCHEDULING = "scheduling"


class ApprovalStatus(Enum):
    """Approval workflow status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class EventType(Enum):
    """Event types for IEP service."""

    IEP_CREATED = "IEP_CREATED"
    IEP_UPDATED = "IEP_UPDATED"
    IEP_SUBMITTED = "IEP_SUBMITTED"
    IEP_APPROVED = "IEP_APPROVED"
    IEP_REJECTED = "IEP_REJECTED"
    GOAL_ADDED = "GOAL_ADDED"
    GOAL_UPDATED = "GOAL_UPDATED"
    ACCOMMODATION_ADDED = "ACCOMMODATION_ADDED"
