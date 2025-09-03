"""
Pydantic schemas for the Approval Service API.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator

from .enums import (
    ApprovalStatus, ParticipantRole, DecisionType, 
    ApprovalType, Priority, NotificationChannel, WebhookEventType
)


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    class Config:
        from_attributes = True
        use_enum_values = True


# Participant schemas
class ParticipantInput(BaseSchema):
    """Input schema for approval participants."""
    user_id: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    role: ParticipantRole
    display_name: str = Field(..., min_length=1, max_length=200)
    is_required: bool = True
    metadata: Optional[Dict[str, Any]] = None


class ParticipantResponse(BaseSchema):
    """Response schema for approval participants."""
    id: UUID
    user_id: str
    email: str
    role: ParticipantRole
    display_name: str
    is_required: bool
    has_responded: bool
    has_approved: bool
    has_rejected: bool
    notified_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]


# Decision schemas
class DecisionInput(BaseSchema):
    """Input schema for approval decisions."""
    decision_type: DecisionType
    comments: Optional[str] = Field(None, max_length=2000)
    metadata: Optional[Dict[str, Any]] = None


class DecisionResponse(BaseSchema):
    """Response schema for approval decisions."""
    id: UUID
    participant_id: UUID
    decision_type: DecisionType
    comments: Optional[str]
    created_at: datetime
    metadata: Optional[Dict[str, Any]]


# Approval schemas
class ApprovalCreateInput(BaseSchema):
    """Input schema for creating approval requests."""
    tenant_id: str = Field(..., min_length=1, max_length=100)
    approval_type: ApprovalType
    priority: Priority = Priority.NORMAL
    
    # Resource information
    resource_type: str = Field(..., min_length=1, max_length=100)
    resource_id: str = Field(..., min_length=1, max_length=200)
    resource_data: Optional[Dict[str, Any]] = None
    
    # Approval details
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    created_by: str = Field(..., min_length=1, max_length=200)
    
    # Timing
    ttl_hours: Optional[int] = Field(None, ge=1, le=720)  # 1 hour to 30 days
    
    # Participants
    participants: List[ParticipantInput] = Field(..., min_length=1, max_length=10)
    required_participants: Optional[int] = None
    require_all_participants: bool = True
    
    # Webhook configuration
    webhook_url: Optional[str] = Field(None, max_length=1000)
    webhook_events: Optional[List[WebhookEventType]] = None
    callback_data: Optional[Dict[str, Any]] = None
    
    @field_validator('participants')
    @classmethod
    def validate_participants(cls, v):
        """Validate participants list."""
        if not v:
            raise ValueError("At least one participant is required")
        
        # Check for duplicate user_ids
        user_ids = [p.user_id for p in v]
        if len(user_ids) != len(set(user_ids)):
            raise ValueError("Duplicate user_ids are not allowed")
        
        # Check role requirements - must have at least one guardian and one staff
        roles = [p.role for p in v]
        has_guardian = any(role == ParticipantRole.GUARDIAN for role in roles)
        staff_roles = [
            ParticipantRole.TEACHER, 
            ParticipantRole.ADMINISTRATOR,
            ParticipantRole.SPECIAL_EDUCATION_COORDINATOR,
            ParticipantRole.PRINCIPAL
        ]
        has_staff = any(role in staff_roles for role in roles)
        
        if not has_guardian or not has_staff:
            raise ValueError("Must have at least one guardian and one staff member")
        
        return v
    
    @model_validator(mode='after')
    def validate_required_participants(self):
        """Validate required participants count."""
        if self.required_participants is not None and self.participants:
            participants_count = len(self.participants)
            if self.required_participants > participants_count:
                raise ValueError("Required participants cannot exceed total participants")
            if self.required_participants < 1:
                raise ValueError("Required participants must be at least 1")
        return self


class ApprovalResponse(BaseSchema):
    """Response schema for approval requests."""
    id: UUID
    tenant_id: str
    
    # Approval metadata
    approval_type: ApprovalType
    status: ApprovalStatus
    priority: Priority
    
    # Resource information
    resource_type: str
    resource_id: str
    resource_data: Optional[Dict[str, Any]]
    
    # Approval details
    title: str
    description: Optional[str]
    created_by: str
    
    # Timing
    created_at: datetime
    expires_at: datetime
    completed_at: Optional[datetime]
    
    # Workflow configuration
    required_participants: int
    require_all_participants: bool
    
    # External integration
    webhook_url: Optional[str]
    webhook_events: Optional[List[str]]
    callback_data: Optional[Dict[str, Any]]
    
    # Progress information
    approval_progress: Dict[str, Any]
    is_expired: bool
    
    # Related data
    participants: List[ParticipantResponse]
    decisions: List[DecisionResponse]


class ApprovalSummary(BaseSchema):
    """Summary schema for approval lists."""
    id: UUID
    tenant_id: str
    approval_type: ApprovalType
    status: ApprovalStatus
    priority: Priority
    resource_type: str
    resource_id: str
    title: str
    created_by: str
    created_at: datetime
    expires_at: datetime
    completed_at: Optional[datetime]
    approval_progress: Dict[str, Any]
    is_expired: bool


# Query schemas
class ApprovalListQuery(BaseSchema):
    """Query parameters for listing approvals."""
    tenant_id: Optional[str] = None
    status: Optional[ApprovalStatus] = None
    approval_type: Optional[ApprovalType] = None
    priority: Optional[Priority] = None
    resource_type: Optional[str] = None
    created_by: Optional[str] = None
    participant_user_id: Optional[str] = None
    expires_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    created_after: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    order_by: str = Field(default="created_at")
    order_desc: bool = Field(default=True)


# Response schemas
class ApprovalListResponse(BaseSchema):
    """Response schema for approval lists."""
    items: List[ApprovalSummary]
    total: int
    limit: int
    offset: int
    has_more: bool


class DecisionResult(BaseSchema):
    """Result of making a decision."""
    success: bool
    message: str
    approval_status: ApprovalStatus
    decision_id: UUID
    approval_completed: bool
    errors: Optional[List[str]] = None


class ApprovalCreationResult(BaseSchema):
    """Result of creating an approval."""
    success: bool
    message: str
    approval_id: Optional[UUID] = None
    errors: Optional[List[str]] = None


# Webhook schemas
class WebhookPayload(BaseSchema):
    """Webhook payload schema."""
    event_type: WebhookEventType
    timestamp: datetime
    approval_id: UUID
    tenant_id: str
    data: Dict[str, Any]
    callback_data: Optional[Dict[str, Any]] = None


# Health check schema
class HealthResponse(BaseSchema):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]
