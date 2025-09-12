"""
Pydantic schemas for API request/response models.

Data validation and serialization schemas for the i18n service.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TranslationCreate(BaseModel):
    """Schema for creating a new translation."""

    key: str = Field(..., min_length=1, max_length=255, description="Translation key")
    locale: str = Field(..., min_length=2, max_length=10, description="Locale code")
    value: str = Field(..., min_length=1, description="Translation value")
    context: str | None = Field(None, description="Context for the translation")
    description: str | None = Field(None, description="Description for translators")


class TranslationUpdate(BaseModel):
    """Schema for updating an existing translation."""

    value: str | None = Field(None, min_length=1, description="New translation value")
    context: str | None = Field(None, description="Updated context")
    description: str | None = Field(None, description="Updated description")
    is_approved: bool | None = Field(None, description="Approval status")


class TranslationResponse(BaseModel):
    """Schema for translation responses."""

    id: UUID
    key: str
    locale: str
    value: str
    context: str | None = None
    description: str | None = None
    is_approved: bool
    accessibility_compliant: bool
    wcag_level: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocaleConfigCreate(BaseModel):
    """Schema for creating locale configuration."""

    locale: str = Field(..., min_length=2, max_length=10, description="Locale code")
    display_name: str = Field(
        ..., min_length=1, max_length=100, description="Display name"
    )
    is_rtl: bool = Field(False, description="Is right-to-left language")
    is_enabled: bool = Field(True, description="Is locale enabled")
    fallback_locale: str | None = Field(None, description="Fallback locale")


class LocaleConfigResponse(BaseModel):
    """Schema for locale configuration responses."""

    id: UUID
    locale: str
    display_name: str
    is_rtl: bool
    is_enabled: bool
    fallback_locale: str | None = None
    completion_percentage: float
    total_translations: int
    translated_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccessibilityAuditResponse(BaseModel):
    """Schema for accessibility audit responses."""

    id: UUID
    translation_id: UUID
    audit_type: str
    wcag_level: str
    score: float
    issues_found: list[dict]
    recommendations: list[str]
    auditor_id: str | None = None
    audit_tool: str
    audit_date: datetime
    next_audit_date: datetime | None = None

    class Config:
        from_attributes = True


class AccessibilityStatsResponse(BaseModel):
    """Schema for accessibility statistics responses."""

    total_translations: int
    compliant_translations: int
    aa_level_translations: int
    compliance_percentage: float
    aa_percentage: float
    target_met: bool
    locale: str | None = None


class TranslationKeyResponse(BaseModel):
    """Schema for translation key responses."""

    id: UUID
    key: str
    namespace: str
    category: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class BulkImportRequest(BaseModel):
    """Schema for bulk import requests."""

    translations: dict[str, dict[str, str]] = Field(
        ..., description="Translations in format {locale: {key: value}}"
    )
    approve_all: bool = Field(
        False, description="Auto-approve all imported translations"
    )
    overwrite_existing: bool = Field(
        False, description="Overwrite existing translations"
    )


class BulkImportResponse(BaseModel):
    """Schema for bulk import responses."""

    imported_count: int
    updated_count: int
    skipped_count: int
    errors: list[str]
    success: bool


class SearchRequest(BaseModel):
    """Schema for search requests."""

    query: str = Field(..., min_length=1, description="Search query")
    locale: str | None = Field(None, description="Filter by locale")
    search_keys: bool = Field(True, description="Search in translation keys")
    search_values: bool = Field(True, description="Search in translation values")
    case_sensitive: bool = Field(False, description="Case sensitive search")


class SearchResponse(BaseModel):
    """Schema for search responses."""

    results: list[TranslationResponse]
    total_count: int
    query: str
    filters: dict[str, str]


class LocaleStatsResponse(BaseModel):
    """Schema for locale statistics responses."""

    locale: str
    display_name: str
    total_keys: int
    translated_keys: int
    approved_keys: int
    completion_percentage: float
    approval_percentage: float
    missing_keys: list[str]
    accessibility_compliant: int
    wcag_aa_compliant: int
    last_updated: datetime | None = None


class ComplianceReportResponse(BaseModel):
    """Schema for accessibility compliance reports."""

    locale: str
    total_translations: int
    compliant_count: int
    non_compliant_count: int
    wcag_aa_count: int
    wcag_a_count: int
    below_a_count: int
    compliance_percentage: float
    common_issues: list[dict[str, int]]
    recommendations: list[str]
    generated_at: datetime


class ValidationResponse(BaseModel):
    """Schema for validation responses."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    suggestions: list[str]


class ExportRequest(BaseModel):
    """Schema for export requests."""

    locale: str
    format: str = Field("json", description="Export format: json, po, csv")
    approved_only: bool = Field(True, description="Only export approved translations")
    include_metadata: bool = Field(False, description="Include metadata in export")


class ExportResponse(BaseModel):
    """Schema for export responses."""

    locale: str
    format: str
    total_translations: int
    exported_count: int
    download_url: str | None = None
    content: dict | None = None


class HealthResponse(BaseModel):
    """Schema for health check responses."""

    status: str
    service: str
    version: str = "1.0.0"
    timestamp: datetime
    database_connected: bool
    features: list[str] = [
        "translations",
        "locales",
        "accessibility",
        "bulk_operations",
        "search",
    ]


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str
    message: str
    details: dict | None = None
    timestamp: datetime


# Request/Response pairs for specific operations
class ApprovalRequest(BaseModel):
    """Schema for approval requests."""

    translation_ids: list[UUID]
    auditor_id: str | None = None
    notes: str | None = None


class ApprovalResponse(BaseModel):
    """Schema for approval responses."""

    approved_count: int
    failed_count: int
    errors: list[str]


class MissingTranslationsResponse(BaseModel):
    """Schema for missing translations responses."""

    target_locale: str
    reference_locale: str
    missing_keys: list[str]
    total_missing: int
    completion_percentage: float


class LocaleComparisonRequest(BaseModel):
    """Schema for locale comparison requests."""

    base_locale: str
    compare_locales: list[str]
    include_stats: bool = Field(True, description="Include completion statistics")


class LocaleComparisonResponse(BaseModel):
    """Schema for locale comparison responses."""

    base_locale: str
    comparisons: list[dict[str, any]]
    summary: dict[str, any]


# Accessibility-specific schemas
class AccessibilityAuditRequest(BaseModel):
    """Schema for accessibility audit requests."""

    translation_ids: list[UUID] | None = None
    locale: str | None = None
    audit_type: str = Field("automated", description="Type of audit")
    auditor_id: str | None = None
    force_reaudit: bool = Field(
        False, description="Force re-audit of already audited translations"
    )


class AccessibilityConfigResponse(BaseModel):
    """Schema for accessibility configuration responses."""

    wcag_version: str = "2.2"
    target_level: str = "AA"
    target_compliance: float = 98.0
    enabled_tools: list[str] = ["internal_validator", "axe-core"]
    audit_frequency_days: int = 90


class AccessibilityIssueResponse(BaseModel):
    """Schema for accessibility issue responses."""

    issue_type: str
    severity: str
    count: int
    affected_locales: list[str]
    common_patterns: list[str]
    recommendations: list[str]
