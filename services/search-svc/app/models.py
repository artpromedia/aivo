"""Pydantic models for search service."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SearchScope(str, Enum):
    """Search scope enumeration."""

    LESSONS = "lessons"
    COURSEWORK = "coursework"
    LEARNERS = "learners"
    ALL = "all"


class UserRole(str, Enum):
    """User role enumeration for RBAC."""

    LEARNER = "learner"
    GUARDIAN = "guardian"
    TEACHER = "teacher"
    DISTRICT_ADMIN = "district_admin"
    SYSTEM_ADMIN = "system_admin"


class SearchRequest(BaseModel):
    """Search request model."""

    q: str = Field(
        ...,
        description="Search query",
        min_length=1,
        max_length=500
    )
    scope: SearchScope = Field(
        default=SearchScope.ALL,
        description="Search scope"
    )
    size: int = Field(
        default=20,
        description="Number of results",
        ge=1,
        le=100
    )
    from_: int = Field(
        default=0,
        description="Offset for pagination",
        ge=0,
        alias="from"
    )
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional filters"
    )


class SuggestionRequest(BaseModel):
    """Suggestion request model."""

    q: str = Field(
        ...,
        description="Query for suggestions",
        min_length=1
    )
    size: int = Field(
        default=5,
        description="Number of suggestions",
        ge=1,
        le=10
    )
    scope: SearchScope = Field(
        default=SearchScope.ALL,
        description="Suggestion scope"
    )


class UserContext(BaseModel):
    """User context for RBAC filtering."""

    user_id: str = Field(
        ...,
        description="User identifier"
    )
    role: UserRole = Field(
        ...,
        description="User role"
    )
    district_id: str | None = Field(
        None,
        description="District identifier"
    )
    school_id: str | None = Field(
        None,
        description="School identifier"
    )
    class_ids: list[str] = Field(
        default_factory=list,
        description="Class identifiers"
    )
    learner_ids: list[str] = Field(
        default_factory=list,
        description="Accessible learner IDs"
    )


class SearchHit(BaseModel):
    """Individual search result."""

    id: str = Field(
        ...,
        description="Document ID"
    )
    type: str = Field(
        ...,
        description="Document type"
    )
    title: str = Field(
        ...,
        description="Document title"
    )
    content: str = Field(
        ...,
        description="Document content snippet"
    )
    score: float = Field(
        ...,
        description="Search relevance score"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    highlighted: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Highlighted snippets"
    )


class SearchResponse(BaseModel):
    """Search response model."""

    hits: list[SearchHit] = Field(
        ...,
        description="Search results"
    )
    total: int = Field(
        ...,
        description="Total number of matches"
    )
    took: int = Field(
        ...,
        description="Query execution time in milliseconds"
    )
    aggregations: dict[str, Any] = Field(
        default_factory=dict,
        description="Search aggregations"
    )


class SuggestionItem(BaseModel):
    """Individual suggestion item."""

    text: str = Field(
        ...,
        description="Suggested text"
    )
    score: float = Field(
        ...,
        description="Suggestion score"
    )
    type: str = Field(
        ...,
        description="Suggestion type"
    )


class SuggestionResponse(BaseModel):
    """Suggestion response model."""

    suggestions: list[SuggestionItem] = Field(
        ...,
        description="Suggestions"
    )
    took: int = Field(..., description="Query execution time in milliseconds")


class IndexDocument(BaseModel):
    """Base document for indexing."""

    id: str = Field(
        ...,
        description="Document ID"
    )
    type: str = Field(
        ...,
        description="Document type"
    )
    title: str = Field(
        ...,
        description="Document title"
    )
    content: str = Field(..., description="Document content")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class LessonDocument(IndexDocument):
    """Lesson document for indexing."""

    type: str = Field(default="lesson", description="Document type")
    subject: str = Field(..., description="Subject area")
    grade_level: int | None = Field(None, description="Grade level")
    district_id: str = Field(..., description="District ID")
    school_id: str | None = Field(None, description="School ID")
    teacher_id: str = Field(..., description="Teacher ID")
    tags: list[str] = Field(default_factory=list, description="Content tags")
    difficulty_level: str | None = Field(None, description="Difficulty level")


class CourseworkDocument(IndexDocument):
    """Coursework document for indexing."""

    type: str = Field(default="coursework", description="Document type")
    assignment_type: str = Field(
        ...,
        description="Assignment type"
    )
    subject: str = Field(
        ...,
        description="Subject area"
    )
    grade_level: int | None = Field(None, description="Grade level")
    district_id: str = Field(..., description="District ID")
    school_id: str | None = Field(None, description="School ID")
    class_id: str = Field(..., description="Class ID")
    teacher_id: str = Field(..., description="Teacher ID")
    due_date: datetime | None = Field(None, description="Due date")
    points_possible: int | None = Field(None, description="Points possible")


class LearnerDocument(IndexDocument):
    """Learner document for indexing (PII-masked)."""

    type: str = Field(default="learner", description="Document type")
    masked_name: str = Field(..., description="PII-masked name")
    grade_level: int | None = Field(None, description="Grade level")
    district_id: str = Field(..., description="District ID")
    school_id: str | None = Field(None, description="School ID")
    class_ids: list[str] = Field(default_factory=list, description="Class IDs")
    teacher_ids: list[str] = Field(
        default_factory=list, description="Teacher IDs"
    )
    guardian_ids: list[str] = Field(
        default_factory=list, description="Guardian IDs"
    )
    performance_level: str | None = Field(
        None, description="Performance level"
    )
    interests: list[str] = Field(
        default_factory=list, description="Learning interests"
    )


class IndexRequest(BaseModel):
    """Request to index a document."""

    index: str = Field(..., description="Index name")
    document: IndexDocument = Field(..., description="Document to index")
    refresh: bool = Field(
        default=False, description="Refresh index after operation"
    )


class BulkIndexRequest(BaseModel):
    """Request to bulk index documents."""

    index: str = Field(..., description="Index name")
    documents: list[IndexDocument] = Field(
        ..., description="Documents to index"
    )
    refresh: bool = Field(
        default=False, description="Refresh index after operation"
    )


class HealthStatus(BaseModel):
    """Service health status."""

    status: str = Field(..., description="Service status")
    opensearch_status: str = Field(
        ..., description="OpenSearch connection status"
    )
    redis_status: str = Field(..., description="Redis connection status")
    indices_status: dict[str, str] = Field(
        default_factory=dict, description="Index health status"
    )
    timestamp: datetime = Field(..., description="Status check timestamp")
