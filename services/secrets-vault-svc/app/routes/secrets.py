"""Secret management API routes."""

from datetime import datetime
from typing import Any, Dict, List, Optional


from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import AccessLevel, SecretStatus, SecretType
from ..services import (
    AccessDeniedError,
    NamespaceService,
    SecretExpiredError,
    SecretNotFoundError,
    SecretService,
)

router = APIRouter(prefix="/secrets", tags=["secrets"])


# Request/Response Models
class SecretCreateRequest(BaseModel):
    """Request model for creating a secret."""

    name: str = Field(..., min_length=1, max_length=255, description="Secret name")
    value: str = Field(..., min_length=1, description="Secret value")
    namespace: str = Field(..., min_length=1, max_length=100, description="Namespace")
    secret_type: SecretType = Field(..., description="Type of secret")
    description: Optional[str] = Field(None, max_length=1000, description="Description")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    tags: Optional[Dict[str, str]] = Field(None, description="Tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    access_level: AccessLevel = Field(AccessLevel.READ_ONLY, description="Access level")
    allowed_services: Optional[List[str]] = Field(None, description="Allowed services")
    allowed_users: Optional[List[str]] = Field(None, description="Allowed users")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    rotation_interval_days: Optional[int] = Field(None, gt=0, description="Rotation interval in days")
    auto_rotate: bool = Field(False, description="Enable automatic rotation")
    created_by: Optional[str] = Field(None, description="Creator")
    encryption_key_id: str = Field("default", description="Encryption key ID")


class SecretUpdateRequest(BaseModel):
    """Request model for updating a secret."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Secret name")
    value: Optional[str] = Field(None, min_length=1, description="Secret value")
    description: Optional[str] = Field(None, max_length=1000, description="Description")
    tags: Optional[Dict[str, str]] = Field(None, description="Tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    access_level: Optional[AccessLevel] = Field(None, description="Access level")
    allowed_services: Optional[List[str]] = Field(None, description="Allowed services")
    allowed_users: Optional[List[str]] = Field(None, description="Allowed users")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    rotation_interval_days: Optional[int] = Field(None, gt=0, description="Rotation interval in days")
    auto_rotate: Optional[bool] = Field(None, description="Enable automatic rotation")
    updated_by: Optional[str] = Field(None, description="Updater")


class SecretRotateRequest(BaseModel):
    """Request model for rotating a secret."""

    new_value: str = Field(..., min_length=1, description="New secret value")
    rotated_by: Optional[str] = Field(None, description="Rotator")
    reason: str = Field("Manual rotation", description="Rotation reason")


class SecretResponse(BaseModel):
    """Response model for secret metadata."""

    id: str
    name: str
    description: Optional[str]
    namespace: str
    tenant_id: Optional[str]
    secret_type: SecretType
    status: SecretStatus
    access_level: AccessLevel
    allowed_services: Optional[List[str]]
    allowed_users: Optional[List[str]]
    tags: Optional[Dict[str, str]]
    metadata: Optional[Dict[str, Any]]
    expires_at: Optional[datetime]
    rotation_interval_days: Optional[int]
    auto_rotate: bool
    last_accessed_at: Optional[datetime]
    last_rotated_at: Optional[datetime]
    access_count: int
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]

    class Config:
        from_attributes = True


class SecretValueResponse(BaseModel):
    """Response model for secret value."""

    id: str
    name: str
    value: str
    version: int
    last_accessed_at: Optional[datetime]


class SecretListResponse(BaseModel):
    """Response model for secret list."""

    secrets: List[SecretResponse]
    total: int
    limit: int
    offset: int


# Dependency Functions
async def get_secret_service(db: AsyncSession = Depends(get_db)) -> SecretService:
    """Get secret service instance."""
    return SecretService(db)


async def get_namespace_service(db: AsyncSession = Depends(get_db)) -> NamespaceService:
    """Get namespace service instance."""
    return NamespaceService(db)


# Route Handlers
@router.post("/", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
async def create_secret(
    request: SecretCreateRequest,
    secret_service: SecretService = Depends(get_secret_service),
    namespace_service: NamespaceService = Depends(get_namespace_service),
):
    """Create a new secret."""
    try:
        # Verify namespace exists
        namespace = await namespace_service.get_namespace_by_name(request.namespace)
        if not namespace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Namespace '{request.namespace}' not found"
            )

        secret = await secret_service.create_secret(**request.model_dump())
        return SecretResponse.model_validate(secret)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{secret_id}", response_model=SecretResponse)
async def get_secret(
    secret_id: str,
    accessor: Optional[str] = Query(None, description="Accessor (user/service)"),
    service_name: Optional[str] = Query(None, description="Service name"),
    secret_service: SecretService = Depends(get_secret_service),
):
    """Get secret metadata by ID."""
    try:
        secret = await secret_service.get_secret(secret_id, accessor, service_name)
        return SecretResponse.model_validate(secret)

    except SecretNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Secret not found")
    except AccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{secret_id}/value", response_model=SecretValueResponse)
async def get_secret_value(
    secret_id: str,
    accessor: Optional[str] = Query(None, description="Accessor (user/service)"),
    service_name: Optional[str] = Query(None, description="Service name"),
    secret_service: SecretService = Depends(get_secret_service),
):
    """Get decrypted secret value by ID."""
    try:
        secret = await secret_service.get_secret(secret_id, accessor, service_name)
        value = await secret_service.get_secret_value(secret_id, accessor, service_name)

        return SecretValueResponse(
            id=secret.id,
            name=secret.name,
            value=value,
            version=secret.version,
            last_accessed_at=secret.last_accessed_at,
        )

    except SecretNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Secret not found")
    except AccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    except SecretExpiredError:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Secret has expired")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{secret_id}", response_model=SecretResponse)
async def update_secret(
    secret_id: str,
    request: SecretUpdateRequest,
    secret_service: SecretService = Depends(get_secret_service),
):
    """Update secret."""
    try:
        secret = await secret_service.update_secret(secret_id, **request.model_dump(exclude_unset=True))
        return SecretResponse.model_validate(secret)

    except SecretNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Secret not found")
    except AccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{secret_id}/rotate", response_model=SecretResponse)
async def rotate_secret(
    secret_id: str,
    request: SecretRotateRequest,
    secret_service: SecretService = Depends(get_secret_service),
):
    """Rotate secret value."""
    try:
        secret = await secret_service.rotate_secret(
            secret_id,
            request.new_value,
            request.rotated_by,
            request.reason,
        )
        return SecretResponse.model_validate(secret)

    except SecretNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Secret not found")
    except AccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_id: str,
    deleted_by: Optional[str] = Query(None, description="Deleter"),
    hard_delete: bool = Query(False, description="Perform hard delete"),
    secret_service: SecretService = Depends(get_secret_service),
):
    """Delete secret."""
    try:
        await secret_service.delete_secret(secret_id, deleted_by, hard_delete)

    except SecretNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Secret not found")
    except AccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=SecretListResponse)
async def list_secrets(
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    secret_type: Optional[SecretType] = Query(None, description="Filter by secret type"),
    status: Optional[SecretStatus] = Query(None, description="Filter by status"),
    accessor: Optional[str] = Query(None, description="Accessor (user/service)"),
    service_name: Optional[str] = Query(None, description="Service name"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset results"),
    secret_service: SecretService = Depends(get_secret_service),
):
    """List secrets with filtering."""
    try:
        secrets = await secret_service.list_secrets(
            namespace=namespace,
            tenant_id=tenant_id,
            secret_type=secret_type,
            status=status,
            accessor=accessor,
            service_name=service_name,
            limit=limit,
            offset=offset,
        )

        return SecretListResponse(
            secrets=[SecretResponse.model_validate(secret) for secret in secrets],
            total=len(secrets),
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/expiring/check", response_model=List[SecretResponse])
async def check_expiring_secrets(
    days_ahead: int = Query(7, ge=1, le=365, description="Days ahead to check"),
    secret_service: SecretService = Depends(get_secret_service),
):
    """Get secrets that will expire within specified days."""
    try:
        secrets = await secret_service.check_expiring_secrets(days_ahead)
        return [SecretResponse.model_validate(secret) for secret in secrets]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/rotation/due", response_model=List[SecretResponse])
async def check_rotation_due_secrets(
    secret_service: SecretService = Depends(get_secret_service),
):
    """Get secrets that are due for rotation."""
    try:
        secrets = await secret_service.check_rotation_due_secrets()
        return [SecretResponse.model_validate(secret) for secret in secrets]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/stats")
async def get_secrets_stats(
    secret_service: SecretService = Depends(get_secret_service),
):
    """Get secrets statistics."""
    try:
        # Get all secrets to calculate stats
        secrets = await secret_service.list_secrets()

        total_secrets = len(secrets)
        active_secrets = len([s for s in secrets if s.status.value == "active"])
        expired_secrets = len([s for s in secrets if s.expires_at and s.expires_at < datetime.utcnow()])

        # Get namespaces count
        from ..services import NamespaceService
        namespace_service = NamespaceService()
        from ..database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            namespaces = await namespace_service.list_namespaces(db)
            namespaces_count = len(namespaces)

        # Calculate total accesses
        total_accesses = sum(s.access_count for s in secrets)

        return {
            "total_secrets": total_secrets,
            "active_secrets": active_secrets,
            "expired_secrets": expired_secrets,
            "namespaces_count": namespaces_count,
            "total_accesses": total_accesses,
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
