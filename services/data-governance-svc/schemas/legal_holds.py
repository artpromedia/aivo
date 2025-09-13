"""
Pydantic schemas for legal holds
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from ..models import LegalHoldStatus, EntityType


class LegalHoldBase(BaseModel):
    """Base legal hold schema."""
    name: str = Field(..., max_length=200, description="Name of the legal hold")
    description: Optional[str] = Field(None, description="Description of the legal hold")
    case_number: Optional[str] = Field(None, max_length=100, description="Associated case number")
    entity_types: List[EntityType] = Field(..., min_items=1, description="Types of entities covered")
    subject_ids: Optional[List[str]] = Field(None, description="Specific subject IDs (if applicable)")
    tenant_id: Optional[str] = Field(None, max_length=100, description="Tenant ID")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date of the hold")
    legal_authority: Optional[str] = Field(None, max_length=200, description="Legal authority for the hold")
    custodian_name: str = Field(..., max_length=200, description="Name of data custodian")
    custodian_email: EmailStr = Field(..., description="Email of data custodian")


class LegalHoldCreate(LegalHoldBase):
    """Schema for creating legal hold."""
    created_by: str = Field(..., max_length=100, description="User creating the hold")


class LegalHoldUpdate(BaseModel):
    """Schema for updating legal hold."""
    name: Optional[str] = Field(None, max_length=200, description="Name of the legal hold")
    description: Optional[str] = Field(None, description="Description of the legal hold")
    case_number: Optional[str] = Field(None, max_length=100, description="Associated case number")
    entity_types: Optional[List[EntityType]] = Field(None, min_items=1, description="Types of entities covered")
    subject_ids: Optional[List[str]] = Field(None, description="Specific subject IDs")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date of the hold")
    legal_authority: Optional[str] = Field(None, max_length=200, description="Legal authority")
    custodian_name: Optional[str] = Field(None, max_length=200, description="Name of data custodian")
    custodian_email: Optional[EmailStr] = Field(None, description="Email of data custodian")
    updated_by: str = Field(..., max_length=100, description="User updating the hold")


class LegalHoldResponse(LegalHoldBase):
    """Schema for legal hold response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: LegalHoldStatus
    effective_date: datetime
    released_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str


class LegalHoldListResponse(BaseModel):
    """Schema for legal hold list response."""
    holds: List[LegalHoldResponse]
    total: int
    limit: int
    offset: int


class LegalHoldImpactResponse(BaseModel):
    """Schema for legal hold impact analysis."""
    hold_id: str
    hold_name: str
    affected_entities: Dict[EntityType, int]  # Count of entities by type
    blocked_dsr_requests: List[str]  # DSR request IDs
    total_data_items_protected: int
    estimated_storage_mb: Optional[float]
    subjects_under_hold: List[str]


class LegalHoldConflict(BaseModel):
    """Schema for legal hold conflict information."""
    subject_id: str
    entity_type: EntityType
    conflicting_holds: List[Dict[str, Any]]  # Hold info that would block deletion
    conflict_reason: str


class LegalHoldSummary(BaseModel):
    """Schema for active legal holds summary."""
    total_active_holds: int
    holds_by_entity_type: Dict[EntityType, int]
    holds_expiring_soon: List[Dict[str, Any]]  # Holds expiring in next 30 days
    oldest_active_hold: Optional[Dict[str, Any]]
    total_subjects_protected: int
    total_blocked_deletions: int
