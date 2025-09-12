"""
FastAPI routes for authentication and authorization.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import InviteToken, RefreshToken, User
from .notifications import get_notification_client
from .schemas import (
    AcceptInviteRequest,
    AuthResponse,
    GuardianRegister,
    InviteResendResponse,
    InviteTeacherRequest,
    InviteTokenResponse,
    LoginRequest,
    RefreshTokenRequest,
    RoleAssignRequest,
    RoleOperationResponse,
    RoleRevokeRequest,
    StaffLoginRequest,
    UserResponse,
)
from .security import (
    create_access_token,
    create_invite_token,
    create_password_hash,
    create_refresh_token,
    generate_dash_context,
    verify_password,
    verify_token,
)

# Security scheme
security = HTTPBearer()

# Router
router = APIRouter()


# Database dependency placeholder - will be overridden in main.py
def get_db_dependency():
    """Database dependency placeholder."""
    raise NotImplementedError("Database dependency not configured")


# Dependency to get current user from JWT token
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db_dependency),
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    token_payload = verify_token(token)

    # Get user from database
    result = await db.execute(select(User).where(User.id == uuid.UUID(token_payload.sub)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.post("/register-guardian", response_model=AuthResponse)
async def register_guardian(
    request: GuardianRegister, db: AsyncSession = Depends(get_db_dependency)
) -> AuthResponse:
    """Register a new guardian user."""

    # Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new guardian user
    hashed_password = create_password_hash(request.password)

    # Auto-assign tenant ID for guardians (each guardian gets their own tenant)
    guardian_tenant_id = uuid.uuid4()

    new_user = User(
        email=request.email,
        hashed_password=hashed_password,
        first_name=request.first_name,
        last_name=request.last_name,
        phone=request.phone,
        role="guardian",
        tenant_id=guardian_tenant_id,
        status="active",  # Guardians are active immediately
        is_email_verified=False,  # Email verification can be done later
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create tokens
    access_token = create_access_token(
        subject=str(new_user.id),
        email=new_user.email,
        role=new_user.role,
        tenant_id=str(new_user.tenant_id) if new_user.tenant_id else None,
        dash_context=generate_dash_context(
            new_user.role, str(new_user.tenant_id) if new_user.tenant_id else None
        ),
    )

    refresh_token_value = create_refresh_token()

    # Store refresh token in database
    refresh_token = RefreshToken(
        token=refresh_token_value,
        user_id=new_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(refresh_token)
    await db.commit()

    # Send welcome email
    notification_client = get_notification_client()
    await notification_client.send_welcome_email(
        email=new_user.email,
        user_name=f"{new_user.first_name} {new_user.last_name}",
        role=new_user.role,
    )

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        expires_in=15 * 60,  # 15 minutes
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest, http_request: Request, db: AsyncSession = Depends(get_db_dependency)
) -> AuthResponse:
    """Authenticate user and return JWT tokens."""

    # Get user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not active"
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    # Create tokens
    access_token = create_access_token(
        subject=str(user.id),
        email=user.email,
        role=user.role,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        dash_context=generate_dash_context(
            user.role, str(user.tenant_id) if user.tenant_id else None
        ),
    )

    refresh_token_value = create_refresh_token()

    # Store refresh token in database
    refresh_token = RefreshToken(
        token=refresh_token_value,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        user_agent=http_request.headers.get("user-agent"),
        ip_address=http_request.client.host if http_request.client else None,
    )
    db.add(refresh_token)
    await db.commit()

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        expires_in=15 * 60,  # 15 minutes
        user=UserResponse.model_validate(user),
    )


@router.post("/login-staff", response_model=AuthResponse)
async def login_staff(
    request: StaffLoginRequest, http_request: Request, db: AsyncSession = Depends(get_db_dependency)
) -> AuthResponse:
    """Staff login with optional tenant context."""

    # Get user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    if user.role not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: staff role required"
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not active"
        )

    # Validate tenant access for staff users
    if user.role == "staff" and request.tenant_id:
        if user.tenant_id != request.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: invalid tenant"
            )

    # Update last login
    await db.execute(
        update(User).where(User.id == user.id).values(last_login_at=datetime.now(timezone.utc))
    )
    await db.commit()

    # Create tokens with tenant context
    tenant_id = (
        str(request.tenant_id)
        if request.tenant_id
        else (str(user.tenant_id) if user.tenant_id else None)
    )

    access_token = create_access_token(
        subject=str(user.id),
        email=user.email,
        role=user.role,
        tenant_id=tenant_id,
        dash_context=generate_dash_context(user.role, tenant_id),
    )

    refresh_token_value = create_refresh_token()

    # Store refresh token in database
    refresh_token = RefreshToken(
        token=refresh_token_value,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        user_agent=http_request.headers.get("user-agent"),
        ip_address=http_request.client.host if http_request.client else None,
    )
    db.add(refresh_token)
    await db.commit()

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        expires_in=15 * 60,  # 15 minutes
        user=UserResponse.model_validate(user),
    )


@router.post("/invite-teacher", response_model=InviteTokenResponse)
async def invite_teacher(
    request: InviteTeacherRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_dependency),
) -> InviteTokenResponse:
    """Invite a teacher to join a tenant."""

    # Check permissions - only staff and admin can invite teachers
    if current_user.role not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to invite teachers",
        )

    # Staff can only invite to their own tenant
    if current_user.role == "staff" and current_user.tenant_id != request.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot invite teacher to different tenant",
        )

    # Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists"
        )

    # Check for existing pending invitation
    result = await db.execute(
        select(InviteToken).where(
            InviteToken.email == request.email,
            not InviteToken.is_used,
            InviteToken.expires_at > datetime.now(timezone.utc),
        )
    )
    existing_invite = result.scalar_one_or_none()

    if existing_invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pending invitation already exists for this email",
        )

    # Create invitation token
    invite_token_value = create_invite_token()

    invite_token = InviteToken(
        token=invite_token_value,
        email=request.email,
        role="teacher",
        tenant_id=request.tenant_id,
        invited_by=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    db.add(invite_token)
    await db.commit()
    await db.refresh(invite_token)

    # Send invitation email via notification service
    notification_client = get_notification_client()
    email_sent = await notification_client.send_invite_email(
        email=request.email,
        invite_token=invite_token_value,
        role="teacher",
        invited_by=f"{current_user.first_name} {current_user.last_name}",
        organization_name="SchoolApp",
    )

    if not email_sent:
        # Log warning but don't fail the invite creation
        # The invite token is still valid even if email fails
        pass

    return InviteTokenResponse(
        invite_token=invite_token_value,
        email=request.email,
        role="teacher",
        expires_at=invite_token.expires_at,
        invited_by=current_user.id,
    )


@router.post("/accept-invite", response_model=AuthResponse)
async def accept_invite(
    request: AcceptInviteRequest, db: AsyncSession = Depends(get_db_dependency)
) -> AuthResponse:
    """Accept a teacher/staff invitation and create account."""

    # Get invitation token
    result = await db.execute(
        select(InviteToken).where(
            InviteToken.token == request.invite_token,
            not InviteToken.is_used,
            InviteToken.expires_at > datetime.now(timezone.utc),
        )
    )
    invite_token = result.scalar_one_or_none()

    if not invite_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invitation token"
        )

    # Check if user already exists
    result = await db.execute(select(User).where(User.email == invite_token.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists"
        )

    # Create new user account
    hashed_password = create_password_hash(request.password)

    new_user = User(
        email=invite_token.email,
        hashed_password=hashed_password,
        first_name=request.first_name,
        last_name=request.last_name,
        phone=request.phone,
        role=invite_token.role,
        tenant_id=invite_token.tenant_id,
        status="active",
        is_email_verified=True,  # Email is verified through invitation
    )

    try:
        db.add(new_user)

        # Mark invitation as used
        await db.execute(
            update(InviteToken)
            .where(InviteToken.id == invite_token.id)
            .values(is_used=True, used_at=datetime.now(timezone.utc))
        )

        await db.commit()
        await db.refresh(new_user)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create tokens
    access_token = create_access_token(
        subject=str(new_user.id),
        email=new_user.email,
        role=new_user.role,
        tenant_id=str(new_user.tenant_id) if new_user.tenant_id else None,
        dash_context=generate_dash_context(
            new_user.role, str(new_user.tenant_id) if new_user.tenant_id else None
        ),
    )

    refresh_token_value = create_refresh_token()

    # Store refresh token in database
    refresh_token = RefreshToken(
        token=refresh_token_value,
        user_id=new_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(refresh_token)
    await db.commit()

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        expires_in=15 * 60,  # 15 minutes
        user=UserResponse.model_validate(new_user),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db_dependency),
) -> AuthResponse:
    """Refresh access token using refresh token."""

    # Get refresh token from database
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == request.refresh_token,
            not RefreshToken.is_revoked,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    refresh_token = result.scalar_one_or_none()

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        )

    # Get user
    result = await db.execute(select(User).where(User.id == refresh_token.user_id))
    user = result.scalar_one_or_none()

    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is not active"
        )

    # Revoke old refresh token
    await db.execute(
        update(RefreshToken).where(RefreshToken.id == refresh_token.id).values(is_revoked=True)
    )

    # Create new tokens (refresh token rotation)
    access_token = create_access_token(
        subject=str(user.id),
        email=user.email,
        role=user.role,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        dash_context=generate_dash_context(
            user.role, str(user.tenant_id) if user.tenant_id else None
        ),
    )

    new_refresh_token_value = create_refresh_token()

    # Store new refresh token
    new_refresh_token = RefreshToken(
        token=new_refresh_token_value,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        user_agent=http_request.headers.get("user-agent"),
        ip_address=http_request.client.host if http_request.client else None,
    )
    db.add(new_refresh_token)
    await db.commit()

    return AuthResponse(
        access_token=access_token,
        refresh_token=new_refresh_token_value,
        expires_in=15 * 60,  # 15 minutes
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_dependency),
) -> dict:
    """Logout user and revoke refresh token."""

    # Revoke refresh token if provided
    if request.refresh_token:
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token == request.refresh_token, RefreshToken.user_id == current_user.id
            )
            .values(is_revoked=True)
        )
        await db.commit()

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


# New endpoints for role management and invite resend


@router.post("/users/{user_id}/roles", response_model=RoleOperationResponse)
async def assign_user_role(
    user_id: uuid.UUID,
    request: RoleAssignRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_dependency),
) -> RoleOperationResponse:
    """Assign a role to a user within a tenant."""

    # Check permissions - only staff and district_admin can assign roles
    if current_user.role not in ["staff", "district_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to assign roles",
        )

    # Staff can only assign roles within their own tenant
    if current_user.role == "staff" and current_user.tenant_id != request.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot assign roles in different tenant",
        )

    # Get target user
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update user role and tenant association
    target_user.role = request.role
    target_user.tenant_id = request.tenant_id
    target_user.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(target_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign role",
        )

    return RoleOperationResponse(
        user_id=target_user.id,
        tenant_id=request.tenant_id,
        role=request.role,
        action="assigned",
        message=f"Role {request.role} assigned successfully",
    )


@router.delete("/users/{user_id}/roles", response_model=RoleOperationResponse)
async def revoke_user_role(
    user_id: uuid.UUID,
    request: RoleRevokeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_dependency),
) -> RoleOperationResponse:
    """Revoke a role from a user within a tenant."""

    # Check permissions - only staff and district_admin can revoke roles
    if current_user.role not in ["staff", "district_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to revoke roles",
        )

    # Staff can only revoke roles within their own tenant
    if current_user.role == "staff" and current_user.tenant_id != request.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke roles in different tenant",
        )

    # Get target user
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if user has the role in the specified tenant
    if target_user.role != request.role or target_user.tenant_id != request.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have the specified role in this tenant",
        )

    # Revoke role by setting to basic teacher or removing tenant association
    target_user.role = "teacher"  # Default fallback role
    target_user.tenant_id = None
    target_user.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(target_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to revoke role",
        )

    return RoleOperationResponse(
        user_id=target_user.id,
        tenant_id=request.tenant_id,
        role=request.role,
        action="revoked",
        message=f"Role {request.role} revoked successfully",
    )


@router.post("/invites/{invite_id}/resend", response_model=InviteResendResponse)
async def resend_invite(
    invite_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_dependency),
) -> InviteResendResponse:
    """Resend an invitation email."""

    # Check permissions - only staff and district_admin can resend invites
    if current_user.role not in ["staff", "district_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to resend invites",
        )

    # Get invite token
    result = await db.execute(
        select(InviteToken).where(
            InviteToken.id == invite_id,
            not InviteToken.is_used,
            InviteToken.expires_at > datetime.now(timezone.utc),
        )
    )
    invite_token = result.scalar_one_or_none()

    if not invite_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found or already used/expired",
        )

    # Staff can only resend invites for their own tenant
    if current_user.role == "staff" and current_user.tenant_id != invite_token.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot resend invite for different tenant",
        )

    # Send invitation email via notification service
    notification_client = get_notification_client()
    email_sent = await notification_client.send_invite_email(
        email=invite_token.email,
        invite_token=invite_token.token,
        role=invite_token.role,
        invited_by=f"{current_user.first_name} {current_user.last_name}",
        organization_name="SchoolApp",
    )

    if email_sent:
        # Update the invite with new timestamp
        invite_token.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return InviteResendResponse(
            invite_id=invite_token.id,
            email=invite_token.email,
            status="sent",
            message="Invitation resent successfully",
        )
    else:
        return InviteResendResponse(
            invite_id=invite_token.id,
            email=invite_token.email,
            status="failed",
            message="Failed to resend invitation email",
        )
