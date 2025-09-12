"""Model Dispatch Policy Service - Data Models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SubjectType(str, Enum):
    """Subject types supported by the system."""

    MATH = "math"
    ENGLISH = "english"
    SCIENCE = "science"
    ART = "art"
    MUSIC = "music"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    LANGUAGE = "language"


class GradeBand(str, Enum):
    """Grade band classifications."""

    K_2 = "k-2"  # Kindergarten to Grade 2
    GRADE_3_5 = "3-5"  # Grades 3-5
    GRADE_6_8 = "6-8"  # Grades 6-8
    GRADE_9_12 = "9-12"  # Grades 9-12


class Region(str, Enum):
    """Supported regions for data residency."""

    US_EAST = "us-east"
    US_WEST = "us-west"
    EU_WEST = "eu-west"
    EU_CENTRAL = "eu-central"
    ASIA_PACIFIC = "asia-pacific"
    CANADA = "canada"


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure-openai"
    GOOGLE = "google"
    LOCAL = "local"


class PolicyRequest(BaseModel):
    """Request for model dispatch policy."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    subject: SubjectType = Field(..., description="Subject being taught")
    grade_band: GradeBand = Field(..., description="Grade band classification")
    region: Region = Field(..., description="Geographic region for data residency")
    teacher_override: bool = Field(
        default=False, description="Flag indicating teacher manual override"
    )
    request_id: str | None = Field(
        default=None, description="Optional request identifier for tracking"
    )


class PolicyResponse(BaseModel):
    """Response containing dispatch policy."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    provider: LLMProvider = Field(..., description="Selected LLM provider")
    template_ids: list[str] = Field(
        ...,
        description="List of template IDs for the subject/grade combination",
    )
    moderation_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Content moderation threshold (0.0-1.0)",
    )
    provider_config: dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific configuration"
    )
    routing_reason: str = Field(..., description="Explanation for the routing decision")
    cache_ttl_seconds: int = Field(default=3600, description="Cache time-to-live in seconds")
    request_id: str | None = Field(default=None, description="Request identifier for tracking")


class RouteRule(BaseModel):
    """Individual routing rule configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    priority: int = Field(..., description="Rule priority (higher number = higher priority)")
    conditions: dict[str, Any] = Field(..., description="Conditions for rule matching")
    provider: LLMProvider = Field(..., description="Target provider for this rule")
    template_ids: list[str] = Field(..., description="Template IDs for this rule")
    moderation_threshold: float = Field(
        ..., ge=0.0, le=1.0, description="Moderation threshold for this rule"
    )
    provider_config: dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific configuration"
    )
    enabled: bool = Field(default=True, description="Whether this rule is active")
    description: str = Field(..., description="Human-readable rule description")


class PolicyConfig(BaseModel):
    """Complete policy configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    rules: list[RouteRule] = Field(..., description="List of routing rules")
    default_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI, description="Fallback provider"
    )
    default_moderation_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Default moderation threshold"
    )
    cache_enabled: bool = Field(default=True, description="Whether to cache responses")
    cache_ttl_seconds: int = Field(default=3600, description="Default cache TTL")


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: float = Field(..., description="Response timestamp")
    rules_loaded: int = Field(..., description="Number of routing rules loaded")


class PolicyStats(BaseModel):
    """Policy dispatch statistics."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    total_requests: int = Field(..., description="Total policy requests processed")
    cache_hits: int = Field(..., description="Number of cache hits")
    cache_misses: int = Field(..., description="Number of cache misses")
    provider_distribution: dict[str, int] = Field(..., description="Request count by provider")
    region_distribution: dict[str, int] = Field(..., description="Request count by region")
    average_response_time_ms: float = Field(
        ..., description="Average response time in milliseconds"
    )
    rules_count: int = Field(..., description="Number of active routing rules")
    last_updated: datetime = Field(..., description="Last statistics update time")


class TeacherOverride(BaseModel):
    """Teacher override request."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    teacher_id: str = Field(..., description="Teacher identifier")
    subject: SubjectType = Field(..., description="Subject being overridden")
    grade_band: GradeBand = Field(..., description="Grade band for override")
    preferred_provider: LLMProvider = Field(..., description="Teacher's preferred provider")
    reason: str = Field(..., description="Reason for override")
    duration_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Override duration in hours (max 1 week)",
    )
    request_id: str | None = Field(default=None, description="Optional request identifier")


class OverrideResponse(BaseModel):
    """Teacher override response."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    override_id: str = Field(..., description="Unique override identifier")
    expires_at: datetime = Field(..., description="Override expiration time")
    applied: bool = Field(..., description="Whether override was successfully applied")
    message: str = Field(..., description="Response message")
