"""
Pydantic schemas for chat service.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from .models import UserRole, ChatType, MessageStatus, ModerationAction


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)


# Request/Response Models
class ChatSessionCreate(BaseSchema):
    """Create chat session request."""
    chat_type: ChatType
    participants: List[UUID]
    learner_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    parental_controls_enabled: bool = True
    ai_tutor_enabled: bool = True
    moderation_level: str = "strict"


class ChatSessionResponse(BaseSchema):
    """Chat session response."""
    id: UUID
    chat_type: ChatType
    participants: List[UUID]
    learner_id: Optional[UUID]
    parent_id: Optional[UUID]
    teacher_id: Optional[UUID]
    parental_controls_enabled: bool
    ai_tutor_enabled: bool
    moderation_level: str
    created_at: datetime
    updated_at: datetime
    ended_at: Optional[datetime]
    is_active: bool
    auto_archive_days: int


class MessageCreate(BaseSchema):
    """Create message request."""
    session_id: UUID
    sender_id: UUID
    sender_role: UserRole
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: str = "text"


class MessageResponse(BaseSchema):
    """Message response."""
    id: UUID
    session_id: UUID
    sender_id: UUID
    sender_role: UserRole
    original_content: str
    processed_content: Optional[str]
    content_hash: str
    message_type: str
    created_at: datetime
    edited_at: Optional[datetime]
    status: MessageStatus
    moderation_score: Optional[float]
    moderation_action: Optional[ModerationAction]
    contains_pii: bool
    pii_types: Optional[List[str]]


class ModerationResult(BaseSchema):
    """Moderation result."""
    action: ModerationAction
    confidence: float
    reason: Optional[str]
    toxicity_score: Optional[float]
    threat_score: Optional[float]
    profanity_score: Optional[float]
    identity_attack_score: Optional[float]
    processing_time_ms: int


class ParentalControlCreate(BaseSchema):
    """Create parental control request."""
    parent_id: UUID
    learner_id: UUID
    ai_tutor_enabled: bool = True
    ai_tutor_time_limits: Optional[Dict[str, Any]] = None
    content_filter_level: str = "strict"
    allowed_topics: Optional[List[str]] = None
    blocked_topics: Optional[List[str]] = None
    monitor_all_chats: bool = True
    real_time_alerts: bool = True
    daily_summaries: bool = True
    chat_retention_days: int = 365
    auto_delete_enabled: bool = False


class ParentalControlResponse(BaseSchema):
    """Parental control response."""
    id: UUID
    parent_id: UUID
    learner_id: UUID
    ai_tutor_enabled: bool
    ai_tutor_time_limits: Optional[Dict[str, Any]]
    content_filter_level: str
    allowed_topics: Optional[List[str]]
    blocked_topics: Optional[List[str]]
    monitor_all_chats: bool
    real_time_alerts: bool
    daily_summaries: bool
    chat_retention_days: int
    auto_delete_enabled: bool
    created_at: datetime
    updated_at: datetime


class ParentalControlUpdate(BaseSchema):
    """Update parental control request."""
    ai_tutor_enabled: Optional[bool] = None
    ai_tutor_time_limits: Optional[Dict[str, Any]] = None
    content_filter_level: Optional[str] = None
    allowed_topics: Optional[List[str]] = None
    blocked_topics: Optional[List[str]] = None
    monitor_all_chats: Optional[bool] = None
    real_time_alerts: Optional[bool] = None
    daily_summaries: Optional[bool] = None
    chat_retention_days: Optional[int] = None
    auto_delete_enabled: Optional[bool] = None


class AuditEntryResponse(BaseSchema):
    """Audit entry response."""
    id: UUID
    message_id: UUID
    block_hash: str
    previous_hash: Optional[str]
    merkle_root: str
    timestamp: datetime
    data_hash: str
    signature: Optional[str]
    exported_to_s3: bool
    s3_key: Optional[str]
    parquet_exported: bool


class ChatExportRequest(BaseSchema):
    """Chat export request."""
    session_ids: Optional[List[UUID]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    export_format: str = Field(default="parquet", pattern="^(json|parquet|csv)$")
    include_pii: bool = False
    requester_id: UUID
    requester_role: UserRole


class ChatDeleteRequest(BaseSchema):
    """Chat deletion request."""
    session_ids: Optional[List[UUID]] = None
    message_ids: Optional[List[UUID]] = None
    hard_delete: bool = False
    reason: str = Field(..., min_length=10, max_length=500)
    requester_id: UUID
    requester_role: UserRole


class ErrorResponse(BaseSchema):
    """Error response schema."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseSchema):
    """Health check response."""
    status: str
    service: str
    version: str
    database_status: str
    mongodb_status: str
    redis_status: str
    s3_status: str


class WebSocketMessage(BaseSchema):
    """WebSocket message schema."""
    type: str  # "message", "typing", "user_joined", "user_left", "error"
    session_id: UUID
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModerationStats(BaseSchema):
    """Moderation statistics."""
    total_messages: int
    approved_messages: int
    blocked_messages: int
    flagged_messages: int
    average_processing_time_ms: float
    perspective_api_calls: int
    pii_detections: int


class ChatSessionStats(BaseSchema):
    """Chat session statistics."""
    total_sessions: int
    active_sessions: int
    sessions_by_type: Dict[str, int]
    average_session_duration_minutes: float
    messages_per_session: float


class PIIDetectionResult(BaseSchema):
    """PII detection result."""
    contains_pii: bool
    pii_types: List[str]
    confidence: float
    scrubbed_content: Optional[str]
