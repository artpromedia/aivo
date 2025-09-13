"""Authentication and authorization service."""

from fastapi import HTTPException, Depends, Header
from typing import Optional
import os
import jwt
import structlog

logger = structlog.get_logger()

class AuthService:
    """Service for handling authentication and authorization."""

    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")

    def decode_token(self, token: str) -> dict:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def get_tenant_from_token(self, token: str) -> str:
        """Extract tenant ID from JWT token."""
        payload = self.decode_token(token)
        tenant_id = payload.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=401, detail="Tenant ID not found in token")

        return tenant_id

    def get_user_from_token(self, token: str) -> str:
        """Extract user ID from JWT token."""
        payload = self.decode_token(token)
        user_id = payload.get("sub") or payload.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        return user_id

# Global auth service instance
auth_service = AuthService()

# Dependency functions
async def get_current_tenant(
    authorization: Optional[str] = Header(None)
) -> str:
    """Dependency to get current tenant from Authorization header."""
    if not authorization:
        # For development/testing, use default tenant
        return os.getenv("DEFAULT_TENANT_ID", "default")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.split(" ")[1]
    return auth_service.get_tenant_from_token(token)

async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> str:
    """Dependency to get current user from Authorization header."""
    if not authorization:
        # For development/testing, use default user
        return os.getenv("DEFAULT_USER_ID", "system")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.split(" ")[1]
    return auth_service.get_user_from_token(token)

async def get_current_user_and_tenant(
    authorization: Optional[str] = Header(None)
) -> tuple[str, str]:
    """Dependency to get both current user and tenant."""
    if not authorization:
        return (
            os.getenv("DEFAULT_USER_ID", "system"),
            os.getenv("DEFAULT_TENANT_ID", "default")
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.split(" ")[1]
    payload = auth_service.decode_token(token)

    user_id = payload.get("sub") or payload.get("user_id")
    tenant_id = payload.get("tenant_id")

    if not user_id or not tenant_id:
        raise HTTPException(status_code=401, detail="User ID or Tenant ID not found in token")

    return user_id, tenant_id
