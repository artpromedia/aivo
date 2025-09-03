"""
Core enumerations for the Approval Service.
"""
from enum import Enum


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ParticipantRole(str, Enum):
    """Roles for approval participants."""
    GUARDIAN = "guardian"
    TEACHER = "teacher"
    ADMINISTRATOR = "administrator"
    SPECIAL_EDUCATION_COORDINATOR = "special_education_coordinator"
    PRINCIPAL = "principal"


class DecisionType(str, Enum):
    """Types of decisions participants can make."""
    APPROVE = "approve"
    REJECT = "reject"


class ApprovalType(str, Enum):
    """Types of approval workflows."""
    IEP_DOCUMENT = "iep_document"
    ASSESSMENT_PLAN = "assessment_plan"
    PLACEMENT_CHANGE = "placement_change"
    SERVICE_MODIFICATION = "service_modification"
    BEHAVIORAL_PLAN = "behavioral_plan"


class NotificationChannel(str, Enum):
    """Channels for sending notifications."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class Priority(str, Enum):
    """Priority levels for approval requests."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class WebhookEventType(str, Enum):
    """Types of webhook events."""
    APPROVAL_REQUESTED = "approval_requested"
    DECISION_MADE = "decision_made"
    APPROVAL_COMPLETED = "approval_completed"
    APPROVAL_REJECTED = "approval_rejected"
    APPROVAL_EXPIRED = "approval_expired"
    APPROVAL_CANCELLED = "approval_cancelled"
    REMINDER_SENT = "reminder_sent"
