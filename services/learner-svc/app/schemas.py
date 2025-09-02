"""
Pydantic schemas for learner service API.
"""
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from .models import ProvisionSource


class GuardianBase(BaseModel):
    """Base guardian schema."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)


class GuardianCreate(GuardianBase):
    """Schema for creating a guardian."""
    pass


class GuardianUpdate(BaseModel):
    """Schema for updating a guardian."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)


class Guardian(GuardianBase):
    """Complete guardian schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class TeacherBase(BaseModel):
    """Base teacher schema."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: Optional[str] = Field(None, max_length=100)
    tenant_id: int


class TeacherCreate(TeacherBase):
    """Schema for creating a teacher."""
    pass


class TeacherUpdate(BaseModel):
    """Schema for updating a teacher."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    subject: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class Teacher(TeacherBase):
    """Complete teacher schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TenantBase(BaseModel):
    """Base tenant schema."""
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(default="district", max_length=50)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)


class TenantCreate(TenantBase):
    """Schema for creating a tenant."""
    pass


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class Tenant(TenantBase):
    """Complete tenant schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LearnerBase(BaseModel):
    """Base learner schema."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    dob: date
    provision_source: ProvisionSource
    guardian_id: int
    tenant_id: Optional[int] = None
    grade_current: Optional[int] = Field(None, ge=-1, le=12)  # -1 for pre-K, 0-12 for K-12

    @field_validator('dob')
    @classmethod
    def validate_dob(cls, v: date) -> date:
        """Validate date of birth is reasonable."""
        today = date.today()
        # Must be at least 2 years old and not more than 25 years old
        min_date = date(today.year - 25, today.month, today.day)
        max_date = date(today.year - 2, today.month, today.day)
        
        if v < min_date or v > max_date:
            raise ValueError('Date of birth must be between 2 and 25 years ago')
        return v


class LearnerCreate(LearnerBase):
    """Schema for creating a learner."""
    pass


class LearnerUpdate(BaseModel):
    """Schema for updating a learner."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    grade_current: Optional[int] = Field(None, ge=-1, le=12)
    tenant_id: Optional[int] = None
    is_active: Optional[bool] = None


class Learner(LearnerBase):
    """Complete learner schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    grade_default: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Related objects (optional to include)
    guardian: Optional[Guardian] = None
    tenant: Optional[Tenant] = None
    teachers: Optional[List[Teacher]] = None


class LearnerTeacherAssignment(BaseModel):
    """Schema for teacher assignments."""
    teacher_id: int
    assigned_by: Optional[str] = None


class TeacherAssignment(BaseModel):
    """Schema for teacher assignment to learner."""
    teacher_id: int = Field(..., description="ID of the teacher to assign")
    assigned_by: Optional[str] = Field(None, description="Who assigned the teacher")


class BulkTeacherAssignment(BaseModel):
    """Schema for bulk teacher assignment."""
    teacher_ids: List[int] = Field(..., description="List of teacher IDs to assign")
    assigned_by: Optional[str] = Field(None, description="Who assigned the teachers")


# Legacy schema names for compatibility
LearnerTeacherAssignment = TeacherAssignment
LearnerTeacherBulkAssignment = BulkTeacherAssignment


# Response Models
class LearnerResponse(BaseModel):
    """Response model for learner data."""
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    dob: date
    provision_source: ProvisionSource
    grade_default: int
    grade_current: Optional[int] = None
    guardian_id: int
    tenant_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    guardian: Optional['GuardianResponse'] = None
    tenant: Optional['TenantResponse'] = None
    teachers: List['TeacherResponse'] = []

    model_config = ConfigDict(from_attributes=True)


class GuardianResponse(BaseModel):
    """Response model for guardian data."""
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeacherResponse(BaseModel):
    """Response model for teacher data."""
    id: int
    first_name: str
    last_name: str
    email: str
    subject: Optional[str] = None
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantResponse(BaseModel):
    """Response model for tenant data."""
    id: int
    name: str
    domain: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    timestamp: datetime


class PrivateBrainRequestEvent(BaseModel):
    """Schema for PRIVATE_BRAIN_REQUEST event."""
    learner_id: int
    event_type: str = "PRIVATE_BRAIN_REQUEST"
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
