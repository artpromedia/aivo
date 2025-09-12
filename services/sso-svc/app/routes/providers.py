"""
Identity Provider management endpoints.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from ..database import get_session
from ..models import IdentityProvider, ProviderType, ProviderStatus
from ..schemas.provider import (
    ProviderCreate, ProviderUpdate, ProviderResponse,
    ProviderListResponse, ProviderTestResult
)
from ..services.provider_manager import ProviderManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=ProviderListResponse)
async def list_providers(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    provider_type: Optional[ProviderType] = Query(None, description="Filter by provider type"),
    status: Optional[ProviderStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    session: AsyncSession = Depends(get_session)
):
    """
    List identity providers with optional filtering.

    Returns a paginated list of identity providers with support for
    filtering by tenant, type, and status.
    """
    try:
        query = select(IdentityProvider).where(
            IdentityProvider.deleted_at.is_(None)
        )

        # Apply filters
        if tenant_id:
            query = query.where(IdentityProvider.tenant_id == tenant_id)
        if provider_type:
            query = query.where(IdentityProvider.provider_type == provider_type)
        if status:
            query = query.where(IdentityProvider.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(IdentityProvider.display_order, IdentityProvider.name)
        query = query.offset(skip).limit(limit)

        result = await session.execute(query)
        providers = result.scalars().all()

        return ProviderListResponse(
            providers=[ProviderResponse.from_orm(p) for p in providers],
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve providers")


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific identity provider by ID.

    Returns detailed information about an identity provider
    including configuration and status.
    """
    try:
        result = await session.execute(
            select(IdentityProvider).where(
                IdentityProvider.id == provider_id,
                IdentityProvider.deleted_at.is_(None)
            )
        )
        provider = result.scalar_one_or_none()

        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")

        return ProviderResponse.from_orm(provider)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve provider")


@router.post("/", response_model=ProviderResponse)
async def create_provider(
    provider_data: ProviderCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new identity provider.

    Creates a new identity provider configuration with the provided
    settings. The provider will be created in pending status.
    """
    try:
        provider_manager = ProviderManager(session)
        provider = await provider_manager.create_provider(provider_data)

        return ProviderResponse.from_orm(provider)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to create provider")


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: UUID,
    provider_data: ProviderUpdate,
    session: AsyncSession = Depends(get_session)
):
    """
    Update an existing identity provider.

    Updates the configuration of an existing identity provider.
    Some changes may require re-testing the provider connection.
    """
    try:
        provider_manager = ProviderManager(session)
        provider = await provider_manager.update_provider(provider_id, provider_data)

        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")

        return ProviderResponse.from_orm(provider)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update provider")


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete instead of soft delete"),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete an identity provider.

    By default performs a soft delete, preserving audit trail.
    Use hard_delete=true to permanently remove the provider.
    """
    try:
        provider_manager = ProviderManager(session)
        success = await provider_manager.delete_provider(provider_id, hard_delete)

        if not success:
            raise HTTPException(status_code=404, detail="Provider not found")

        return {"message": "Provider deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete provider")


@router.post("/{provider_id}/test", response_model=ProviderTestResult)
async def test_provider(
    provider_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Test identity provider connectivity and configuration.

    Performs a comprehensive test of the provider configuration
    including metadata retrieval, certificate validation, and
    endpoint connectivity.
    """
    try:
        provider_manager = ProviderManager(session)
        test_result = await provider_manager.test_provider(provider_id)

        if not test_result:
            raise HTTPException(status_code=404, detail="Provider not found")

        return test_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to test provider")


@router.post("/{provider_id}/activate")
async def activate_provider(
    provider_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Activate an identity provider.

    Changes provider status to active, enabling it for authentication.
    Provider must pass configuration tests before activation.
    """
    try:
        provider_manager = ProviderManager(session)
        success = await provider_manager.activate_provider(provider_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Provider not found or failed validation"
            )

        return {"message": "Provider activated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate provider")


@router.post("/{provider_id}/deactivate")
async def deactivate_provider(
    provider_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Deactivate an identity provider.

    Changes provider status to inactive, disabling it for new
    authentication requests. Existing sessions remain valid.
    """
    try:
        provider_manager = ProviderManager(session)
        success = await provider_manager.deactivate_provider(provider_id)

        if not success:
            raise HTTPException(status_code=404, detail="Provider not found")

        return {"message": "Provider deactivated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate provider")


@router.get("/{provider_id}/metadata")
async def get_provider_metadata(
    provider_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Get SAML metadata for an identity provider.

    Returns the raw SAML metadata XML for the specified provider.
    Useful for debugging and integration verification.
    """
    try:
        result = await session.execute(
            select(IdentityProvider).where(
                IdentityProvider.id == provider_id,
                IdentityProvider.deleted_at.is_(None)
            )
        )
        provider = result.scalar_one_or_none()

        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")

        if not provider.is_saml_provider():
            raise HTTPException(
                status_code=400,
                detail="Metadata only available for SAML providers"
            )

        return {
            "entity_id": provider.entity_id,
            "metadata_url": provider.metadata_url,
            "metadata_xml": provider.metadata_xml,
            "sso_url": provider.sso_url,
            "slo_url": provider.slo_url,
            "certificate": provider.certificate
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider metadata {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metadata")


@router.put("/{provider_id}/metadata")
async def update_provider_metadata(
    provider_id: UUID,
    metadata_url: Optional[str] = None,
    metadata_xml: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Update identity provider metadata.

    Updates SAML metadata for a provider either from a URL
    or direct XML content. Validates the metadata structure.
    """
    try:
        if not metadata_url and not metadata_xml:
            raise HTTPException(
                status_code=400,
                detail="Either metadata_url or metadata_xml must be provided"
            )

        provider_manager = ProviderManager(session)
        success = await provider_manager.update_metadata(
            provider_id,
            metadata_url=metadata_url,
            metadata_xml=metadata_xml
        )

        if not success:
            raise HTTPException(status_code=404, detail="Provider not found")

        return {"message": "Metadata updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update provider metadata {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update metadata")
