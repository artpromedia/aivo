"""Pydantic schemas for Edge Bundler Service."""
# flake8: noqa: E501

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models import BundleStatus, CompressionType  # pylint: disable=import-error


class BundleRequest(BaseModel):
    """Schema for bundle creation request."""

    learner_id: UUID = Field(..., description="Learner UUID")
    subjects: list[str] = Field(
        ..., min_items=1, max_items=10, description="Subject list"
    )
    bundle_name: str | None = Field(
        None, max_length=255, description="Optional bundle name"
    )
    max_bundle_size: int = Field(
        52428800, ge=1048576, le=104857600, description="Max bundle size (1MB-100MB)"
    )
    max_precache_size: int = Field(
        26214400, ge=524288, le=52428800, description="Max precache size (512KB-50MB)"
    )
    compression_type: CompressionType = Field(
        CompressionType.GZIP, description="Compression algorithm"
    )
    bundle_version: str = Field(
        "1.0.0", pattern=r"^\d+\.\d+\.\d+$", description="Semantic version"
    )
    include_adapters: bool = Field(True, description="Include lesson adapters")
    precache_priority: list[str] = Field(
        default_factory=list, description="High-priority content for precaching"
    )
    offline_duration_hours: int = Field(
        168, ge=1, le=720, description="Offline availability (1h-30d)"
    )

    @validator("max_precache_size")
    @classmethod
    def validate_precache_size(
        cls: type["BundleRequest"], v: int, values: dict
    ) -> int:
        """Ensure precache size doesn't exceed bundle size."""
        if "max_bundle_size" in values and v > values["max_bundle_size"]:
            raise ValueError("Precache size cannot exceed bundle size")
        return v


class CRDTConfig(BaseModel):
    """CRDT configuration for offline synchronization."""

    enable_crdt: bool = Field(True, description="Enable CRDT offline queue")
    vector_clock_node_id: str = Field(..., description="Unique node identifier")
    merge_strategy: str = Field(
        "last_writer_wins", pattern="^(last_writer_wins|merge_conflicts|custom)$"
    )
    conflict_resolution_hooks: list[str] = Field(
        default_factory=list, description="Custom conflict resolution hooks"
    )
    sync_granularity: str = Field(
        "lesson", pattern="^(lesson|section|paragraph)$", description="Sync granularity level"
    )
    offline_queue_max_size: int = Field(
        1000, ge=10, le=10000, description="Max offline operations to queue"
    )


class BundleAssetInfo(BaseModel):
    """Schema for bundle asset information."""

    asset_type: str = Field(..., description="Asset type (lesson, adapter, media)")
    asset_name: str = Field(..., description="Asset name")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    mime_type: str | None = Field(None, description="MIME type")
    content_id: str | None = Field(None, description="Content identifier")
    subject: str | None = Field(None, description="Subject classification")
    is_precache: bool = Field(False, description="Include in precache")
    priority: int = Field(100, ge=1, le=1000, description="Priority (lower = higher)")


class BundleResponse(BaseModel):
    """Schema for bundle creation response."""

    bundle_id: UUID
    learner_id: UUID
    subjects: list[str]
    bundle_name: str
    status: BundleStatus
    max_bundle_size: int
    max_precache_size: int
    actual_size: int | None = None
    precache_size: int | None = None
    compression_type: CompressionType
    bundle_version: str
    bundle_path: str | None = None
    sha256_hash: str | None = None
    is_signed: bool
    lesson_count: int
    asset_count: int
    adapter_count: int
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None
    error_message: str | None = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class BundleListResponse(BaseModel):
    """Schema for bundle list response."""

    bundles: list[BundleResponse]
    total: int
    page: int
    size: int
    pages: int


class BundleManifest(BaseModel):
    """Schema for bundle manifest file."""

    bundle_id: UUID
    version: str
    created_at: datetime
    expires_at: datetime | None
    learner_id: UUID
    subjects: list[str]
    compression_type: CompressionType
    total_size: int
    precache_size: int
    assets: list[BundleAssetInfo]
    crdt_config: CRDTConfig | None = None
    signature: str | None = None
    checksum: str


class DownloadRequest(BaseModel):
    """Schema for bundle download request."""

    bundle_id: UUID
    learner_id: UUID
    client_version: str | None = Field(None, description="Client app version")
    include_manifest: bool = Field(True, description="Include manifest in response")


class DownloadResponse(BaseModel):
    """Schema for bundle download response."""

    bundle_id: UUID
    download_url: str
    manifest_url: str | None = None
    size: int
    sha256_hash: str
    expires_at: datetime
    download_id: UUID

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class CRDTOperation(BaseModel):
    """Schema for CRDT operation."""

    operation_id: UUID
    operation_type: str = Field(..., pattern="^(create|update|delete|merge)$")
    content_type: str = Field(..., description="Type of content being operated on")
    content_id: str = Field(..., description="Unique content identifier")
    vector_clock: dict[str, int] = Field(..., description="Vector clock for operation ordering")
    operation_data: dict = Field(..., description="Operation payload")
    timestamp: datetime = Field(..., description="Operation timestamp")


class CRDTMergeRequest(BaseModel):
    """Schema for CRDT merge request from offline client."""

    bundle_id: UUID
    learner_id: UUID
    operations: list[CRDTOperation] = Field(..., min_items=1, max_items=100)
    client_vector_clock: dict[str, int] = Field(..., description="Client's current vector clock")


class CRDTMergeResponse(BaseModel):
    """Schema for CRDT merge response."""

    accepted_operations: list[UUID]
    conflicted_operations: list[UUID]
    server_operations: list[CRDTOperation]
    updated_vector_clock: dict[str, int]
    conflicts_resolved: int


class BundleProgressUpdate(BaseModel):
    """Schema for bundle creation progress updates."""

    bundle_id: UUID
    status: BundleStatus
    progress_percentage: int = Field(..., ge=0, le=100)
    current_step: str
    estimated_completion: datetime | None = None
    error_message: str | None = None
    size_info: dict[str, int] | None = None  # current_size, precache_size, etc.


class BundleStatsResponse(BaseModel):
    """Schema for bundle statistics."""

    total_bundles: int
    active_bundles: int
    total_size_bytes: int
    average_size_bytes: int
    download_count: int
    most_popular_subjects: list[dict[str, int]]
    crdt_operations_count: int
    conflict_resolution_count: int


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str
    message: str
    details: dict | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str
    timestamp: datetime
    version: str
    dependencies: dict[str, str]
    metrics: dict[str, int | float] = Field(default_factory=dict)
