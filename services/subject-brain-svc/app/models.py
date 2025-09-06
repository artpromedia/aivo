"""Subject-Brain service models for planner and runtime."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class SubjectType(str, Enum):
    """Subject types supported by the brain."""
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    LANGUAGE_ARTS = "language_arts"
    SOCIAL_STUDIES = "social_studies"
    FOREIGN_LANGUAGE = "foreign_language"


class MasteryLevel(str, Enum):
    """Mastery levels for learning objectives."""
    NOT_STARTED = "not_started"
    BEGINNING = "beginning"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"


class ActivityType(str, Enum):
    """Types of learning activities."""
    LESSON = "lesson"
    PRACTICE = "practice"
    ASSESSMENT = "assessment"
    REMEDIATION = "remediation"
    ENRICHMENT = "enrichment"


class RuntimeStatus(str, Enum):
    """Status of per-learner-subject runtime pods."""
    PENDING = "pending"
    RUNNING = "running"
    SCALING = "scaling"
    IDLE = "idle"
    TERMINATING = "terminating"
    TERMINATED = "terminated"


class LearnerBaseline(BaseModel):
    """Baseline assessment data for a learner in a subject."""
    learner_id: str
    subject: SubjectType
    grade_level: int
    assessment_date: datetime
    mastery_levels: dict[str, MasteryLevel] = Field(
        description="Topic/objective to mastery level mapping"
    )
    learning_style: str | None = None
    pace_preference: str | None = None
    
    
class CourseworkTopic(BaseModel):
    """Topic from current coursework."""
    topic_id: str
    name: str
    subject: SubjectType
    grade_level: int
    prerequisites: list[str] = Field(default_factory=list)
    learning_objectives: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int
    difficulty_level: int = Field(ge=1, le=10)


class TeacherConstraints(BaseModel):
    """Teacher-defined constraints for activity planning."""
    teacher_id: str
    subject: SubjectType
    max_activity_duration_minutes: int = 60
    preferred_activity_types: list[ActivityType] = Field(
        default_factory=list
    )
    blocked_topics: list[str] = Field(default_factory=list)
    required_topics: list[str] = Field(default_factory=list)
    assessment_frequency_days: int = 7
    remediation_threshold: MasteryLevel = MasteryLevel.DEVELOPING


class PlannerInput(BaseModel):
    """Input for the subject-brain planner."""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    learner_id: str
    subject: SubjectType
    baseline: LearnerBaseline
    available_topics: list[CourseworkTopic]
    teacher_constraints: TeacherConstraints
    session_duration_minutes: int = 30
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PlannedActivity(BaseModel):
    """A planned learning activity."""
    activity_id: str = Field(default_factory=lambda: str(uuid4()))
    type: ActivityType
    topic: CourseworkTopic
    estimated_duration_minutes: int
    difficulty_adjustment: float = Field(
        ge=0.5, le=2.0, description="Multiplier for base difficulty"
    )
    learning_objectives: list[str]
    prerequisites_met: bool
    rationale: str = Field(description="Why this activity was selected")


class ActivityPlan(BaseModel):
    """Complete activity plan for a learner session."""
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    learner_id: str
    subject: SubjectType
    activities: list[PlannedActivity]
    total_duration_minutes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    planner_version: str = "1.0"


class RuntimeRequest(BaseModel):
    """Request to start a per-learner-subject runtime."""
    runtime_id: str = Field(default_factory=lambda: str(uuid4()))
    learner_id: str
    subject: SubjectType
    activity_plan: ActivityPlan
    gpu_required: bool = True
    memory_mb: int = 2048
    cpu_cores: float = 1.0
    max_runtime_minutes: int = 120
    priority: int = Field(ge=1, le=10, default=5)


class RuntimeMetrics(BaseModel):
    """Metrics for runtime monitoring and autoscaling."""
    runtime_id: str
    gpu_queue_depth: int = 0
    gpu_utilization_percent: float = 0.0
    memory_usage_mb: int = 0
    cpu_utilization_percent: float = 0.0
    active_learners: int = 0
    pending_requests: int = 0
    last_activity_timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )


class RuntimePod(BaseModel):
    """Kubernetes pod runtime for per-learner-subject processing."""
    runtime_id: str
    learner_id: str
    subject: SubjectType
    pod_name: str
    namespace: str = "subject-brain"
    status: RuntimeStatus = RuntimeStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    last_activity_at: datetime | None = None
    ttl_seconds: int = 300  # Scale to zero after 5 minutes idle
    metrics: RuntimeMetrics
    node_name: str | None = None
    gpu_allocated: bool = False


class ScalingDecision(BaseModel):
    """HPA scaling decision based on metrics."""
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    current_replicas: int
    desired_replicas: int
    scaling_reason: str
    gpu_queue_threshold: int = 10
    cpu_threshold_percent: float = 70.0
    memory_threshold_percent: float = 80.0
    scale_up_triggered: bool = False
    scale_down_triggered: bool = False


class PlannerRequest(BaseModel):
    """API request to the planner service."""
    learner_id: str
    subject: SubjectType
    session_duration_minutes: int = 30
    force_refresh: bool = False


class PlannerResponse(BaseModel):
    """API response from the planner service."""
    success: bool
    plan: ActivityPlan | None = None
    runtime_request: RuntimeRequest | None = None
    error_message: str | None = None
    processing_time_ms: int


class RuntimeStatusResponse(BaseModel):
    """Status response for runtime queries."""
    runtime_id: str
    status: RuntimeStatus
    metrics: RuntimeMetrics
    estimated_completion_minutes: int | None = None
    current_activity: str | None = None
