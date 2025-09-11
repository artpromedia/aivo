"""Database models for Media Service."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class MediaUpload(Base):
    """Video upload records for processing."""
    
    __tablename__ = "media_uploads"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    s3_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    upload_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Processing status and metadata
    processing_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        index=True,
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Video metadata
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resolution_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolution_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    frame_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    hls_outputs: Mapped[list["HLSOutput"]] = relationship(
        back_populates="upload",
        cascade="all, delete-orphan",
    )


class HLSOutput(Base):
    """HLS transcoding outputs and playlists."""
    
    __tablename__ = "hls_outputs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Quality variant information
    quality_label: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "720p", "480p"
    resolution_width: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_height: Mapped[int] = mapped_column(Integer, nullable=False)
    bitrate: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # HLS files
    master_playlist_s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    variant_playlist_s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    segment_prefix: Mapped[str] = mapped_column(String(500), nullable=False)
    segment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    segment_duration: Mapped[float] = mapped_column(Float, default=10.0)
    
    # Processing metadata
    transcoding_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    transcoding_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    transcoding_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    upload: Mapped["MediaUpload"] = relationship(back_populates="hls_outputs")


class PlaylistWhitelist(Base):
    """Whitelisted domains/IPs for HLS playlist access."""
    
    __tablename__ = "playlist_whitelist"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    ip_range: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # CIDR notation
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ZoomLTIConfig(Base):
    """Zoom LTI integration configuration."""
    
    __tablename__ = "zoom_lti_config"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # LTI 1.3 Configuration
    client_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    deployment_id: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_login_url: Mapped[str] = mapped_column(String(500), nullable=False)
    auth_token_url: Mapped[str] = mapped_column(String(500), nullable=False)
    key_set_url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Zoom-specific configuration
    zoom_api_key: Mapped[str] = mapped_column(String(255), nullable=False)
    zoom_api_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    zoom_webhook_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    zoom_base_url: Mapped[str] = mapped_column(
        String(255),
        default="https://api.zoom.us/v2",
    )
    
    # Configuration metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Relationships
    live_sessions: Mapped[list["LiveSession"]] = relationship(
        back_populates="lti_config",
        cascade="all, delete-orphan",
    )


class LiveSession(Base):
    """Live class sessions with Zoom integration."""
    
    __tablename__ = "live_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    lti_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Session information
    session_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Zoom meeting details
    zoom_meeting_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    zoom_meeting_uuid: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    zoom_host_id: Mapped[str] = mapped_column(String(100), nullable=False)
    zoom_join_url: Mapped[str] = mapped_column(String(500), nullable=False)
    zoom_start_url: Mapped[str] = mapped_column(String(500), nullable=False)
    zoom_password: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Session status
    status: Mapped[str] = mapped_column(
        String(50),
        default="scheduled",
        index=True,
    )  # scheduled, started, ended, cancelled
    actual_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    actual_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # LTI context
    lti_context_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lti_resource_link_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Session metadata
    max_participants: Mapped[int] = mapped_column(Integer, default=100)
    requires_registration: Mapped[bool] = mapped_column(Boolean, default=False)
    is_recorded: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Relationships
    lti_config: Mapped["ZoomLTIConfig"] = relationship(back_populates="live_sessions")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class AttendanceRecord(Base):
    """Student attendance records for live sessions."""
    
    __tablename__ = "attendance_records"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Participant information
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    zoom_participant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    participant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    participant_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Attendance details
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    left_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Participation metrics
    camera_on_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    microphone_on_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chat_messages_count: Mapped[int] = mapped_column(Integer, default=0)
    screen_share_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Connection quality
    average_connection_quality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    connection_issues_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # LTI context
    lti_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lti_roles: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Metadata
    attendance_status: Mapped[str] = mapped_column(
        String(50),
        default="present",
    )  # present, late, left_early, absent
    recorded_by: Mapped[str] = mapped_column(
        String(50),
        default="zoom_webhook",
    )  # zoom_webhook, manual, lti_launch
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Relationships
    session: Mapped["LiveSession"] = relationship(back_populates="attendance_records")


class PresignedUpload(Base):
    """Presigned upload URLs for direct S3 uploads."""
    
    __tablename__ = "presigned_uploads"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Upload details
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    s3_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Presigned URL details
    upload_url: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Upload status
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        index=True,
    )  # pending, uploaded, expired, failed
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
