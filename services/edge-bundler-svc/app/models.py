"""Edge Bundler Service for offline lesson packaging with CRDT support."""
# flake8: noqa: E501
# pylint: disable=too-few-public-methods

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""


class BundleStatus(str, Enum):
    """Bundle creation status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class CompressionType(str, Enum):
    """Bundle compression type."""

    GZIP = "gzip"
    BROTLI = "brotli"
    ZSTD = "zstd"


class Bundle(Base):
    """Bundle model for offline lesson packages."""

    __tablename__ = "bundles"

    bundle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True
    )
    learner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    subjects: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    bundle_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Size constraints (in bytes)
    max_bundle_size: Mapped[int] = mapped_column(Integer, default=52428800)  # 50MB
    max_precache_size: Mapped[int] = mapped_column(Integer, default=26214400)  # 25MB
    actual_size: Mapped[int] = mapped_column(Integer, nullable=True)
    precache_size: Mapped[int] = mapped_column(Integer, nullable=True)

    # Bundle metadata
    status: Mapped[BundleStatus] = mapped_column(
        String(20), default=BundleStatus.PENDING, index=True
    )
    compression_type: Mapped[CompressionType] = mapped_column(
        String(10), default=CompressionType.GZIP
    )
    bundle_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")

    # File paths and checksums
    bundle_path: Mapped[str] = mapped_column(String(500), nullable=True)
    manifest_path: Mapped[str] = mapped_column(String(500), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=True, index=True)

    # CRDT metadata
    crdt_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    offline_queue_config: Mapped[dict] = mapped_column(JSON, nullable=True)
    merge_hooks: Mapped[list[dict]] = mapped_column(JSON, default=list)

    # Signing and security
    is_signed: Mapped[bool] = mapped_column(Boolean, default=False)
    signature_path: Mapped[str] = mapped_column(String(500), nullable=True)
    signing_key_id: Mapped[str] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, index=True)

    # Processing metadata
    processing_started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    processing_completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Content metadata
    lesson_count: Mapped[int] = mapped_column(Integer, default=0)
    asset_count: Mapped[int] = mapped_column(Integer, default=0)
    adapter_count: Mapped[int] = mapped_column(Integer, default=0)


class BundleAsset(Base):
    """Individual assets within a bundle."""

    __tablename__ = "bundle_assets"

    asset_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bundle_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Asset metadata
    asset_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # lesson, adapter, media
    asset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)

    # Content identification
    content_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=True, index=True)

    # CRDT specific metadata
    crdt_version: Mapped[str] = mapped_column(String(50), nullable=True)
    last_modified: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=True)

    # Precache priority
    is_precache: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)  # Lower = higher priority

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class BundleDownload(Base):
    """Track bundle downloads and usage analytics."""

    __tablename__ = "bundle_downloads"

    download_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bundle_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    learner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Download metadata
    download_started_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), index=True
    )
    download_completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    download_size: Mapped[int] = mapped_column(Integer, nullable=True)

    # Client information
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    client_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    client_version: Mapped[str] = mapped_column(String(50), nullable=True)

    # Status tracking
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)


class CRDTMergeLog(Base):
    """Track CRDT merge operations for debugging and audit purposes."""

    __tablename__ = "crdt_merge_logs"

    merge_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bundle_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Merge operation details
    merge_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), index=True
    )
    source_version: Mapped[str] = mapped_column(String(100), nullable=False)
    target_version: Mapped[str] = mapped_column(String(100), nullable=False)
    resulting_version: Mapped[str] = mapped_column(String(100), nullable=False)

    # Merge metadata
    merge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    conflicts_count: Mapped[int] = mapped_column(Integer, default=0)
    resolution_strategy: Mapped[str] = mapped_column(String(100), nullable=True)

    # Performance metrics
    merge_duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    affected_assets_count: Mapped[int] = mapped_column(Integer, default=0)

    # Audit information
    initiated_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    merge_context: Mapped[dict] = mapped_column(JSON, nullable=True)
