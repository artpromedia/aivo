"""
Role mapping management endpoints.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from ..database import get_session
from ..models import RoleMapping, MappingType, MappingOperator
from ..schemas.mapping import (
    MappingCreate, MappingUpdate, MappingResponse,
    MappingListResponse, MappingTestRequest, MappingTestResult
)
from ..services.mapping_manager import MappingManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=MappingListResponse)
async def list_mappings(
    provider_id: Optional[str] = Query(None, description="Filter by provider ID"),
    mapping_type: Optional[MappingType] = Query(None, description="Filter by mapping type"),
    enabled_only: bool = Query(True, description="Show only enabled mappings"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    session: AsyncSession = Depends(get_session)
):
    """
    List role mappings with optional filtering.

    Returns a paginated list of role mappings with support for
    filtering by provider, type, and enabled status.
    """
    try:
        query = select(RoleMapping).where(
            RoleMapping.deleted_at.is_(None)
        )

        # Apply filters
        if provider_id:
            query = query.where(RoleMapping.provider_id == provider_id)
        if mapping_type:
            query = query.where(RoleMapping.mapping_type == mapping_type)
        if enabled_only:
            query = query.where(RoleMapping.is_enabled == True)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(RoleMapping.priority.desc(), RoleMapping.name)
        query = query.offset(skip).limit(limit)

        result = await session.execute(query)
        mappings = result.scalars().all()

        return MappingListResponse(
            mappings=[MappingResponse.from_orm(m) for m in mappings],
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        logger.error(f"Failed to list mappings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mappings")


@router.get("/{mapping_id}", response_model=MappingResponse)
async def get_mapping(
    mapping_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific role mapping by ID.

    Returns detailed information about a role mapping
    including its configuration and usage statistics.
    """
    try:
        result = await session.execute(
            select(RoleMapping).where(
                RoleMapping.id == mapping_id,
                RoleMapping.deleted_at.is_(None)
            )
        )
        mapping = result.scalar_one_or_none()

        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")

        return MappingResponse.from_orm(mapping)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mapping")


@router.post("/", response_model=MappingResponse)
async def create_mapping(
    mapping_data: MappingCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new role mapping.

    Creates a new role mapping configuration that defines how
    SAML attributes or groups map to application roles.
    """
    try:
        mapping_manager = MappingManager(session)
        mapping = await mapping_manager.create_mapping(mapping_data)

        return MappingResponse.from_orm(mapping)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to create mapping")


@router.put("/{mapping_id}", response_model=MappingResponse)
async def update_mapping(
    mapping_id: UUID,
    mapping_data: MappingUpdate,
    session: AsyncSession = Depends(get_session)
):
    """
    Update an existing role mapping.

    Updates the configuration of an existing role mapping.
    Changes take effect immediately for new authentications.
    """
    try:
        mapping_manager = MappingManager(session)
        mapping = await mapping_manager.update_mapping(mapping_id, mapping_data)

        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")

        return MappingResponse.from_orm(mapping)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update mapping")


@router.delete("/{mapping_id}")
async def delete_mapping(
    mapping_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete instead of soft delete"),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a role mapping.

    By default performs a soft delete, preserving audit trail.
    Use hard_delete=true to permanently remove the mapping.
    """
    try:
        mapping_manager = MappingManager(session)
        success = await mapping_manager.delete_mapping(mapping_id, hard_delete)

        if not success:
            raise HTTPException(status_code=404, detail="Mapping not found")

        return {"message": "Mapping deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete mapping")


@router.post("/{mapping_id}/test", response_model=MappingTestResult)
async def test_mapping(
    mapping_id: UUID,
    test_data: MappingTestRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Test a role mapping with sample data.

    Tests how a role mapping would behave with provided
    sample SAML attributes or group memberships.
    """
    try:
        mapping_manager = MappingManager(session)
        test_result = await mapping_manager.test_mapping(mapping_id, test_data)

        if test_result is None:
            raise HTTPException(status_code=404, detail="Mapping not found")

        return test_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to test mapping")


@router.post("/{mapping_id}/enable")
async def enable_mapping(
    mapping_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Enable a role mapping.

    Activates the mapping for use in authentication flows.
    """
    try:
        mapping_manager = MappingManager(session)
        success = await mapping_manager.enable_mapping(mapping_id)

        if not success:
            raise HTTPException(status_code=404, detail="Mapping not found")

        return {"message": "Mapping enabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to enable mapping")


@router.post("/{mapping_id}/disable")
async def disable_mapping(
    mapping_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Disable a role mapping.

    Deactivates the mapping, preventing it from being used
    in authentication flows.
    """
    try:
        mapping_manager = MappingManager(session)
        success = await mapping_manager.disable_mapping(mapping_id)

        if not success:
            raise HTTPException(status_code=404, detail="Mapping not found")

        return {"message": "Mapping disabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable mapping")


@router.get("/provider/{provider_id}", response_model=MappingListResponse)
async def get_provider_mappings(
    provider_id: UUID,
    include_disabled: bool = Query(False, description="Include disabled mappings"),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all role mappings for a specific provider.

    Returns all role mappings configured for a given identity provider,
    ordered by priority.
    """
    try:
        query = select(RoleMapping).where(
            RoleMapping.provider_id == provider_id,
            RoleMapping.deleted_at.is_(None)
        )

        if not include_disabled:
            query = query.where(RoleMapping.is_enabled == True)

        # Order by priority and name
        query = query.order_by(RoleMapping.priority.desc(), RoleMapping.name)

        result = await session.execute(query)
        mappings = result.scalars().all()

        return MappingListResponse(
            mappings=[MappingResponse.from_orm(m) for m in mappings],
            total=len(mappings),
            skip=0,
            limit=len(mappings)
        )

    except Exception as e:
        logger.error(f"Failed to get provider mappings for {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve provider mappings")


@router.post("/test-attributes", response_model=List[MappingTestResult])
async def test_attributes_against_mappings(
    provider_id: UUID,
    test_data: MappingTestRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Test SAML attributes against all mappings for a provider.

    Evaluates provided SAML attributes against all active mappings
    for a provider to show which roles would be assigned.
    """
    try:
        mapping_manager = MappingManager(session)
        test_results = await mapping_manager.test_attributes_against_provider(
            provider_id, test_data
        )

        return test_results

    except Exception as e:
        logger.error(f"Failed to test attributes against provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to test attributes")


@router.put("/{mapping_id}/priority")
async def update_mapping_priority(
    mapping_id: UUID,
    priority: int = Query(..., description="New priority value (higher = more priority)"),
    session: AsyncSession = Depends(get_session)
):
    """
    Update the priority of a role mapping.

    Changes the evaluation order of mappings. Higher priority
    mappings are evaluated first.
    """
    try:
        mapping_manager = MappingManager(session)
        success = await mapping_manager.update_priority(mapping_id, priority)

        if not success:
            raise HTTPException(status_code=404, detail="Mapping not found")

        return {"message": "Priority updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update mapping priority {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update priority")
