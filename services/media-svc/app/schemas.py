"""Pydantic schemas for Media Service."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class MediaUploadCreate(BaseModel):
    """Schema for creating media upload records."""

    user_id: uuid.UUID
    original_filename: str = Field(..., max_length=255)
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., max_length=100)
    s3_key: str = Field(..., max_length=500)
    s3_bucket: str = Field(..., max_length=100)


class MediaUploadResponse(BaseModel):
    """Schema for media upload responses."""

    id: uuid.UUID
    user_id: uuid.UUID
    original_filename: str
    file_size: int
    mime_type: str
    s3_key: str
    s3_bucket: str
    upload_timestamp: datetime
    processing_status: str
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None
    processing_error: str | None = None
    duration_seconds: float | None = None
    resolution_width: int | None = None
    resolution_height: int | None = None
    frame_rate: float | None = None
    bitrate: int | None = None
    codec: str | None = None

    model_config = {"from_attributes": True}


class HLSQualityConfig(BaseModel):
    """Configuration for HLS quality variants."""

    quality_label: str = Field(..., max_length=20)
    resolution_width: int = Field(..., gt=0)
    resolution_height: int = Field(..., gt=0)
    bitrate: int = Field(..., gt=0)


class HLSTranscodeRequest(BaseModel):
    """Request schema for HLS transcoding."""

    upload_id: uuid.UUID
    quality_variants: list[HLSQualityConfig] = Field(
        default=[
            HLSQualityConfig(
                quality_label="1080p",
                resolution_width=1920,
                resolution_height=1080,
                bitrate=5000000,
            ),
            HLSQualityConfig(
                quality_label="720p",
                resolution_width=1280,
                resolution_height=720,
                bitrate=2500000,
            ),
            HLSQualityConfig(
                quality_label="480p",
                resolution_width=854,
                resolution_height=480,
                bitrate=1000000,
            ),
        ],
    )
    segment_duration: float = Field(default=10.0, gt=0)


class HLSOutputResponse(BaseModel):
    """Schema for HLS output responses."""

    id: uuid.UUID
    upload_id: uuid.UUID
    quality_label: str
    resolution_width: int
    resolution_height: int
    bitrate: int
    master_playlist_s3_key: str
    variant_playlist_s3_key: str
    segment_prefix: str
    segment_count: int
    segment_duration: float
    transcoding_started_at: datetime
    transcoding_completed_at: datetime | None = None
    transcoding_error: str | None = None

    model_config = {"from_attributes": True}


class PresignedUploadRequest(BaseModel):
    """Request schema for presigned upload URLs."""

    filename: str = Field(..., max_length=255)
    content_type: str = Field(..., max_length=100)
    file_size: int = Field(..., gt=0)


class PresignedUploadResponse(BaseModel):
    """Response schema for presigned upload URLs."""

    id: uuid.UUID
    upload_url: str
    s3_key: str
    s3_bucket: str
    expires_at: datetime


class PlaylistWhitelistCreate(BaseModel):
    """Schema for creating playlist whitelist entries."""

    domain: str | None = Field(None, max_length=255)
    ip_address: str | None = Field(None, max_length=45)
    ip_range: str | None = Field(None, max_length=50)
    description: str = Field(..., max_length=255)
    created_by: uuid.UUID


class PlaylistWhitelistResponse(BaseModel):
    """Schema for playlist whitelist responses."""

    id: uuid.UUID
    domain: str | None = None
    ip_address: str | None = None
    ip_range: str | None = None
    description: str
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ZoomLTIConfigCreate(BaseModel):
    """Schema for creating Zoom LTI configuration."""

    organization_id: uuid.UUID
    client_id: str = Field(..., max_length=255)
    deployment_id: str = Field(..., max_length=255)
    issuer: str = Field(..., max_length=255)
    auth_login_url: HttpUrl
    auth_token_url: HttpUrl
    key_set_url: HttpUrl
    zoom_api_key: str = Field(..., max_length=255)
    zoom_api_secret: str = Field(..., max_length=255)
    zoom_webhook_secret: str | None = Field(None, max_length=255)
    zoom_base_url: str = Field(default="https://api.zoom.us/v2", max_length=255)
    created_by: uuid.UUID


class ZoomLTIConfigResponse(BaseModel):
    """Schema for Zoom LTI configuration responses."""

    id: uuid.UUID
    organization_id: uuid.UUID
    client_id: str
    deployment_id: str
    issuer: str
    auth_login_url: str
    auth_token_url: str
    key_set_url: str
    zoom_base_url: str
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LiveSessionCreate(BaseModel):
    """Schema for creating live sessions."""

    lti_config_id: uuid.UUID
    session_name: str = Field(..., max_length=255)
    description: str | None = None
    scheduled_start: datetime
    scheduled_end: datetime
    zoom_host_id: str = Field(..., max_length=100)
    max_participants: int = Field(default=100, gt=0)
    requires_registration: bool = Field(default=False)
    is_recorded: bool = Field(default=True)
    lti_context_id: str | None = Field(None, max_length=255)
    lti_resource_link_id: str | None = Field(None, max_length=255)
    created_by: uuid.UUID


class LiveSessionResponse(BaseModel):
    """Schema for live session responses."""

    id: uuid.UUID
    lti_config_id: uuid.UUID
    session_name: str
    description: str | None = None
    scheduled_start: datetime
    scheduled_end: datetime
    zoom_meeting_id: str
    zoom_meeting_uuid: str | None = None
    zoom_host_id: str
    zoom_join_url: str
    zoom_start_url: str
    zoom_password: str | None = None
    status: str
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    lti_context_id: str | None = None
    lti_resource_link_id: str | None = None
    max_participants: int
    requires_registration: bool
    is_recorded: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AttendanceRecordCreate(BaseModel):
    """Schema for creating attendance records."""

    session_id: uuid.UUID
    user_id: uuid.UUID
    zoom_participant_id: str | None = Field(None, max_length=100)
    participant_name: str = Field(..., max_length=255)
    participant_email: str | None = Field(None, max_length=255)
    joined_at: datetime
    left_at: datetime | None = None
    duration_minutes: int | None = None
    camera_on_duration: int | None = None
    microphone_on_duration: int | None = None
    chat_messages_count: int = Field(default=0)
    screen_share_duration: int | None = None
    average_connection_quality: str | None = Field(None, max_length=20)
    connection_issues_count: int = Field(default=0)
    lti_user_id: str | None = Field(None, max_length=255)
    lti_roles: str | None = Field(None, max_length=500)
    attendance_status: str = Field(default="present", max_length=50)
    recorded_by: str = Field(default="zoom_webhook", max_length=50)


class AttendanceRecordResponse(BaseModel):
    """Schema for attendance record responses."""

    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    zoom_participant_id: str | None = None
    participant_name: str
    participant_email: str | None = None
    joined_at: datetime
    left_at: datetime | None = None
    duration_minutes: int | None = None
    camera_on_duration: int | None = None
    microphone_on_duration: int | None = None
    chat_messages_count: int
    screen_share_duration: int | None = None
    average_connection_quality: str | None = None
    connection_issues_count: int
    lti_user_id: str | None = None
    lti_roles: str | None = None
    attendance_status: str
    recorded_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LTILaunchRequest(BaseModel):
    """Schema for LTI launch requests."""

    iss: str  # Issuer
    aud: str  # Audience (client_id)
    sub: str  # Subject (user identifier)
    exp: int  # Expiration time
    iat: int  # Issued at time
    nonce: str  # Nonce
    deployment_id: str
    target_link_uri: str

    # LTI Claims
    message_type: str = Field(alias="https://purl.imsglobal.org/spec/lti/claim/message_type")
    version: str = Field(alias="https://purl.imsglobal.org/spec/lti/claim/version")
    context: dict | None = Field(None, alias="https://purl.imsglobal.org/spec/lti/claim/context")
    resource_link: dict | None = Field(
        None,
        alias="https://purl.imsglobal.org/spec/lti/claim/resource_link",
    )
    roles: list[str] | None = Field(
        None,
        alias="https://purl.imsglobal.org/spec/lti/claim/roles",
    )

    model_config = {"populate_by_name": True}


class ZoomWebhookEvent(BaseModel):
    """Schema for Zoom webhook events."""

    event: str
    event_ts: int
    payload: dict


class AttendanceStats(BaseModel):
    """Schema for attendance statistics."""

    session_id: uuid.UUID
    total_participants: int
    average_duration_minutes: float
    camera_usage_percentage: float
    microphone_usage_percentage: float
    total_chat_messages: int
    connection_quality_distribution: dict
    attendance_status_distribution: dict


class VideoProcessingStatus(BaseModel):
    """Schema for video processing status."""

    upload_id: uuid.UUID
    status: str
    progress_percentage: float | None = None
    current_stage: str | None = None
    estimated_completion: datetime | None = None
    error_message: str | None = None
    hls_variants_completed: list[str] = Field(default_factory=list)
