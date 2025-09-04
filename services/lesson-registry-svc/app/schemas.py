"""Pydantic schemas for lesson registry."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .models import AssetType, GradeBand, LessonState


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)


# Asset schemas
class AssetBase(BaseSchema):
    """Base asset schema."""
    name: str = Field(..., min_length=1, max_length=255)
    asset_type: AssetType
    file_path: str = Field(..., min_length=1, max_length=500)
    file_size: int | None = Field(None, ge=0)
    mime_type: str | None = Field(None, max_length=100)
    alt_text: str | None = Field(None, max_length=500)
    extra_metadata: dict | None = None


class AssetCreate(AssetBase):
    """Asset creation schema."""


class AssetUpdate(BaseSchema):
    """Asset update schema."""
    name: str | None = Field(None, min_length=1, max_length=255)
    alt_text: str | None = Field(None, max_length=500)
    extra_metadata: dict | None = None


class Asset(AssetBase):
    """Asset response schema."""
    id: UUID
    version_id: UUID
    cdn_url: str | None = None
    s3_bucket: str | None = None
    s3_key: str | None = None
    signed_url: str | None = None  # Presigned URL for access
    created_at: datetime
    updated_at: datetime


# Lesson Version schemas
class LessonVersionBase(BaseSchema):
    """Base lesson version schema."""
    content: dict
    summary: str | None = Field(None, max_length=1000)
    learning_objectives: list[str] | None = Field(default_factory=list)
    duration_minutes: int | None = Field(None, ge=1, le=480)  # Max 8 hours


class LessonVersionCreate(LessonVersionBase):
    """Lesson version creation schema."""


class LessonVersionUpdate(BaseSchema):
    """Lesson version update schema."""
    content: dict | None = None
    summary: str | None = Field(None, max_length=1000)
    learning_objectives: list[str] | None = None
    duration_minutes: int | None = Field(None, ge=1, le=480)


class LessonVersion(LessonVersionBase):
    """Lesson version response schema."""
    id: UUID
    lesson_id: UUID
    version_number: int
    state: LessonState
    published_by: UUID | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    assets: list[Asset] = Field(default_factory=list)


# Lesson schemas
class LessonBase(BaseSchema):
    """Base lesson schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    subject: str = Field(..., min_length=1, max_length=100)
    grade_band: GradeBand
    keywords: list[str] | None = Field(default_factory=list)
    extra_metadata: dict | None = None


class LessonCreate(LessonBase):
    """Lesson creation schema."""


class LessonUpdate(BaseSchema):
    """Lesson update schema."""
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    subject: str | None = Field(None, min_length=1, max_length=100)
    grade_band: GradeBand | None = None
    keywords: list[str] | None = None
    extra_metadata: dict | None = None


class Lesson(LessonBase):
    """Lesson response schema."""
    id: UUID
    created_by: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    versions: list[LessonVersion] = Field(default_factory=list)

    # Computed fields
    latest_version: LessonVersion | None = None
    published_version: LessonVersion | None = None


# Search schemas
class SearchFilters(BaseSchema):
    """Search filters."""
    subject: str | None = Field(None, max_length=100)
    grade_band: GradeBand | None = None
    keywords: list[str] | None = Field(default_factory=list)
    state: LessonState | None = None
    created_by: UUID | None = None


class SearchParams(BaseSchema):
    """Search parameters."""
    q: str | None = Field(
        None, min_length=1, max_length=200, description="Search query"
    )
    filters: SearchFilters | None = Field(default_factory=SearchFilters)
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str | None = Field("created_at", description="Sort field")
    sort_order: str = Field(
        "desc", pattern="^(asc|desc)$", description="Sort order"
    )


class SearchResults(BaseSchema):
    """Search results."""
    lessons: list[Lesson]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# Publish schemas
class PublishRequest(BaseSchema):
    """Publish lesson version request."""
    version_id: UUID


class PublishResponse(BaseSchema):
    """Publish lesson version response."""
    success: bool
    message: str
    version: LessonVersion


# Health check schema
class HealthCheck(BaseSchema):
    """Health check response."""
    status: str = "ok"
    timestamp: datetime
    version: str
    database: bool = True
    storage: bool = True
