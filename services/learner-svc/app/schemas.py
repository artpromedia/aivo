"""
Pydantic schemas for learner service API.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import ProvisionSource


class GuardianBase(BaseModel):
    """Base guardian schema."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(None, max_length=20)


class GuardianCreate(GuardianBase):
    """Schema for creating a guardian."""


class GuardianUpdate(BaseModel):
    """Schema for updating a guardian."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20)


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
    subject: str | None = Field(None, max_length=100)
    tenant_id: int


class TeacherCreate(TeacherBase):
    """Schema for creating a teacher."""


class TeacherUpdate(BaseModel):
    """Schema for updating a teacher."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    subject: str | None = Field(None, max_length=100)
    is_active: bool | None = None


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
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=20)


class TenantCreate(TenantBase):
    """Schema for creating a tenant."""


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""

    name: str | None = Field(None, min_length=1, max_length=200)
    type: str | None = Field(None, max_length=50)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=20)
    is_active: bool | None = None


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
    email: EmailStr | None = None
    dob: date
    provision_source: ProvisionSource
    guardian_id: int
    tenant_id: int | None = None
    # -1 for pre-K, 0-12 for K-12
    grade_current: int | None = Field(None, ge=-1, le=12)

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        """Validate date of birth is reasonable."""
        today = date.today()
        # Must be at least 2 years old and not more than 25 years old
        min_date = date(today.year - 25, today.month, today.day)
        max_date = date(today.year - 2, today.month, today.day)

        if v < min_date or v > max_date:
            raise ValueError("Date of birth must be between 2 and 25 years ago")
        return v


class LearnerCreate(LearnerBase):
    """Schema for creating a learner."""


class LearnerUpdate(BaseModel):
    """Schema for updating a learner."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    grade_current: int | None = Field(None, ge=-1, le=12)
    tenant_id: int | None = None
    is_active: bool | None = None


class Learner(LearnerBase):
    """Complete learner schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    grade_default: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Related objects (optional to include)
    guardian: Guardian | None = None
    tenant: Tenant | None = None
    teachers: list[Teacher] | None = None


class LearnerTeacherAssignment(BaseModel):
    """Schema for teacher assignments."""

    teacher_id: int
    assigned_by: str | None = None


class TeacherAssignment(BaseModel):
    """Schema for teacher assignment to learner."""

    teacher_id: int = Field(..., description="ID of the teacher to assign")
    assigned_by: str | None = Field(None, description="Who assigned the teacher")


class BulkTeacherAssignment(BaseModel):
    """Schema for bulk teacher assignment."""

    teacher_ids: list[int] = Field(..., description="List of teacher IDs to assign")
    assigned_by: str | None = Field(None, description="Who assigned the teachers")


# Legacy schema names for compatibility
LearnerTeacherBulkAssignment = BulkTeacherAssignment


# Response Models
class LearnerResponse(BaseModel):
    """Response model for learner data."""

    id: int
    first_name: str
    last_name: str
    email: str | None = None
    dob: date
    provision_source: ProvisionSource
    grade_default: int
    grade_current: int | None = None
    guardian_id: int
    tenant_id: int | None = None
    created_at: datetime
    updated_at: datetime

    # Related data
    guardian: Optional["GuardianResponse"] = None
    tenant: Optional["TenantResponse"] = None
    teachers: list["TeacherResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class GuardianResponse(BaseModel):
    """Response model for guardian data."""

    id: int
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeacherResponse(BaseModel):
    """Response model for teacher data."""

    id: int
    first_name: str
    last_name: str
    email: str
    subject: str | None = None
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantResponse(BaseModel):
    """Response model for tenant data."""

    id: int
    name: str
    domain: str | None = None
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
    detail: str | None = None
    timestamp: datetime
