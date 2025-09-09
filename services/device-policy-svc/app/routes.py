"""FastAPI routes for Device Policy Service."""

import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PolicyStatus, PolicyType
from app.schemas import (
    AllowlistEntryCreate,
    AllowlistEntryResponse,
    AllowlistEntryUpdate,
    AllowlistResponse,
    DevicePolicyAssign,
    DevicePolicyResponse,
    PolicyCreate,
    PolicyListResponse,
    PolicyResponse,
    PolicySyncRequest,
    PolicySyncResponse,
    PolicyUpdate,
)
from app.services import AllowlistService, PolicyService, PolicySyncService

logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()

# Initialize services
policy_service = PolicyService()
sync_service = PolicySyncService(policy_service)
allowlist_service = AllowlistService()


# Policy management endpoints
@router.post("/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_data: PolicyCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyResponse:
    """Create a new device policy."""
    try:
        # Get user from request headers (in production, use proper auth)
        created_by = request.headers.get("X-User-ID")

        policy = await policy_service.create_policy(policy_data, db, created_by=created_by)
        return PolicyResponse.from_orm(policy)
    except Exception as e:
        logger.error("Failed to create policy", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create policy"
        ) from e


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyResponse:
    """Get a specific policy by ID."""
    policy = await policy_service.get_policy(policy_id, db)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return PolicyResponse.from_orm(policy)


@router.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: UUID,
    policy_data: PolicyUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyResponse:
    """Update an existing policy."""
    policy = await policy_service.update_policy(policy_id, policy_data, db)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return PolicyResponse.from_orm(policy)


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a policy."""
    success = await policy_service.delete_policy(policy_id, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")


@router.get("/policies", response_model=PolicyListResponse)
async def list_policies(
    policy_type: Annotated[PolicyType | None, Query()] = None,
    status_filter: Annotated[PolicyStatus | None, Query(alias="status")] = None,
    tenant_id: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 50,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> PolicyListResponse:
    """List policies with pagination and filters."""
    policies, total = await policy_service.list_policies(
        db, policy_type, status_filter, tenant_id, page, size
    )

    pages = (total + size - 1) // size

    return PolicyListResponse(
        items=[PolicyResponse.from_orm(p) for p in policies],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


# Device policy assignment endpoints
@router.post(
    "/device-policies", response_model=DevicePolicyResponse, status_code=status.HTTP_201_CREATED
)
async def assign_policy_to_device(
    assignment: DevicePolicyAssign,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DevicePolicyResponse:
    """Assign a policy to a device."""
    try:
        assigned_by = request.headers.get("X-User-ID")

        device_policy = await policy_service.assign_policy_to_device(
            assignment.device_id, assignment.policy_id, db, assigned_by=assigned_by
        )
        return DevicePolicyResponse.from_orm(device_policy)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to assign policy", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to assign policy"
        ) from e


@router.get("/devices/{device_id}/policies", response_model=list[DevicePolicyResponse])
async def get_device_policies(
    device_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DevicePolicyResponse]:
    """Get all policies assigned to a device."""
    device_policies = await policy_service.get_device_policies(device_id, db)
    return [DevicePolicyResponse.from_orm(dp) for dp in device_policies]


# Policy synchronization endpoints
@router.post("/policy/sync", response_model=PolicySyncResponse)
async def sync_policies(
    sync_request: PolicySyncRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicySyncResponse:
    """Synchronize policies with a device."""
    try:
        # Log sync request
        logger.info(
            "Policy sync requested",
            device_id=sync_request.device_id,
            client_ip=request.client.host,
            user_agent=request.headers.get("User-Agent"),
        )

        return await sync_service.sync_policies(sync_request, db)
    except Exception as e:
        logger.error("Policy sync failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Policy sync failed"
        ) from e


@router.get("/policy/sync")
async def long_poll_sync(
    device_id: Annotated[UUID, Query()],
    current_policies: Annotated[
        str, Query(description="JSON string of current policy versions")
    ] = "{}",
    timeout: Annotated[int, Query(ge=30, le=600)] = 300,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> PolicySyncResponse | None:
    """Long polling endpoint for policy updates."""
    try:
        current_dict = json.loads(current_policies)
        return await sync_service.long_poll_sync(device_id, current_dict, db, timeout)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid current_policies JSON"
        )
    except Exception as e:
        logger.error("Long poll sync failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Long poll sync failed"
        ) from e


# Allowlist management endpoints
@router.post(
    "/allowlist", response_model=AllowlistEntryResponse, status_code=status.HTTP_201_CREATED
)
async def create_allowlist_entry(
    entry_data: AllowlistEntryCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AllowlistEntryResponse:
    """Create a new allowlist entry."""
    try:
        created_by = request.headers.get("X-User-ID")

        entry = await allowlist_service.create_entry(entry_data, db, created_by=created_by)
        return AllowlistEntryResponse.from_orm(entry)
    except Exception as e:
        logger.error("Failed to create allowlist entry", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create allowlist entry",
        ) from e


@router.get("/allowlist/{entry_id}", response_model=AllowlistEntryResponse)
async def get_allowlist_entry(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AllowlistEntryResponse:
    """Get a specific allowlist entry by ID."""
    entry = await allowlist_service.get_entry(entry_id, db)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Allowlist entry not found"
        )
    return AllowlistEntryResponse.from_orm(entry)


@router.put("/allowlist/{entry_id}", response_model=AllowlistEntryResponse)
async def update_allowlist_entry(
    entry_id: UUID,
    entry_data: AllowlistEntryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AllowlistEntryResponse:
    """Update an allowlist entry."""
    entry = await allowlist_service.update_entry(entry_id, entry_data, db)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Allowlist entry not found"
        )
    return AllowlistEntryResponse.from_orm(entry)


@router.delete("/allowlist/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allowlist_entry(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete an allowlist entry."""
    success = await allowlist_service.delete_entry(entry_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Allowlist entry not found"
        )


@router.get("/allowlist", response_model=AllowlistResponse)
async def list_allowlist_entries(
    entry_type: Annotated[str | None, Query(pattern="^(domain|url|ip|subnet)$")] = None,
    category: Annotated[str | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    tenant_id: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 50,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AllowlistResponse:
    """List allowlist entries with pagination and filters."""
    entries, total = await allowlist_service.list_entries(
        db, entry_type, category, is_active, tenant_id, page, size
    )

    pages = (total + size - 1) // size

    return AllowlistResponse(
        items=[AllowlistEntryResponse.from_orm(e) for e in entries],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/allowlist/active", response_model=list[AllowlistEntryResponse])
async def get_active_allowlist(
    tenant_id: Annotated[str | None, Query()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[AllowlistEntryResponse]:
    """Get all active allowlist entries for walled garden implementation."""
    entries = await allowlist_service.get_active_allowlist(tenant_id, db)
    return [AllowlistEntryResponse.from_orm(e) for e in entries]


# Health check endpoint
@router.get("/health")
async def health_check(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Health check endpoint."""
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unhealthy"
        ) from e
