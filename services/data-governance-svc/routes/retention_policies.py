"""
Retention Policies API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_db
from ..models import RetentionPolicy, EntityType
from ..schemas.retention import (
    RetentionPolicyCreate, RetentionPolicyUpdate, RetentionPolicyResponse,
    RetentionPolicyListResponse
)
from ..services.retention_service import RetentionPolicyService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=RetentionPolicyListResponse)
@limiter.limit("30/minute")
async def get_retention_policies(
    request,
    entity_type: Optional[EntityType] = Query(None, description="Filter by entity type"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get all retention policies with optional filtering."""
    service = RetentionPolicyService(db)

    policies = await service.list_policies(
        entity_type=entity_type,
        tenant_id=tenant_id
    )

    return RetentionPolicyListResponse(
        policies=policies,
        total=len(policies)
    )


@router.get("/{entity_type}", response_model=RetentionPolicyResponse)
@limiter.limit("30/minute")
async def get_retention_policy(
    request,
    entity_type: EntityType,
    tenant_id: Optional[str] = Query(None, description="Tenant ID for multi-tenant policies"),
    db: AsyncSession = Depends(get_db)
):
    """Get retention policy for specific entity type and tenant."""
    service = RetentionPolicyService(db)

    policy = await service.get_policy(entity_type=entity_type, tenant_id=tenant_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retention policy not found for entity type '{entity_type}'"
        )

    return policy


@router.put("/{entity_type}", response_model=RetentionPolicyResponse)
@limiter.limit("10/minute")
async def create_or_update_retention_policy(
    request,
    entity_type: EntityType,
    policy_data: RetentionPolicyCreate,
    tenant_id: Optional[str] = Query(None, description="Tenant ID for multi-tenant policies"),
    db: AsyncSession = Depends(get_db)
):
    """Create or update retention policy for specific entity type."""
    service = RetentionPolicyService(db)

    # Check if policy exists
    existing_policy = await service.get_policy(entity_type=entity_type, tenant_id=tenant_id)

    if existing_policy:
        # Update existing policy
        update_data = RetentionPolicyUpdate(**policy_data.dict())
        policy = await service.update_policy(
            policy_id=existing_policy.id,
            update_data=update_data
        )
    else:
        # Create new policy
        policy = await service.create_policy(
            entity_type=entity_type,
            tenant_id=tenant_id,
            policy_data=policy_data
        )

    return policy


@router.delete("/{entity_type}")
@limiter.limit("5/minute")
async def delete_retention_policy(
    request,
    entity_type: EntityType,
    tenant_id: Optional[str] = Query(None, description="Tenant ID for multi-tenant policies"),
    db: AsyncSession = Depends(get_db)
):
    """Delete retention policy for specific entity type."""
    service = RetentionPolicyService(db)

    success = await service.delete_policy(entity_type=entity_type, tenant_id=tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retention policy not found for entity type '{entity_type}'"
        )

    return {"message": "Retention policy deleted successfully"}


@router.post("/{entity_type}/validate")
@limiter.limit("20/minute")
async def validate_retention_policy(
    request,
    entity_type: EntityType,
    policy_data: RetentionPolicyCreate,
    tenant_id: Optional[str] = Query(None, description="Tenant ID for multi-tenant policies"),
    db: AsyncSession = Depends(get_db)
):
    """Validate retention policy configuration without saving."""
    service = RetentionPolicyService(db)

    validation_result = await service.validate_policy(
        entity_type=entity_type,
        tenant_id=tenant_id,
        policy_data=policy_data
    )

    return validation_result


@router.get("/{entity_type}/impact")
@limiter.limit("10/minute")
async def get_policy_impact(
    request,
    entity_type: EntityType,
    tenant_id: Optional[str] = Query(None, description="Tenant ID for multi-tenant policies"),
    db: AsyncSession = Depends(get_db)
):
    """Get impact analysis of current retention policy."""
    service = RetentionPolicyService(db)

    impact = await service.get_policy_impact(entity_type=entity_type, tenant_id=tenant_id)
    return impact


@router.post("/bulk-update")
@limiter.limit("5/minute")
async def bulk_update_policies(
    request,
    updates: List[dict],
    db: AsyncSession = Depends(get_db)
):
    """Bulk update multiple retention policies."""
    service = RetentionPolicyService(db)

    results = await service.bulk_update_policies(updates)
    return {"updated_policies": results}
