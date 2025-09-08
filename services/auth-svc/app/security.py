"""
Security utilities for JWT tokens and password hashing.
"""

import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from .schemas import TokenPayload


class SecurityConfig:
    """Security configuration."""

    # JWT Configuration - Using asymmetric RS256 for production
    ALGORITHM = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS = 30  # Longer-lived refresh tokens

    # RSA key pair for JWT signing (in production, load from secure storage)
    _private_key = None
    _public_key = None

    @classmethod
    def get_private_key(cls):
        """Get or generate RSA private key for JWT signing."""
        if cls._private_key is None:
            # In production, load from environment or key management system
            private_key_pem = os.getenv("JWT_PRIVATE_KEY")
            if private_key_pem:
                cls._private_key = serialization.load_pem_private_key(
                    private_key_pem.encode(), password=None, backend=default_backend()
                )
            else:
                # Generate for development (not recommended for production)
                cls._private_key = rsa.generate_private_key(
                    public_exponent=65537, key_size=2048, backend=default_backend()
                )
        return cls._private_key

    @classmethod
    def get_public_key(cls):
        """Get RSA public key for JWT verification."""
        if cls._public_key is None:
            public_key_pem = os.getenv("JWT_PUBLIC_KEY")
            if public_key_pem:
                cls._public_key = serialization.load_pem_public_key(
                    public_key_pem.encode(), backend=default_backend()
                )
            else:
                # Derive from private key
                cls._public_key = cls.get_private_key().public_key()
        return cls._public_key

    @classmethod
    def get_private_key_pem(cls):
        """Get private key as PEM string for JWT signing."""
        return (
            cls.get_private_key()
            .private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            .decode()
        )

    @classmethod
    def get_public_key_pem(cls):
        """Get public key as PEM string for JWT verification."""
        return (
            cls.get_public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode()
        )

    # Fallback to HS256 for development if RSA keys not available
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM_DEV = "HS256"  # For development fallback

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
    expires_delta: Optional[timedelta] = None,
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

    # Use RS256 with asymmetric keys for production
    try:
        private_key_pem = SecurityConfig.get_private_key_pem()
        return jwt.encode(payload, private_key_pem, algorithm=SecurityConfig.ALGORITHM)
    except Exception:
        # Fallback to HS256 for development if RSA keys fail
        return jwt.encode(
            payload, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM_DEV
        )


def create_refresh_token() -> str:
    """Create a secure refresh token."""
    return secrets.token_urlsafe(32)


def create_invite_token() -> str:
    """Create a secure invitation token."""
    return secrets.token_urlsafe(32)


def verify_token(token: str) -> TokenPayload:
    """Verify and decode a JWT token."""
    try:
        # Try RS256 first
        try:
            public_key_pem = SecurityConfig.get_public_key_pem()
            payload = jwt.decode(token, public_key_pem, algorithms=[SecurityConfig.ALGORITHM])
        except Exception:
            # Fallback to HS256 for development
            payload = jwt.decode(
                token, SecurityConfig.SECRET_KEY, algorithms=[SecurityConfig.ALGORITHM_DEV]
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
            jti=payload.get("jti", ""),
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
            "features": ["analytics", "user_management", "billing", "support"],
        }
    elif user_role == "staff":
        return {
            "permissions": ["read:tenant", "write:tenant"],
            "scope": "tenant",
            "tenant_id": tenant_id,
            "features": ["analytics", "user_management"],
        }
    elif user_role == "teacher":
        return {
            "permissions": ["read:courses", "write:courses", "read:students"],
            "scope": "tenant",
            "tenant_id": tenant_id,
            "features": ["course_management", "student_progress"],
        }
    elif user_role == "guardian":
        return {
            "permissions": ["read:children"],
            "scope": "family",
            "tenant_id": tenant_id,
            "features": ["child_progress", "billing"],
        }

    return None


def validate_role_permissions(
    required_role: str, user_role: str, tenant_id: Optional[str] = None
) -> bool:
    """Validate if user has required permissions."""
    role_hierarchy = {"admin": 4, "staff": 3, "teacher": 2, "guardian": 1}

    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)

    return user_level >= required_level
