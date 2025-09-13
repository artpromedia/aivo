"""
Pydantic schemas for retention policies
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

from ..models import EntityType


class RetentionPolicyBase(BaseModel):
    """Base retention policy schema."""
    retention_days: int = Field(..., gt=0, description="Number of days to retain data")
    auto_delete_enabled: bool = Field(True, description="Enable automatic deletion")
    grace_period_days: int = Field(30, ge=0, description="Grace period before deletion")
    legal_basis: Optional[str] = Field(None, max_length=200, description="Legal basis for retention")
    compliance_framework: Optional[str] = Field(None, max_length=100, description="Compliance framework (FERPA, COPPA, GDPR)")
    description: Optional[str] = Field(None, description="Policy description")
    custom_rules: Optional[Dict[str, Any]] = Field(None, description="Custom retention rules")


class RetentionPolicyCreate(RetentionPolicyBase):
    """Schema for creating retention policy."""
    created_by: str = Field(..., max_length=100, description="User creating the policy")


class RetentionPolicyUpdate(BaseModel):
    """Schema for updating retention policy."""
    retention_days: Optional[int] = Field(None, gt=0, description="Number of days to retain data")
    auto_delete_enabled: Optional[bool] = Field(None, description="Enable automatic deletion")
    grace_period_days: Optional[int] = Field(None, ge=0, description="Grace period before deletion")
    legal_basis: Optional[str] = Field(None, max_length=200, description="Legal basis for retention")
    compliance_framework: Optional[str] = Field(None, max_length=100, description="Compliance framework")
    description: Optional[str] = Field(None, description="Policy description")
    custom_rules: Optional[Dict[str, Any]] = Field(None, description="Custom retention rules")
    updated_by: str = Field(..., max_length=100, description="User updating the policy")


class RetentionPolicyResponse(RetentionPolicyBase):
    """Schema for retention policy response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: EntityType
    tenant_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str


class RetentionPolicyListResponse(BaseModel):
    """Schema for retention policy list response."""
    policies: List[RetentionPolicyResponse]
    total: int


class RetentionPolicyValidation(BaseModel):
    """Schema for policy validation response."""
    is_valid: bool
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class RetentionPolicyImpact(BaseModel):
    """Schema for policy impact analysis."""
    entity_type: EntityType
    tenant_id: Optional[str]
    current_data_count: int
    data_to_delete: int
    data_under_legal_hold: int
    estimated_deletion_date: Optional[datetime]
    storage_savings_mb: Optional[float]
    affected_subjects: List[str] = Field(default_factory=list)
