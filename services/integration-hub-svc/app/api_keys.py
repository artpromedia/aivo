"""API Keys management endpoints."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.config import settings
from app.database import get_db
from app.models import ApiKey, Tenant

logger = structlog.get_logger(__name__)
router = APIRouter()


# Pydantic schemas
class ApiKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str = Field(..., min_length=1, max_length=255, description="API key name")
    description: Optional[str] = Field(None, max_length=1000, description="API key description")
    scopes: List[str] = Field(default=["read", "write"], description="API key permissions")
    expires_in_days: Optional[int] = Field(
        default=365,
        ge=1,
        le=365,
        description="Days until expiration"
    )
    rate_limit_per_minute: Optional[int] = Field(
        None,
        ge=1,
        le=10000,
        description="Rate limit per minute"
    )


class ApiKeyRotate(BaseModel):
    """Schema for rotating an API key."""

    expires_in_days: Optional[int] = Field(
        default=365,
        ge=1,
        le=365,
        description="Days until expiration for new key"
    )


class ApiKeyResponse(BaseModel):
    """Schema for API key response."""

    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    key_prefix: str
    scopes: List[str]
    is_active: bool
    is_revoked: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    rate_limit_per_minute: Optional[int]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(ApiKeyResponse):
    """Schema for API key creation response with the actual key."""

    api_key: str = Field(..., description="The actual API key (only shown once)")


class ApiKeyList(BaseModel):
    """Schema for API key list response."""

    api_keys: List[ApiKeyResponse]
    total: int
    page: int
    size: int


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key with prefix and hash."""
    # Generate random key
    key_part = secrets.token_urlsafe(settings.api_key_length)

    # Create full key with prefix
    full_key = f"{settings.api_key_prefix}{key_part}"

    # Create hash for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    # Create prefix for identification
    key_prefix = full_key[:12]  # First 12 characters for identification

    return full_key, key_hash, key_prefix


async def get_tenant_by_id(tenant_id: UUID, db: AsyncSession) -> Tenant:
    """Get tenant by ID or raise 404."""
    stmt = select(Tenant).where(Tenant.id == tenant_id, Tenant.is_active == True)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return tenant


@router.post("/tenants/{tenant_id}/api-keys", response_model=ApiKeyCreateResponse)
async def create_api_key(
    tenant_id: UUID,
    api_key_data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system",  # TODO: Add proper auth
) -> ApiKeyCreateResponse:
    """Create a new API key for a tenant."""
    logger.info("Creating API key", tenant_id=str(tenant_id), name=api_key_data.name)

    # Verify tenant exists
    tenant = await get_tenant_by_id(tenant_id, db)

    # Check API key limit
    stmt = select(ApiKey).where(
        and_(ApiKey.tenant_id == tenant_id, ApiKey.is_revoked == False)
    )
    result = await db.execute(stmt)
    existing_keys = result.scalars().all()

    if len(existing_keys) >= tenant.max_api_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum number of API keys ({tenant.max_api_keys}) exceeded"
        )

    # Generate API key
    full_key, key_hash, key_prefix = generate_api_key()

    # Set expiration
    expires_at = None
    if api_key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_in_days)

    # Create API key record
    api_key = ApiKey(
        tenant_id=tenant_id,
        name=api_key_data.name,
        description=api_key_data.description,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=api_key_data.scopes,
        expires_at=expires_at,
        rate_limit_per_minute=api_key_data.rate_limit_per_minute,
        created_by=current_user,
    )

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info("API key created", api_key_id=str(api_key.id), tenant_id=str(tenant_id))

    # Return response with the actual key (only time it's shown)
    response_data = ApiKeyResponse.model_validate(api_key)
    return ApiKeyCreateResponse(**response_data.model_dump(), api_key=full_key)


@router.get("/tenants/{tenant_id}/api-keys", response_model=ApiKeyList)
async def list_api_keys(
    tenant_id: UUID,
    page: int = 1,
    size: int = 50,
    include_revoked: bool = False,
    db: AsyncSession = Depends(get_db),
) -> ApiKeyList:
    """List API keys for a tenant."""
    # Verify tenant exists
    await get_tenant_by_id(tenant_id, db)

    # Build query
    conditions = [ApiKey.tenant_id == tenant_id]
    if not include_revoked:
        conditions.append(ApiKey.is_revoked == False)

    stmt = (
        select(ApiKey)
        .where(and_(*conditions))
        .order_by(ApiKey.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    result = await db.execute(stmt)
    api_keys = result.scalars().all()

    # Get total count
    count_stmt = select(ApiKey).where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    return ApiKeyList(
        api_keys=[ApiKeyResponse.model_validate(key) for key in api_keys],
        total=total,
        page=page,
        size=size,
    )


@router.get("/tenants/{tenant_id}/api-keys/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    tenant_id: UUID,
    api_key_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ApiKeyResponse:
    """Get a specific API key."""
    stmt = select(ApiKey).where(
        and_(
            ApiKey.id == api_key_id,
            ApiKey.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return ApiKeyResponse.model_validate(api_key)


@router.post("/tenants/{tenant_id}/api-keys/{api_key_id}/rotate", response_model=ApiKeyCreateResponse)
async def rotate_api_key(
    tenant_id: UUID,
    api_key_id: UUID,
    rotate_data: ApiKeyRotate,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system",  # TODO: Add proper auth
) -> ApiKeyCreateResponse:
    """Rotate an API key (generate new key, revoke old one)."""
    logger.info("Rotating API key", api_key_id=str(api_key_id), tenant_id=str(tenant_id))

    # Get existing API key
    stmt = select(ApiKey).where(
        and_(
            ApiKey.id == api_key_id,
            ApiKey.tenant_id == tenant_id,
            ApiKey.is_revoked == False,
        )
    )
    result = await db.execute(stmt)
    old_api_key = result.scalar_one_or_none()

    if not old_api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or already revoked"
        )

    # Generate new API key
    full_key, key_hash, key_prefix = generate_api_key()

    # Set expiration
    expires_at = None
    if rotate_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=rotate_data.expires_in_days)

    # Create new API key with same properties
    new_api_key = ApiKey(
        tenant_id=tenant_id,
        name=f"{old_api_key.name} (rotated)",
        description=old_api_key.description,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=old_api_key.scopes,
        expires_at=expires_at,
        rate_limit_per_minute=old_api_key.rate_limit_per_minute,
        created_by=current_user,
    )

    # Revoke old API key
    old_api_key.is_revoked = True
    old_api_key.revoked_at = datetime.utcnow()
    old_api_key.revoked_by = current_user
    old_api_key.revoked_reason = "Rotated"

    db.add(new_api_key)
    await db.commit()
    await db.refresh(new_api_key)

    logger.info(
        "API key rotated",
        old_key_id=str(api_key_id),
        new_key_id=str(new_api_key.id),
        tenant_id=str(tenant_id)
    )

    # Return response with the new key
    response_data = ApiKeyResponse.model_validate(new_api_key)
    return ApiKeyCreateResponse(**response_data.model_dump(), api_key=full_key)


@router.delete("/tenants/{tenant_id}/api-keys/{api_key_id}")
async def delete_api_key(
    tenant_id: UUID,
    api_key_id: UUID,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system",  # TODO: Add proper auth
) -> dict[str, str]:
    """Delete (revoke) an API key."""
    logger.info("Deleting API key", api_key_id=str(api_key_id), tenant_id=str(tenant_id))

    stmt = select(ApiKey).where(
        and_(
            ApiKey.id == api_key_id,
            ApiKey.tenant_id == tenant_id,
            ApiKey.is_revoked == False,
        )
    )
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or already revoked"
        )

    # Revoke the API key
    api_key.is_revoked = True
    api_key.revoked_at = datetime.utcnow()
    api_key.revoked_by = current_user
    api_key.revoked_reason = reason or "Deleted via API"

    await db.commit()

    logger.info("API key deleted", api_key_id=str(api_key_id), tenant_id=str(tenant_id))

    return {"message": "API key revoked successfully"}
