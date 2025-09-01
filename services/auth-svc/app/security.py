"""
Security utilities for JWT tokens and password hashing.
"""
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import argon2

from .schemas import TokenPayload


class SecurityConfig:
    """Security configuration."""
    
    # JWT Configuration - Using asymmetric RS256 for production
    ALGORITHM = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS = 30    # Longer-lived refresh tokens
    
    # In production, these would be loaded from environment variables
    # For now, using a simple secret key for HS256 (development only)
    SECRET_KEY = "your-super-secret-key-change-in-production"
    ALGORITHM_DEV = "HS256"  # For development
    
    # Password hashing
    ARGON2_ROUNDS = 12
    ARGON2_MEMORY_COST = 65536  # 64 MB
    ARGON2_PARALLELISM = 3
    
    # Invitation tokens
    INVITE_TOKEN_EXPIRE_DAYS = 7


# Password context using Argon2
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__rounds=SecurityConfig.ARGON2_ROUNDS,
    argon2__memory_cost=SecurityConfig.ARGON2_MEMORY_COST,
    argon2__parallelism=SecurityConfig.ARGON2_PARALLELISM,
)


def create_password_hash(password: str) -> str:
    """Create a secure password hash using Argon2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    email: str,
    role: str,
    tenant_id: Optional[str] = None,
    dash_context: Optional[dict] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # JWT payload with custom claims
    payload = {
        "sub": subject,  # user_id
        "email": email,
        "role": role,
        "tenant_id": tenant_id,
        "dash_context": dash_context,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),  # JWT ID for token revocation
    }
    
    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}
    
    # Use HS256 for development (in production, use RS256 with key pairs)
    return jwt.encode(payload, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM_DEV)


def create_refresh_token() -> str:
    """Create a secure refresh token."""
    return secrets.token_urlsafe(32)


def create_invite_token() -> str:
    """Create a secure invitation token."""
    return secrets.token_urlsafe(32)


def verify_token(token: str) -> TokenPayload:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, 
            SecurityConfig.SECRET_KEY, 
            algorithms=[SecurityConfig.ALGORITHM_DEV]
        )
        
        # Validate required fields
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token payload
        token_data = TokenPayload(
            sub=user_id,
            email=payload.get("email", ""),
            role=payload.get("role", "guardian"),
            tenant_id=payload.get("tenant_id"),
            dash_context=payload.get("dash_context"),
            exp=payload.get("exp", 0),
            iat=payload.get("iat", 0),
            jti=payload.get("jti", "")
        )
        
        return token_data
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_password_reset_token() -> str:
    """Generate a secure password reset token."""
    return secrets.token_urlsafe(32)


def get_email_verification_token() -> str:
    """Generate a secure email verification token."""
    return secrets.token_urlsafe(32)


def generate_dash_context(user_role: str, tenant_id: Optional[str] = None) -> Optional[dict]:
    """Generate dashboard context based on user role and tenant."""
    if user_role == "admin":
        return {
            "permissions": ["read:all", "write:all", "delete:all"],
            "scope": "global",
            "features": ["analytics", "user_management", "billing", "support"]
        }
    elif user_role == "staff":
        return {
            "permissions": ["read:tenant", "write:tenant"],
            "scope": "tenant",
            "tenant_id": tenant_id,
            "features": ["analytics", "user_management"]
        }
    elif user_role == "teacher":
        return {
            "permissions": ["read:courses", "write:courses", "read:students"],
            "scope": "tenant",
            "tenant_id": tenant_id,
            "features": ["course_management", "student_progress"]
        }
    elif user_role == "guardian":
        return {
            "permissions": ["read:children"],
            "scope": "family",
            "tenant_id": tenant_id,
            "features": ["child_progress", "billing"]
        }
    
    return None


def validate_role_permissions(required_role: str, user_role: str, tenant_id: Optional[str] = None) -> bool:
    """Validate if user has required permissions."""
    role_hierarchy = {
        "admin": 4,
        "staff": 3,
        "teacher": 2,
        "guardian": 1
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level
