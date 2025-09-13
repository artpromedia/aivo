"""Namespace management API routes."""

from typing import Any, Dict, List, Optional


from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services import NamespaceExistsError, NamespaceService

router = APIRouter(prefix="/namespaces", tags=["namespaces"])


# Request/Response Models
class NamespaceCreateRequest(BaseModel):
    """Request model for creating a namespace."""

    name: str = Field(..., min_length=1, max_length=100, description="Namespace name")
    display_name: str = Field(..., min_length=1, max_length=255, description="Display name")
    description: Optional[str] = Field(None, max_length=1000, description="Description")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    parent_namespace: Optional[str] = Field(None, max_length=100, description="Parent namespace")
    max_secrets: Optional[int] = Field(None, gt=0, description="Maximum secrets allowed")
    retention_days: Optional[int] = Field(None, gt=0, description="Retention period in days")
    allowed_users: Optional[List[str]] = Field(None, description="Allowed users")
    allowed_services: Optional[List[str]] = Field(None, description="Allowed services")
    tags: Optional[Dict[str, str]] = Field(None, description="Tags")
    created_by: Optional[str] = Field(None, description="Creator")


class NamespaceUpdateRequest(BaseModel):
    """Request model for updating a namespace."""

    display_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Display name")
    description: Optional[str] = Field(None, max_length=1000, description="Description")
    max_secrets: Optional[int] = Field(None, gt=0, description="Maximum secrets allowed")
    retention_days: Optional[int] = Field(None, gt=0, description="Retention period in days")
    allowed_users: Optional[List[str]] = Field(None, description="Allowed users")
    allowed_services: Optional[List[str]] = Field(None, description="Allowed services")
    tags: Optional[Dict[str, str]] = Field(None, description="Tags")
    updated_by: Optional[str] = Field(None, description="Updater")


class NamespaceResponse(BaseModel):
    """Response model for namespace."""

    id: str
    name: str
    display_name: str
    description: Optional[str]
    tenant_id: Optional[str]
    parent_namespace: Optional[str]
    is_active: bool
    max_secrets: Optional[int]
    retention_days: Optional[int]
    allowed_users: Optional[List[str]]
    allowed_services: Optional[List[str]]
    tags: Optional[Dict[str, str]]
    created_at: Any  # datetime
    updated_at: Any  # datetime
    created_by: Optional[str]
    updated_by: Optional[str]

    class Config:
        from_attributes = True


class NamespaceStatsResponse(BaseModel):
    """Response model for namespace statistics."""

    namespace: str
    total_secrets: int
    active_secrets: int
    expired_secrets: int
    inactive_secrets: int


class NamespaceListResponse(BaseModel):
    """Response model for namespace list."""

    namespaces: List[NamespaceResponse]
    total: int
    limit: int
    offset: int


# Dependency Functions
async def get_namespace_service(db: AsyncSession = Depends(get_db)) -> NamespaceService:
    """Get namespace service instance."""
    return NamespaceService(db)


# Route Handlers
@router.post("/", response_model=NamespaceResponse, status_code=status.HTTP_201_CREATED)
async def create_namespace(
    request: NamespaceCreateRequest,
    namespace_service: NamespaceService = Depends(get_namespace_service),
):
    """Create a new namespace."""
    try:
        namespace = await namespace_service.create_namespace(**request.model_dump())
        return NamespaceResponse.model_validate(namespace)

    except NamespaceExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{namespace_id}", response_model=NamespaceResponse)
async def get_namespace(
    namespace_id: str,
    namespace_service: NamespaceService = Depends(get_namespace_service),
):
    """Get namespace by ID."""
    try:
        namespace = await namespace_service.get_namespace(namespace_id)
        if not namespace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Namespace not found")

        return NamespaceResponse.model_validate(namespace)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/by-name/{namespace_name}", response_model=NamespaceResponse)
async def get_namespace_by_name(
    namespace_name: str,
    namespace_service: NamespaceService = Depends(get_namespace_service),
):
    """Get namespace by name."""
    try:
        namespace = await namespace_service.get_namespace_by_name(namespace_name)
        if not namespace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Namespace not found")

        return NamespaceResponse.model_validate(namespace)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{namespace_id}", response_model=NamespaceResponse)
async def update_namespace(
    namespace_id: str,
    request: NamespaceUpdateRequest,
    namespace_service: NamespaceService = Depends(get_namespace_service),
):
    """Update namespace."""
    try:
        namespace = await namespace_service.update_namespace(
            namespace_id, **request.model_dump(exclude_unset=True)
        )
        return NamespaceResponse.model_validate(namespace)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{namespace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_namespace(
    namespace_id: str,
    updated_by: Optional[str] = Query(None, description="Updater"),
    namespace_service: NamespaceService = Depends(get_namespace_service),
):
    """Deactivate namespace."""
    try:
        await namespace_service.deactivate_namespace(namespace_id, updated_by)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=NamespaceListResponse)
async def list_namespaces(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    parent_namespace: Optional[str] = Query(None, description="Filter by parent namespace"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset results"),
    namespace_service: NamespaceService = Depends(get_namespace_service),
):
    """List namespaces with filtering."""
    try:
        namespaces = await namespace_service.list_namespaces(
            tenant_id=tenant_id,
            parent_namespace=parent_namespace,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

        return NamespaceListResponse(
            namespaces=[NamespaceResponse.model_validate(ns) for ns in namespaces],
            total=len(namespaces),
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{namespace_name}/stats", response_model=NamespaceStatsResponse)
async def get_namespace_stats(
    namespace_name: str,
    namespace_service: NamespaceService = Depends(get_namespace_service),
):
    """Get namespace statistics."""
    try:
        # Verify namespace exists
        namespace = await namespace_service.get_namespace_by_name(namespace_name)
        if not namespace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Namespace not found")

        stats = await namespace_service.get_namespace_stats(namespace_name)

        return NamespaceStatsResponse(
            namespace=namespace_name,
            **stats,
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
