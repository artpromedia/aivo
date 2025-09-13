"""
Banner Management API Routes
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import BannerSeverity, BannerType
from app.services.banner_service import BannerService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/banners", tags=["banners"])

# Initialize service
banner_service = BannerService()


# Request/Response schemas
class CreateBannerRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    banner_type: BannerType
    severity: BannerSeverity = BannerSeverity.INFO
    target_tenants: Optional[List[str]] = Field(default_factory=list)
    target_roles: Optional[List[str]] = Field(default_factory=list)
    auto_dismiss: bool = Field(default=False)
    auto_dismiss_minutes: Optional[int] = Field(None, ge=1, le=1440)
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_by: str = Field(..., min_length=1)
    incident_id: Optional[str] = None


class UpdateBannerRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1, max_length=1000)
    banner_type: Optional[BannerType] = None
    severity: Optional[BannerSeverity] = None
    target_tenants: Optional[List[str]] = None
    target_roles: Optional[List[str]] = None
    auto_dismiss: Optional[bool] = None
    auto_dismiss_minutes: Optional[int] = Field(None, ge=1, le=1440)
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class BannerResponse(BaseModel):
    id: str
    title: str
    message: str
    banner_type: BannerType
    severity: BannerSeverity
    target_tenants: List[str]
    target_roles: List[str]
    auto_dismiss: bool
    auto_dismiss_minutes: Optional[int]
    starts_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    incident_id: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BannerListResponse(BaseModel):
    banners: List[BannerResponse]
    pagination: Dict[str, Any]


class UserBannerResponse(BaseModel):
    banner: BannerResponse
    dismissed: bool
    dismissed_at: Optional[datetime]


class DismissBannerRequest(BaseModel):
    user_id: str = Field(..., min_length=1)


@router.post("/", response_model=BannerResponse, status_code=status.HTTP_201_CREATED)
async def create_banner(
    request: CreateBannerRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new banner announcement."""

    try:
        banner = await banner_service.create_banner(
            db=db,
            title=request.title,
            message=request.message,
            banner_type=request.banner_type,
            severity=request.severity,
            target_tenants=request.target_tenants,
            target_roles=request.target_roles,
            auto_dismiss=request.auto_dismiss,
            auto_dismiss_minutes=request.auto_dismiss_minutes,
            starts_at=request.starts_at,
            expires_at=request.expires_at,
            created_by=request.created_by,
            incident_id=uuid.UUID(request.incident_id) if request.incident_id else None
        )

        logger.info(
            "Banner created via API",
            banner_id=str(banner.id),
            title=banner.title,
            banner_type=banner.banner_type.value
        )

        return BannerResponse.model_validate(banner)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create banner", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create banner"
        )


@router.get("/", response_model=BannerListResponse)
async def list_banners(
    banner_type: Optional[BannerType] = Query(None, description="Filter by banner type"),
    severity: Optional[BannerSeverity] = Query(None, description="Filter by severity"),
    active_only: bool = Query(True, description="Show only active banners"),
    include_expired: bool = Query(False, description="Include expired banners"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """List banner announcements with filtering and pagination."""

    try:
        result = await banner_service.list_banners(
            db=db,
            banner_type=banner_type,
            severity=severity,
            active_only=active_only,
            include_expired=include_expired,
            page=page,
            page_size=page_size
        )

        return BannerListResponse(
            banners=[BannerResponse.model_validate(banner) for banner in result["banners"]],
            pagination=result["pagination"]
        )

    except Exception as e:
        logger.error("Failed to list banners", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list banners"
        )


@router.get("/active", response_model=List[UserBannerResponse])
async def get_active_banners_for_user(
    user_id: str = Query(..., description="User ID"),
    tenant_id: Optional[str] = Query(None, description="User's tenant ID"),
    roles: Optional[List[str]] = Query(None, description="User's roles"),
    db: AsyncSession = Depends(get_db)
):
    """Get active banners for a specific user with dismissal status."""

    try:
        banners = await banner_service.get_active_banners_for_user(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles or []
        )

        response = []
        for banner_data in banners:
            response.append(UserBannerResponse(
                banner=BannerResponse.model_validate(banner_data["banner"]),
                dismissed=banner_data["dismissed"],
                dismissed_at=banner_data["dismissed_at"]
            ))

        return response

    except Exception as e:
        logger.error("Failed to get active banners for user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active banners"
        )


@router.get("/{banner_id}", response_model=BannerResponse)
async def get_banner(
    banner_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific banner by ID."""

    try:
        banner = await banner_service.get_banner(db, banner_id)

        if not banner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Banner not found"
            )

        return BannerResponse.model_validate(banner)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get banner", banner_id=str(banner_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get banner"
        )


@router.put("/{banner_id}", response_model=BannerResponse)
async def update_banner(
    banner_id: uuid.UUID,
    request: UpdateBannerRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing banner."""

    try:
        banner = await banner_service.update_banner(
            db=db,
            banner_id=banner_id,
            title=request.title,
            message=request.message,
            banner_type=request.banner_type,
            severity=request.severity,
            target_tenants=request.target_tenants,
            target_roles=request.target_roles,
            auto_dismiss=request.auto_dismiss,
            auto_dismiss_minutes=request.auto_dismiss_minutes,
            starts_at=request.starts_at,
            expires_at=request.expires_at,
            is_active=request.is_active
        )

        if not banner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Banner not found"
            )

        logger.info("Banner updated via API", banner_id=str(banner_id))

        return BannerResponse.model_validate(banner)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update banner", banner_id=str(banner_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update banner"
        )


@router.delete("/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_banner(
    banner_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a banner (soft delete)."""

    try:
        success = await banner_service.delete_banner(db, banner_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Banner not found"
            )

        logger.info("Banner deleted via API", banner_id=str(banner_id))

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete banner", banner_id=str(banner_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete banner"
        )


@router.post("/{banner_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_banner(
    banner_id: uuid.UUID,
    request: DismissBannerRequest,
    db: AsyncSession = Depends(get_db)
):
    """Dismiss a banner for a specific user."""

    try:
        success = await banner_service.dismiss_banner(
            db=db,
            banner_id=banner_id,
            user_id=request.user_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Banner not found"
            )

        logger.info(
            "Banner dismissed",
            banner_id=str(banner_id),
            user_id=request.user_id
        )

        return {"success": True, "message": "Banner dismissed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to dismiss banner",
            banner_id=str(banner_id),
            user_id=request.user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to dismiss banner"
        )


@router.post("/cleanup-expired", status_code=status.HTTP_200_OK)
async def cleanup_expired_banners(
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger cleanup of expired banners."""

    try:
        cleaned_count = await banner_service.cleanup_expired_banners(db)

        logger.info("Banner cleanup completed", cleaned_count=cleaned_count)

        return {"cleaned_banners": cleaned_count}

    except Exception as e:
        logger.error("Failed to cleanup expired banners", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired banners"
        )
