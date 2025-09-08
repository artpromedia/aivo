"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .enums import ModerationResult


class PIIEntity(BaseModel):
    """PII entity detected in text."""

    entity_type: str = Field(..., description="Type of PII entity")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    score: float = Field(..., description="Confidence score")
    text: str = Field(..., description="Original text")


class ContentContext(BaseModel):
    """Educational context for content envelope."""

    subject: str | None = Field(None, description="Academic subject")
    grade_level: str | None = Field(None, description="Grade level")
    learning_objective: str | None = Field(None, description="Learning objective")
    content_type: str | None = Field(None, description="Type of content")


class GenerateRequest(BaseModel):
    """Request schema for text generation."""

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(..., description="Input prompt for generation")
    model: str | None = Field(None, description="Model to use for generation")
    max_tokens: int | None = Field(None, description="Maximum tokens to generate")
    temperature: float | None = Field(0.7, description="Sampling temperature", ge=0.0, le=2.0)
    top_p: float | None = Field(1.0, description="Top-p sampling", ge=0.0, le=1.0)
    frequency_penalty: float | None = Field(0.0, description="Frequency penalty", ge=-2.0, le=2.0)
    presence_penalty: float | None = Field(0.0, description="Presence penalty", ge=-2.0, le=2.0)
    stop: str | list[str] | None = Field(None, description="Stop sequences")

    # Educational context
    context: ContentContext | None = Field(None, description="Educational context")

    # Control flags
    skip_moderation: bool = Field(False, description="Skip content moderation")
    skip_pii_scrubbing: bool = Field(False, description="Skip PII scrubbing")


class EmbeddingRequest(BaseModel):
    """Request schema for text embeddings."""

    model_config = ConfigDict(extra="forbid")

    input: str | list[str] = Field(..., description="Text to embed")
    model: str | None = Field(None, description="Embedding model to use")

    # Educational context
    context: ContentContext | None = Field(None, description="Educational context")

    # Control flags
    skip_pii_scrubbing: bool = Field(False, description="Skip PII scrubbing")


class ModerationRequest(BaseModel):
    """Request schema for content moderation."""

    model_config = ConfigDict(extra="forbid")

    input: str | list[str] = Field(..., description="Content to moderate")
    model: str | None = Field(None, description="Moderation model to use")
    threshold: float | None = Field(None, description="Custom threshold", ge=0.0, le=1.0)


class GenerationChoice(BaseModel):
    """Single generation choice."""

    index: int = Field(..., description="Choice index")
    text: str = Field(..., description="Generated text")
    finish_reason: str = Field(..., description="Reason for completion")
    logprobs: dict[str, Any] | None = Field(None, description="Log probabilities")


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(..., description="Tokens in prompt")
    completion_tokens: int | None = Field(None, description="Tokens in completion")
    total_tokens: int = Field(..., description="Total tokens used")


class GenerateResponse(BaseModel):
    """Response schema for text generation."""

    id: str = Field(..., description="Response ID")
    object: str = Field("text_completion", description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: list[GenerationChoice] = Field(..., description="Generated choices")
    usage: Usage = Field(..., description="Token usage")

    # Moderation information
    moderation_result: ModerationResult = Field(..., description="Moderation status")
    moderation_scores: dict[str, float] | None = Field(None, description="Moderation scores")

    # PII information
    pii_detected: bool = Field(False, description="Whether PII was detected")
    pii_entities: list[PIIEntity] = Field(default_factory=list, description="Detected PII entities")
    pii_scrubbed: bool = Field(False, description="Whether PII was scrubbed")

    # Educational context
    context: ContentContext | None = Field(None, description="Educational context")


class EmbeddingData(BaseModel):
    """Single embedding result."""

    object: str = Field("embedding", description="Object type")
    index: int = Field(..., description="Input index")
    embedding: list[float] = Field(..., description="Embedding vector")


class EmbeddingResponse(BaseModel):
    """Response schema for embeddings."""

    object: str = Field("list", description="Object type")
    data: list[EmbeddingData] = Field(..., description="Embedding data")
    model: str = Field(..., description="Model used")
    usage: Usage = Field(..., description="Token usage")

    # PII information
    pii_detected: bool = Field(False, description="Whether PII was detected")
    pii_entities: list[PIIEntity] = Field(default_factory=list, description="Detected PII entities")
    pii_scrubbed: bool = Field(False, description="Whether PII was scrubbed")

    # Educational context
    context: ContentContext | None = Field(None, description="Educational context")


class ModerationCategory(BaseModel):
    """Moderation category result."""

    flagged: bool = Field(..., description="Whether category was flagged")
    score: float = Field(..., description="Category score")


class ModerationResult(BaseModel):
    """Moderation result for single input."""

    flagged: bool = Field(..., description="Whether content was flagged")
    categories: dict[str, bool] = Field(..., description="Category flags")
    category_scores: dict[str, float] = Field(..., description="Category scores")


class ModerationResponse(BaseModel):
    """Response schema for moderation."""

    id: str = Field(..., description="Response ID")
    model: str = Field(..., description="Model used")
    results: list[ModerationResult] = Field(..., description="Moderation results")


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Current timestamp")
    dependencies: dict[str, str] = Field(..., description="Dependency status")
