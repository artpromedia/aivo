"""
Pydantic schemas for enrollment router service.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

from .models import ProvisionSource, EnrollmentStatus


class LearnerProfile(BaseModel):
    """Learner profile information."""
    learner_id: Optional[str] = None
    email: str = Field(..., description="Learner email address")
    first_name: str = Field(..., min_length=1, description="Learner first name")
    last_name: str = Field(..., min_length=1, description="Learner last name")
    grade_level: Optional[str] = None
    school: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class EnrollmentContext(BaseModel):
    """Context information for enrollment routing."""
    tenant_id: Optional[int] = Field(None, description="District/tenant ID")
    guardian_id: Optional[str] = Field(None, description="Parent/guardian ID")
    source: Optional[str] = Field(None, description="Enrollment source")
    referral_code: Optional[str] = None
    campaign_id: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None

    @model_validator(mode='after')
    def validate_enrollment_context(self):
        """Ensure either tenant_id or guardian_id is provided."""
        if not self.tenant_id and not self.guardian_id:
            raise ValueError('Either tenant_id or guardian_id must be provided')
        return self


class EnrollmentRequest(BaseModel):
    """Request schema for enrollment routing."""
    learner_profile: LearnerProfile
    context: EnrollmentContext


class DistrictEnrollmentResult(BaseModel):
    """Result for district-provisioned enrollment."""
    provision_source: ProvisionSource = ProvisionSource.DISTRICT
    status: EnrollmentStatus
    tenant_id: int
    seats_reserved: int
    seats_available: int
    decision_id: int
    message: str


class ParentEnrollmentResult(BaseModel):
    """Result for parent-paid enrollment."""
    provision_source: ProvisionSource = ProvisionSource.PARENT
    status: EnrollmentStatus
    guardian_id: str
    checkout_session_id: Optional[str] = None
    checkout_url: Optional[str] = None
    decision_id: int
    message: str


class EnrollmentDecisionResponse(BaseModel):
    """Response schema for enrollment decisions."""
    decision_id: int
    provision_source: ProvisionSource
    status: EnrollmentStatus
    
    # Learner information
    learner_profile: LearnerProfile
    context: EnrollmentContext
    
    # District enrollment fields (if applicable)
    tenant_id: Optional[int] = None
    seats_reserved: Optional[int] = None
    seats_available: Optional[int] = None
    
    # Parent enrollment fields (if applicable)  
    guardian_id: Optional[str] = None
    checkout_session_id: Optional[str] = None
    checkout_url: Optional[str] = None
    
    # Metadata
    created_at: datetime
    message: str
    
    model_config = ConfigDict(from_attributes=True)


class DistrictSeatAllocationCreate(BaseModel):
    """Schema for creating district seat allocation."""
    tenant_id: int = Field(..., description="District/tenant ID")
    total_seats: int = Field(..., ge=0, description="Total allocated seats")


class DistrictSeatAllocationUpdate(BaseModel):
    """Schema for updating district seat allocation."""
    total_seats: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class DistrictSeatAllocationResponse(BaseModel):
    """Response schema for district seat allocation."""
    id: int
    tenant_id: int
    total_seats: int
    reserved_seats: int
    used_seats: int
    available_seats: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class EnrollmentEvent(BaseModel):
    """Event schema for enrollment decisions."""
    event_type: str = "ENROLLMENT_DECISION"
    decision_id: int
    provision_source: ProvisionSource
    tenant_id: Optional[int] = None
    guardian_id: Optional[str] = None
    learner_email: str
    status: EnrollmentStatus
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
