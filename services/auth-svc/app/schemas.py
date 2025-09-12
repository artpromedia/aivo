"""
Pydantic schemas for request/response validation.
"""

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["guardian", "teacher", "staff", "admin"] = "guardian"
    tenant_id: Optional[uuid.UUID] = None


class GuardianRegister(BaseModel):
    """Schema for guardian self-registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class LoginRequest(BaseModel):
    """Schema for login requests."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class StaffLoginRequest(BaseModel):
    """Schema for staff login with additional context."""

    email: EmailStr
    password: str = Field(..., min_length=1)
    tenant_id: Optional[uuid.UUID] = None  # For multi-tenant staff


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token requests."""

    refresh_token: str = Field(..., min_length=1)


class InviteTeacherRequest(BaseModel):
    """Schema for teacher invitation."""

    email: EmailStr
    tenant_id: uuid.UUID
    message: Optional[str] = Field(None, max_length=500)


class AcceptInviteRequest(BaseModel):
    """Schema for invitation acceptance."""

    invite_token: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserResponse(UserBase):
    """Schema for user responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: Literal["guardian", "teacher", "staff", "admin"]
    tenant_id: Optional[uuid.UUID] = None
    status: Literal["active", "inactive", "pending", "suspended"]
    avatar: Optional[str] = None
    phone: Optional[str] = None
    is_email_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    """Schema for authentication responses."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str  # user_id as string
    email: str
    role: Literal["guardian", "teacher", "staff", "admin"]
    tenant_id: Optional[str] = None  # UUID as string
    dash_context: Optional[dict] = None  # Dashboard context for admin users
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    jti: str  # JWT ID for token revocation


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str
    message: str
    details: Optional[dict] = None


class ValidationErrorDetail(BaseModel):
    """Schema for validation error details."""

    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""

    error: str = "validation_failed"
    message: str = "Request validation failed"
    validation_errors: list[ValidationErrorDetail]


class InviteTokenResponse(BaseModel):
    """Schema for invite token responses."""

    invite_token: str
    email: str
    role: Literal["teacher", "staff"]
    expires_at: datetime
    invited_by: uuid.UUID


class PasswordResetRequest(BaseModel):
    """Schema for password reset requests."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    """Schema for profile updates."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar: Optional[str] = Field(None, max_length=500)


# Add to schemas.py - new schemas for role management and invite resend


class RoleAssignRequest(BaseModel):
    """Schema for role assignment requests."""

    tenant_id: uuid.UUID
    role: Literal["teacher", "staff", "district_admin"]


class RoleRevokeRequest(BaseModel):
    """Schema for role revocation requests."""

    tenant_id: uuid.UUID
    role: Literal["teacher", "staff", "district_admin"]


class RoleOperationResponse(BaseModel):
    """Schema for role operation responses."""

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str
    action: Literal["assigned", "revoked"]
    message: str


class InviteResendResponse(BaseModel):
    """Schema for invite resend responses."""

    invite_id: uuid.UUID
    email: str
    status: Literal["sent", "failed"]
    message: str
