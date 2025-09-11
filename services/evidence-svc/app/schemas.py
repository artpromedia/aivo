"""Pydantic schemas for Evidence Service."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class EvidenceUploadBase(BaseModel):
    """Base schema for evidence uploads."""

    learner_id: uuid.UUID
    original_filename: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=50)
    mime_type: str = Field(..., max_length=100)


class EvidenceUploadCreate(EvidenceUploadBase):
    """Schema for creating evidence uploads."""

    file_size: int = Field(..., gt=0)
    s3_key: str = Field(..., max_length=500)
    s3_bucket: str = Field(..., max_length=100)
    content_hash: str = Field(..., min_length=64, max_length=64)
    metadata: Optional[Dict[str, Any]] = None


class EvidenceUploadUpdate(BaseModel):
    """Schema for updating evidence uploads."""

    processing_status: Optional[str] = Field(None, max_length=50)
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class EvidenceUploadResponse(EvidenceUploadBase):
    """Schema for evidence upload responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_size: int
    s3_key: str
    s3_bucket: str
    upload_timestamp: datetime
    content_hash: str
    processing_status: str
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class EvidenceExtractionBase(BaseModel):
    """Base schema for evidence extractions."""

    upload_id: uuid.UUID
    extraction_type: str = Field(..., max_length=50)
    extractor_version: str = Field(..., max_length=50)


class EvidenceExtractionCreate(EvidenceExtractionBase):
    """Schema for creating evidence extractions."""

    extracted_text: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    subject_tags: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    extraction_metadata: Optional[Dict[str, Any]] = None


class EvidenceExtractionResponse(EvidenceExtractionBase):
    """Schema for evidence extraction responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    extracted_text: Optional[str] = None
    keywords: List[str]
    subject_tags: List[str]
    confidence_score: Optional[float] = None
    extraction_metadata: Optional[Dict[str, Any]] = None
    extracted_at: datetime


class IEPGoalBase(BaseModel):
    """Base schema for IEP goals."""

    learner_id: uuid.UUID
    goal_text: str
    subject_area: str = Field(..., max_length=100)
    category: str = Field(..., max_length=100)


class IEPGoalCreate(IEPGoalBase):
    """Schema for creating IEP goals."""

    target_date: Optional[datetime] = None
    keywords: List[str] = Field(default_factory=list)


class IEPGoalUpdate(BaseModel):
    """Schema for updating IEP goals."""

    goal_text: Optional[str] = None
    subject_area: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    target_date: Optional[datetime] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None


class IEPGoalResponse(IEPGoalBase):
    """Schema for IEP goal responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_date: Optional[datetime] = None
    keywords: List[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool


class IEPGoalLinkageBase(BaseModel):
    """Base schema for IEP goal linkages."""

    extraction_id: uuid.UUID
    iep_goal_id: uuid.UUID
    linkage_strength: float = Field(..., ge=0.0, le=1.0)
    linkage_reason: str


class IEPGoalLinkageCreate(IEPGoalLinkageBase):
    """Schema for creating IEP goal linkages."""

    matching_keywords: List[str] = Field(default_factory=list)


class IEPGoalLinkageUpdate(BaseModel):
    """Schema for updating IEP goal linkages."""

    validated_by_teacher: Optional[bool] = None
    teacher_notes: Optional[str] = None


class IEPGoalLinkageResponse(IEPGoalLinkageBase):
    """Schema for IEP goal linkage responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    matching_keywords: List[str]
    created_at: datetime
    validated_by_teacher: Optional[bool] = None
    teacher_notes: Optional[str] = None


class EvidenceAuditEntryBase(BaseModel):
    """Base schema for evidence audit entries."""

    upload_id: uuid.UUID
    learner_id: uuid.UUID
    action_type: str = Field(..., max_length=50)
    action_details: Dict[str, Any]
    performed_by: uuid.UUID


class EvidenceAuditEntryCreate(EvidenceAuditEntryBase):
    """Schema for creating evidence audit entries."""

    content_hash: str = Field(..., min_length=64, max_length=64)
    previous_hash: Optional[str] = Field(None, min_length=64, max_length=64)
    signature: Optional[str] = None


class EvidenceAuditEntryResponse(EvidenceAuditEntryBase):
    """Schema for evidence audit entry responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    timestamp: datetime
    content_hash: str
    previous_hash: Optional[str] = None
    chain_hash: str
    signature: Optional[str] = None


class SubjectKeywordMapBase(BaseModel):
    """Base schema for subject keyword mappings."""

    subject_area: str = Field(..., max_length=100)
    keyword: str = Field(..., max_length=200)


class SubjectKeywordMapCreate(SubjectKeywordMapBase):
    """Schema for creating subject keyword mappings."""

    weight: float = Field(default=1.0, ge=0.1, le=10.0)


class SubjectKeywordMapUpdate(BaseModel):
    """Schema for updating subject keyword mappings."""

    weight: Optional[float] = Field(None, ge=0.1, le=10.0)
    is_active: Optional[bool] = None


class SubjectKeywordMapResponse(SubjectKeywordMapBase):
    """Schema for subject keyword mapping responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    weight: float
    created_at: datetime
    is_active: bool


# Extraction Processing Schemas
class TextractConfig(BaseModel):
    """Configuration for AWS Textract processing."""

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
    )

    detect_text: bool = True
    analyze_document: bool = True
    feature_types: List[str] = Field(
        default_factory=lambda: [
            "TABLES",
            "FORMS",
            "SIGNATURES",
        ],
    )
    max_pages: int = Field(default=50, ge=1, le=100)
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class WhisperConfig(BaseModel):
    """Configuration for OpenAI Whisper processing."""

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
    )

    model: str = Field(default="whisper-1")
    language: Optional[str] = None
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    response_format: str = Field(default="verbose_json")
    timestamp_granularities: List[str] = Field(
        default_factory=lambda: [
            "word",
            "segment",
        ],
    )


class KeywordExtractionConfig(BaseModel):
    """Configuration for keyword extraction."""

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
    )

    max_keywords: int = Field(default=20, ge=5, le=50)
    min_keyword_length: int = Field(default=3, ge=2, le=10)
    use_tfidf: bool = True
    use_yake: bool = True
    use_spacy: bool = True
    subject_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class ProcessingJobRequest(BaseModel):
    """Schema for processing job requests."""

    upload_id: uuid.UUID
    priority: int = Field(default=1, ge=1, le=10)
    textract_config: Optional[TextractConfig] = None
    whisper_config: Optional[WhisperConfig] = None
    keyword_config: Optional[KeywordExtractionConfig] = None


class ProcessingJobResponse(BaseModel):
    """Schema for processing job responses."""

    job_id: uuid.UUID
    upload_id: uuid.UUID
    status: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)


class EvidenceSummary(BaseModel):
    """Schema for evidence summary responses."""

    upload: EvidenceUploadResponse
    extractions: List[EvidenceExtractionResponse]
    linkages: List[IEPGoalLinkageResponse]
    audit_entries: List[EvidenceAuditEntryResponse]


class BulkLinkageRequest(BaseModel):
    """Schema for bulk linkage requests."""

    learner_id: uuid.UUID
    subject_areas: Optional[List[str]] = None
    min_linkage_strength: float = Field(default=0.7, ge=0.0, le=1.0)
    auto_validate_threshold: float = Field(default=0.9, ge=0.0, le=1.0)


class LinkageAnalytics(BaseModel):
    """Schema for linkage analytics responses."""

    total_extractions: int
    total_linkages: int
    average_linkage_strength: float
    validated_linkages: int
    pending_validation: int
    subject_distribution: Dict[str, int]
    confidence_distribution: Dict[str, int]


class ExtractionStats(BaseModel):
    """Schema for extraction statistics."""

    total_uploads: int
    processed_uploads: int
    pending_uploads: int
    failed_uploads: int
    total_extractions: int
    average_processing_time: Optional[float] = None
    extraction_types: Dict[str, int]
    file_types: Dict[str, int]
