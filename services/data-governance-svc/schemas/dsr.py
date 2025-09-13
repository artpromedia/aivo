"""
Pydantic schemas for DSR (Data Subject Rights) requests
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from ..models import DSRType, DSRStatus, EntityType


class DSRRequestBase(BaseModel):
    """Base DSR request schema."""
    subject_id: str = Field(..., max_length=100, description="Subject identifier")
    subject_type: EntityType = Field(..., description="Type of subject")
    requester_email: EmailStr = Field(..., description="Email of person making request")
    requester_name: Optional[str] = Field(None, max_length=200, description="Name of requester")
    tenant_id: Optional[str] = Field(None, max_length=100, description="Tenant ID")
    legal_basis: Optional[str] = Field(None, max_length=200, description="Legal basis for request")


class DSRRequestCreate(DSRRequestBase):
    """Schema for creating DSR request."""
    dsr_type: DSRType = Field(..., description="Type of DSR request")


class DSRRequestResponse(DSRRequestBase):
    """Schema for DSR request response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    dsr_type: DSRType
    status: DSRStatus
    progress_percentage: int
    export_file_path: Optional[str]
    export_download_url: Optional[str]
    export_expires_at: Optional[datetime]
    deletion_summary: Optional[Dict[str, Any]]
    error_details: Optional[str]
    verification_token: Optional[str]
    identity_verified: bool
    completion_certificate: Optional[str]
    requested_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class DSRRequestListResponse(BaseModel):
    """Schema for DSR request list response."""
    requests: List[DSRRequestResponse]
    total: int
    limit: int
    offset: int


class DSRStatusResponse(BaseModel):
    """Schema for DSR status response."""
    id: str
    status: DSRStatus
    progress_percentage: int
    current_step: Optional[str] = Field(None, description="Current processing step")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    error_details: Optional[str]
    blocked_by_legal_holds: List[str] = Field(default_factory=list, description="Legal hold IDs blocking this request")


class DSRExportResponse(BaseModel):
    """Schema for DSR export download response."""
    download_url: str
    expires_at: datetime
    file_size_bytes: int
    export_format: str = "zip"
    includes_metadata: bool = True


class DSRStatistics(BaseModel):
    """Schema for DSR statistics."""
    total_requests: int
    by_type: Dict[DSRType, int]
    by_status: Dict[DSRStatus, int]
    average_processing_time_hours: Optional[float]
    pending_requests: int
    blocked_by_legal_holds: int
    completed_last_30_days: int


class BulkDSRRequest(BaseModel):
    """Schema for bulk DSR requests."""
    subject_ids: List[str] = Field(..., max_items=100, description="List of subject IDs")
    subject_type: EntityType = Field(..., description="Type of subjects")
    dsr_type: DSRType = Field(..., description="Type of DSR request")
    requester_email: EmailStr = Field(..., description="Email of person making request")
    requester_name: Optional[str] = Field(None, max_length=200, description="Name of requester")
    tenant_id: Optional[str] = Field(None, max_length=100, description="Tenant ID")
    legal_basis: Optional[str] = Field(None, max_length=200, description="Legal basis for requests")
