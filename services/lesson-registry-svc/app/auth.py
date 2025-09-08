"""Authentication and authorization service."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


class TokenData(BaseModel):
    """Token data model."""

    user_id: UUID
    tenant_id: UUID
    email: str
    roles: list[str]
    exp: datetime


class User(BaseModel):
    """User model for authentication."""

    id: UUID
    tenant_id: UUID
    email: str
    roles: list[str]
    is_active: bool = True


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Verify JWT token and return token data."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        user_id: str = payload.get("user_id")
        tenant_id: str = payload.get("tenant_id")
        email: str = payload.get("email")
        roles: list[str] = payload.get("roles", [])
        exp: float = payload.get("exp")

        if user_id is None or tenant_id is None or email is None:
            raise credentials_exception

        # Check if token is expired
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = TokenData(
            user_id=UUID(user_id),
            tenant_id=UUID(tenant_id),
            email=email,
            roles=roles,
            exp=datetime.fromtimestamp(exp) if exp else datetime.utcnow(),
        )

        return token_data

    except JWTError as exc:
        logger.error("JWT validation error: %s", exc)
        raise credentials_exception from exc
    except ValueError as e:
        logger.error("Token validation error: %s", e)
        raise credentials_exception from e


async def get_current_user(token_data: TokenData = Depends(verify_token)) -> User:
    """Get current user from token."""
    return User(
        id=token_data.user_id,
        tenant_id=token_data.tenant_id,
        email=token_data.email,
        roles=token_data.roles,
    )


class RoleChecker:
    """Role-based access control checker."""

    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not any(role in current_user.roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user


# Predefined role checkers
require_admin = RoleChecker(settings.admin_roles)
require_teacher = RoleChecker(settings.teacher_roles + settings.admin_roles)
require_teacher_only = RoleChecker(settings.teacher_roles)


def can_edit_lesson(current_user: User, lesson_created_by: UUID, lesson_tenant_id: UUID) -> bool:
    """Check if user can edit a lesson."""
    # Admin can edit any lesson in their tenant
    if any(role in current_user.roles for role in settings.admin_roles):
        return current_user.tenant_id == lesson_tenant_id

    # Teacher can only edit their own lessons
    if any(role in current_user.roles for role in settings.teacher_roles):
        return current_user.id == lesson_created_by and current_user.tenant_id == lesson_tenant_id

    return False


def can_publish_lesson(current_user: User, lesson_tenant_id: UUID) -> bool:
    """Check if user can publish a lesson."""
    # Only admins can publish lessons
    if any(role in current_user.roles for role in settings.admin_roles):
        return current_user.tenant_id == lesson_tenant_id

    return False


def can_view_lesson(current_user: User, lesson_tenant_id: UUID) -> bool:
    """Check if user can view a lesson."""
    # Users can view lessons in their tenant
    return current_user.tenant_id == lesson_tenant_id


# Mock function for development - replace with actual user service
async def get_user_by_email(email: str) -> User | None:
    """Get user by email - mock implementation."""
    # This should be replaced with actual user service call
    if email == "admin@example.com":
        return User(
            id=UUID("12345678-1234-1234-1234-123456789abc"),
            tenant_id=UUID("87654321-4321-4321-4321-cba987654321"),
            email=email,
            roles=["admin"],
        )
    elif email == "teacher@example.com":
        return User(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            tenant_id=UUID("87654321-4321-4321-4321-cba987654321"),
            email=email,
            roles=["teacher"],
        )
    return None
