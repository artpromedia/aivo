"""
Pydantic schemas for tenant service.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from .models import TenantKind, SeatState, UserRole


# Base schemas
class TenantBase(BaseModel):
    """Base tenant schema."""
    name: str = Field(..., min_length=1, max_length=255)
    kind: TenantKind


class TenantCreate(TenantBase):
    """Schema for creating a tenant."""
    parent_id: Optional[int] = None


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class Tenant(TenantBase):
    """Full tenant schema with relationships."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool


class TenantWithChildren(Tenant):
    """Tenant schema with children included."""
    children: List[Tenant] = []


# Seat schemas
class SeatBase(BaseModel):
    """Base seat schema."""
    tenant_id: int
    state: SeatState = SeatState.FREE


class SeatCreate(BaseModel):
    """Schema for creating seats."""
    tenant_id: int
    count: int = Field(..., gt=0, le=1000)


class SeatAllocate(BaseModel):
    """Schema for allocating a seat."""
    seat_id: int
    learner_id: str = Field(..., min_length=1)


class SeatReclaim(BaseModel):
    """Schema for reclaiming a seat."""
    seat_id: int
    reason: Optional[str] = Field(None, max_length=500)


class Seat(SeatBase):
    """Full seat schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    learner_id: Optional[str] = None
    reserved_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SeatSummary(BaseModel):
    """Summary of seat allocation for a tenant."""
    tenant_id: int
    tenant_name: str
    total_seats: int
    free_seats: int
    reserved_seats: int
    assigned_seats: int
    utilization_percentage: float


# User role schemas
class UserTenantRoleBase(BaseModel):
    """Base user tenant role schema."""
    user_id: str = Field(..., min_length=1)
    tenant_id: int
    role: UserRole


class UserTenantRoleCreate(UserTenantRoleBase):
    """Schema for creating user tenant roles."""
    pass


class UserTenantRole(UserTenantRoleBase):
    """Full user tenant role schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    is_active: bool


# Audit schemas
class SeatAudit(BaseModel):
    """Seat audit entry schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    seat_id: int
    previous_state: Optional[SeatState]
    new_state: SeatState
    previous_learner_id: Optional[str]
    new_learner_id: Optional[str]
    changed_by: str
    reason: Optional[str]
    created_at: datetime


# District and school specific schemas
class DistrictCreate(BaseModel):
    """Schema for creating a district."""
    name: str = Field(..., min_length=1, max_length=255)


class SchoolCreate(BaseModel):
    """Schema for creating a school under a district."""
    name: str = Field(..., min_length=1, max_length=255)


# Response schemas
class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    error_code: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    data: Optional[dict] = None


# Bulk operations
class BulkSeatOperation(BaseModel):
    """Schema for bulk seat operations."""
    seat_ids: List[int] = Field(..., min_length=1, max_length=100)


class BulkSeatAllocate(BulkSeatOperation):
    """Schema for bulk seat allocation."""
    learner_ids: List[str] = Field(..., min_length=1, max_length=100)
    
    def model_validate(cls, v):
        """Validate that seat_ids and learner_ids have same length."""
        if len(v.seat_ids) != len(v.learner_ids):
            raise ValueError("seat_ids and learner_ids must have the same length")
        return v
