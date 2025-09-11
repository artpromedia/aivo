"""
Database models for model dispatch policy.

Handles LLM provider selection based on subject, grade band, and region.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class GradeBand(str, Enum):
    """Educational grade bands."""

    EARLY_CHILDHOOD = "early_childhood"  # Pre-K to K
    ELEMENTARY = "elementary"  # Grades 1-5
    MIDDLE = "middle"  # Grades 6-8
    HIGH = "high"  # Grades 9-12
    ADULT = "adult"  # Adult education
    SPECIAL = "special"  # Special needs


class Subject(str, Enum):
    """Academic subjects."""

    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    LANGUAGE_ARTS = "language_arts"
    SOCIAL_STUDIES = "social_studies"
    ART = "art"
    MUSIC = "music"
    PHYSICAL_EDUCATION = "physical_education"
    TECHNOLOGY = "technology"
    FOREIGN_LANGUAGE = "foreign_language"
    CAREER_TECHNICAL = "career_technical"
    SPECIAL_EDUCATION = "special_education"
    GENERAL = "general"


class Region(str, Enum):
    """Geographic regions for data residency."""

    US_EAST = "us_east"
    US_WEST = "us_west"
    US_CENTRAL = "us_central"
    CANADA = "canada"
    EU_WEST = "eu_west"
    EU_CENTRAL = "eu_central"
    UK = "uk"
    APAC_SINGAPORE = "apac_singapore"
    APAC_TOKYO = "apac_tokyo"
    APAC_SYDNEY = "apac_sydney"
    AFRICA_SOUTH = "africa_south"
    LATAM_BRAZIL = "latam_brazil"
    MIDDLE_EAST = "middle_east"


class ProviderType(str, Enum):
    """LLM provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    AWS_BEDROCK = "aws_bedrock"
    HUGGING_FACE = "hugging_face"
    LOCAL = "local"
    CUSTOM = "custom"


class ModelProvider(Base):
    """LLM provider configuration."""

    __tablename__ = "model_providers"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    provider_type: Mapped[ProviderType] = mapped_column(nullable=False)
    endpoint_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key_env: Mapped[Optional[str]] = mapped_column(String(100))
    supported_regions: Mapped[List[str]] = mapped_column(JSON, default=list)
    model_configs: Mapped[Dict] = mapped_column(JSON, default=dict)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, default=60)
    rate_limit_tpm: Mapped[int] = mapped_column(Integer, default=100000)
    cost_per_1k_input: Mapped[float] = mapped_column(Float, default=0.0)
    cost_per_1k_output: Mapped[float] = mapped_column(Float, default=0.0)
    latency_p95_ms: Mapped[int] = mapped_column(Integer, default=1000)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.99)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class PromptTemplate(Base):
    """Prompt templates for different subjects and grades."""

    __tablename__ = "prompt_templates"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[Subject] = mapped_column(nullable=False)
    grade_band: Mapped[GradeBand] = mapped_column(nullable=False)
    template_content: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    variables: Mapped[List[str]] = mapped_column(JSON, default=list)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1000)
    stop_sequences: Mapped[List[str]] = mapped_column(JSON, default=list)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class DispatchPolicy(Base):
    """Policy rules for model selection based on subject/grade/region."""

    __tablename__ = "dispatch_policies"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[Optional[Subject]] = mapped_column()  # None = applies to all
    grade_band: Mapped[Optional[GradeBand]] = mapped_column()  # None = applies to all
    region: Mapped[Optional[Region]] = mapped_column()  # None = applies to all
    primary_provider_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    fallback_provider_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    template_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    moderation_threshold: Mapped[float] = mapped_column(Float, default=0.8)
    allow_teacher_override: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)  # Lower = higher priority
    conditions: Mapped[Dict] = mapped_column(JSON, default=dict)  # Additional conditions
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class RegionalRouting(Base):
    """Regional routing rules for data residency compliance."""

    __tablename__ = "regional_routing"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    region: Mapped[Region] = mapped_column(nullable=False, unique=True)
    allowed_providers: Mapped[List[str]] = mapped_column(JSON, default=list)
    blocked_providers: Mapped[List[str]] = mapped_column(JSON, default=list)
    data_residency_required: Mapped[bool] = mapped_column(Boolean, default=True)
    encryption_required: Mapped[bool] = mapped_column(Boolean, default=True)
    audit_logging_required: Mapped[bool] = mapped_column(Boolean, default=True)
    retention_days: Mapped[int] = mapped_column(Integer, default=90)
    compliance_frameworks: Mapped[List[str]] = mapped_column(JSON, default=list)
    backup_region: Mapped[Optional[Region]] = mapped_column()
    routing_preferences: Mapped[Dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class DispatchLog(Base):
    """Log of model dispatch decisions."""

    __tablename__ = "dispatch_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject: Mapped[Subject] = mapped_column(nullable=False)
    grade_band: Mapped[GradeBand] = mapped_column(nullable=False)
    region: Mapped[Region] = mapped_column(nullable=False)
    selected_provider_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    template_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    moderation_threshold: Mapped[float] = mapped_column(Float)
    policy_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    teacher_override: Mapped[bool] = mapped_column(Boolean, default=False)
    override_reason: Mapped[Optional[str]] = mapped_column(String(500))
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ModelMetrics(Base):
    """Performance metrics for model providers."""

    __tablename__ = "model_metrics"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    subject: Mapped[Subject] = mapped_column(nullable=False)
    grade_band: Mapped[GradeBand] = mapped_column(nullable=False)
    region: Mapped[Region] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_response_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    p95_response_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
