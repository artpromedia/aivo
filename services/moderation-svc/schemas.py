"""Pydantic schemas for moderation service API."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field

from models import ContentType, ModerationStatus, DecisionType, SeverityLevel, FlagReason

# Request schemas

class ModerationDecisionRequest(BaseModel):
    """Request schema for making a moderation decision."""
    decision_type: DecisionType
    reason: str = Field(..., min_length=1, max_length=1000)
    notes: Optional[str] = Field(None, max_length=2000)
    moderator_id: str = Field(..., min_length=1)
    expires_at: Optional[datetime] = None
    confidence_level: Optional[int] = Field(None, ge=0, le=100)

class AppealRequest(BaseModel):
    """Request schema for submitting an appeal."""
    reason: str = Field(..., min_length=10, max_length=2000)
    evidence: Optional[str] = Field(None, max_length=5000)
    evidence_urls: Optional[List[str]] = None
    appellant_name: Optional[str] = None
    appellant_email: Optional[str] = None

# Response schemas

class QueueItemResponse(BaseModel):
    """Response schema for a moderation queue item."""
    id: UUID
    content_id: str
    content_type: ContentType
    content_url: Optional[str]
    content_preview: Optional[str]
    content_metadata: Optional[Dict[str, Any]]

    user_id: str
    tenant_id: Optional[str]
    session_id: Optional[str]

    flag_reason: FlagReason
    flag_details: Optional[str]
    severity_level: SeverityLevel
    confidence_score: Optional[int]

    status: ModerationStatus
    flagged_at: datetime
    reviewed_at: Optional[datetime]
    expires_at: Optional[datetime]

    flagged_by_system: bool
    flagged_by_user_id: Optional[str]

    # Include latest decision if any
    latest_decision: Optional['ModerationDecisionResponse'] = None

    class Config:
        from_attributes = True

class ModerationDecisionResponse(BaseModel):
    """Response schema for a moderation decision."""
    id: UUID
    queue_item_id: UUID
    decision_type: DecisionType
    reason: str
    notes: Optional[str]
    moderator_id: str
    moderator_name: Optional[str]
    decided_at: datetime
    expires_at: Optional[datetime]
    confidence_level: Optional[int]
    escalation_required: bool
    appeal_deadline: Optional[datetime]

    class Config:
        from_attributes = True

class QueueListResponse(BaseModel):
    """Response schema for queue list with pagination."""
    items: List[QueueItemResponse]
    total_count: int
    page_size: int
    offset: int
    has_more: bool

class QueueStatsResponse(BaseModel):
    """Response schema for moderation queue statistics."""
    total_pending: int
    total_in_review: int
    total_resolved_today: int
    total_resolved_week: int

    by_content_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_status: Dict[str, int]
    by_flag_reason: Dict[str, int]

    average_resolution_time_hours: Optional[float]
    median_resolution_time_hours: Optional[float]

    escalation_rate: float
    appeal_rate: float
    overturn_rate: float

    top_moderators: List[Dict[str, Any]]  # [{moderator_id, name, decisions_count}]

class AuditLogResponse(BaseModel):
    """Response schema for audit log entries."""
    id: UUID
    queue_item_id: Optional[UUID]
    decision_id: Optional[UUID]
    action: str
    description: Optional[str]
    actor_id: str
    actor_type: str
    actor_name: Optional[str]
    context: Optional[Dict[str, Any]]
    timestamp: datetime

    class Config:
        from_attributes = True

class AppealResponse(BaseModel):
    """Response schema for moderation appeals."""
    id: UUID
    decision_id: UUID
    reason: str
    evidence: Optional[str]
    evidence_urls: Optional[List[str]]
    appellant_id: str
    appellant_name: Optional[str]
    appellant_email: Optional[str]
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution: Optional[str]
    resolver_id: Optional[str]
    resolver_name: Optional[str]

    class Config:
        from_attributes = True

class ModerationRuleResponse(BaseModel):
    """Response schema for moderation rules."""
    id: UUID
    name: str
    description: Optional[str]
    rule_type: str
    config: Dict[str, Any]
    is_active: bool
    content_types: Optional[List[str]]
    severity_level: SeverityLevel
    auto_action: Optional[DecisionType]
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    version: int

    class Config:
        from_attributes = True

# Bulk operation schemas

class BulkDecisionRequest(BaseModel):
    """Request schema for bulk moderation decisions."""
    item_ids: List[UUID] = Field(..., min_items=1, max_items=50)
    decision_type: DecisionType
    reason: str = Field(..., min_length=1, max_length=1000)
    notes: Optional[str] = Field(None, max_length=2000)
    moderator_id: str = Field(..., min_length=1)

class BulkDecisionResponse(BaseModel):
    """Response schema for bulk moderation decisions."""
    successful: List[UUID]
    failed: List[Dict[str, Any]]  # [{item_id, error}]
    total_processed: int

# Content submission schema (for external services)

class ContentSubmissionRequest(BaseModel):
    """Request schema for submitting content for moderation."""
    content_id: str = Field(..., min_length=1)
    content_type: ContentType
    content_url: Optional[str] = None
    content_preview: Optional[str] = Field(None, max_length=1000)
    content_metadata: Optional[Dict[str, Any]] = None

    user_id: str = Field(..., min_length=1)
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None

    flag_reason: FlagReason
    flag_details: Optional[str] = Field(None, max_length=2000)
    severity_level: SeverityLevel = SeverityLevel.MEDIUM
    confidence_score: Optional[int] = Field(None, ge=0, le=100)

    flagged_by_system: bool = True
    flagged_by_user_id: Optional[str] = None

# Update QueueItemResponse to resolve forward reference
QueueItemResponse.model_rebuild()
