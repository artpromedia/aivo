"""
GraphQL schema types for IEP Service.
"""

import json
from datetime import date, datetime

import strawberry

from .enums import AccommodationType, ApprovalStatus, GoalStatus, GoalType, IepStatus


# Custom scalar for JSON data like vector clocks
@strawberry.scalar(
    serialize=lambda v: json.dumps(v) if v else "{}",
    parse_value=lambda v: json.loads(v) if v else {},
)
class JSON:
    """Custom JSON scalar type for complex data structures."""

    pass


@strawberry.type
class Goal:
    """IEP Goal type."""

    id: str
    iep_id: str
    goal_type: GoalType
    status: GoalStatus
    title: str
    description: str
    measurable_criteria: str
    target_date: date
    baseline_data: str | None = None
    progress_notes: list[str] = strawberry.field(default_factory=list)
    responsible_staff: list[str] = strawberry.field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    # CRDT metadata
    version: int = 1
    vector_clock: JSON = strawberry.field(default_factory=dict)


@strawberry.type
class Accommodation:
    """IEP Accommodation type."""

    id: str
    iep_id: str
    accommodation_type: AccommodationType
    title: str
    description: str
    implementation_notes: str | None = None
    applicable_settings: list[str] = strawberry.field(default_factory=list)
    frequency: str | None = None
    duration: str | None = None
    responsible_staff: list[str] = strawberry.field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    # CRDT metadata
    version: int = 1
    vector_clock: JSON = strawberry.field(default_factory=dict)


@strawberry.type
class ApprovalRecord:
    """Approval record for IEP documents."""

    id: str
    iep_id: str
    approver_id: str
    approver_role: str
    status: ApprovalStatus
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    rejection_reason: str | None = None
    comments: str | None = None
    created_at: datetime


@strawberry.type
class IepDoc:
    """Main IEP Document type with CRDT support."""

    id: str
    student_id: str
    student_name: str
    status: IepStatus

    # Document metadata
    school_year: str
    effective_date: date
    expiry_date: date
    meeting_date: date | None = None

    # IEP content
    goals: list[Goal] = strawberry.field(default_factory=list)
    accommodations: list[Accommodation] = strawberry.field(default_factory=list)

    # Additional IEP data
    present_levels: str | None = None
    transition_services: str | None = None
    special_factors: list[str] = strawberry.field(default_factory=list)
    placement_details: str | None = None

    # Approval workflow
    approval_records: list[ApprovalRecord] = strawberry.field(default_factory=list)
    pending_approval_count: int = 0
    required_approval_count: int = 2

    # Document tracking
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    # CRDT metadata for collaborative editing
    version: int = 1
    vector_clock: JSON = strawberry.field(default_factory=dict)
    operation_log: list[JSON] = strawberry.field(default_factory=list)

    @strawberry.field
    def is_approved(self) -> bool:
        """Check if IEP has required approvals."""
        approved_count = sum(
            1 for record in self.approval_records if record.status == ApprovalStatus.APPROVED
        )
        return approved_count >= self.required_approval_count

    @strawberry.field
    def approval_progress(self) -> str:
        """Get approval progress as string."""
        approved_count = sum(
            1 for record in self.approval_records if record.status == ApprovalStatus.APPROVED
        )
        return f"{approved_count}/{self.required_approval_count}"


# Input types for mutations
@strawberry.input
class GoalInput:
    """Input type for creating/updating goals."""

    goal_type: GoalType
    title: str
    description: str
    measurable_criteria: str
    target_date: date
    baseline_data: str | None = None
    responsible_staff: list[str] = strawberry.field(default_factory=list)


@strawberry.input
class AccommodationInput:
    """Input type for creating/updating accommodations."""

    accommodation_type: AccommodationType
    title: str
    description: str
    implementation_notes: str | None = None
    applicable_settings: list[str] = strawberry.field(default_factory=list)
    frequency: str | None = None
    duration: str | None = None
    responsible_staff: list[str] = strawberry.field(default_factory=list)


@strawberry.input
class IepDocInput:
    """Input type for creating/updating IEP documents."""

    student_id: str
    student_name: str
    school_year: str
    effective_date: date
    expiry_date: date
    meeting_date: date | None = None
    present_levels: str | None = None
    transition_services: str | None = None
    special_factors: list[str] = strawberry.field(default_factory=list)
    placement_details: str | None = None
    goals: list[GoalInput] = strawberry.field(default_factory=list)
    accommodations: list[AccommodationInput] = strawberry.field(default_factory=list)


@strawberry.input
class CrdtOperation:
    """CRDT operation input for collaborative editing."""

    operation_type: str  # "insert", "delete", "update"
    path: str  # JSON path to the field
    value: str | None = None
    position: int | None = None
    author: str
    timestamp: datetime


# Response types
@strawberry.type
class IepMutationResult:
    """Result type for IEP mutations."""

    success: bool
    message: str
    iep: IepDoc | None = None
    errors: list[str] = strawberry.field(default_factory=list)


@strawberry.type
class ApprovalResult:
    """Result type for approval operations."""

    success: bool
    message: str
    approval_id: str | None = None
    status: ApprovalStatus | None = None
    errors: list[str] = strawberry.field(default_factory=list)
