"""Rate limits and quotas management endpoints."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import ApiQuota, LimitType, RateLimit, RateLimitBreach

router = APIRouter(prefix="/limits", tags=["limits"])


# Request/Response Models
class RateLimitCreateRequest(BaseModel):
    """Request model for creating a rate limit."""

    tenant_id: str = Field(..., description="Tenant ID")
    service_name: str = Field(..., description="Service name")
    route_pattern: str = Field(..., description="Route pattern (e.g., /api/v1/secrets/*)")
    limit_type: LimitType = Field(..., description="Type of limit")
    limit_value: int = Field(..., gt=0, description="Limit value")
    enforcement_mode: str = Field("enforce", description="Enforcement mode: enforce, warn, monitor")
    description: Optional[str] = Field(None, description="Description")
    created_by: Optional[str] = Field(None, description="Creator")


class RateLimitUpdateRequest(BaseModel):
    """Request model for updating a rate limit."""

    limit_value: Optional[int] = Field(None, gt=0, description="Limit value")
    enforcement_mode: Optional[str] = Field(None, description="Enforcement mode")
    enabled: Optional[bool] = Field(None, description="Enable/disable limit")
    description: Optional[str] = Field(None, description="Description")
    updated_by: Optional[str] = Field(None, description="Updater")


class RateLimitResponse(BaseModel):
    """Response model for rate limit."""

    id: str
    tenant_id: str
    service_name: str
    route_pattern: str
    limit_type: str
    limit_value: int
    current_usage: int
    usage_percentage: float
    window_start: Optional[datetime]
    window_end: Optional[datetime]
    enabled: bool
    enforcement_mode: str
    description: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RateLimitBreachResponse(BaseModel):
    """Response model for rate limit breach."""

    id: str
    rate_limit_id: str
    tenant_id: str
    service_name: str
    route_path: str
    breach_timestamp: datetime
    attempted_requests: int
    allowed_limit: int
    breach_percentage: float
    user_id: Optional[str]
    client_ip: Optional[str]
    action_taken: str
    resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolution_notes: Optional[str]

    class Config:
        from_attributes = True


class QuotaCreateRequest(BaseModel):
    """Request model for creating API quota."""

    tenant_id: str = Field(..., description="Tenant ID")
    service_name: str = Field(..., description="Service name")
    monthly_request_limit: int = Field(10000, gt=0, description="Monthly request limit")
    daily_request_limit: int = Field(1000, gt=0, description="Daily request limit")
    hourly_request_limit: int = Field(100, gt=0, description="Hourly request limit")
    soft_limit_percentage: float = Field(0.8, ge=0.0, le=1.0, description="Soft limit threshold")
    created_by: Optional[str] = Field(None, description="Creator")


class QuotaUpdateRequest(BaseModel):
    """Request model for updating API quota."""

    monthly_request_limit: Optional[int] = Field(None, gt=0, description="Monthly request limit")
    daily_request_limit: Optional[int] = Field(None, gt=0, description="Daily request limit")
    hourly_request_limit: Optional[int] = Field(None, gt=0, description="Hourly request limit")
    soft_limit_percentage: Optional[float] = Field(None, ge=0.0, le=1.0, description="Soft limit threshold")
    enabled: Optional[bool] = Field(None, description="Enable/disable quota")
    updated_by: Optional[str] = Field(None, description="Updater")


class QuotaResponse(BaseModel):
    """Response model for API quota."""

    id: str
    tenant_id: str
    service_name: str
    monthly_request_limit: int
    daily_request_limit: int
    hourly_request_limit: int
    monthly_usage: int
    daily_usage: int
    hourly_usage: int
    monthly_usage_percentage: float
    daily_usage_percentage: float
    hourly_usage_percentage: float
    monthly_reset_at: Optional[datetime]
    daily_reset_at: Optional[datetime]
    hourly_reset_at: Optional[datetime]
    enabled: bool
    soft_limit_enabled: bool
    soft_limit_percentage: float
    created_by: Optional[str]
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LimitsOverviewResponse(BaseModel):
    """Overview of limits and quotas."""

    total_rate_limits: int
    active_rate_limits: int
    breached_limits_24h: int
    total_quotas: int
    quota_warnings: int
    quota_exceeded: int
    recent_breaches: List[RateLimitBreachResponse]


# Rate Limits Management
@router.post("/rate-limits", response_model=RateLimitResponse, status_code=status.HTTP_201_CREATED)
async def create_rate_limit(
    request: RateLimitCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new rate limit."""
    try:
        rate_limit = RateLimit(**request.model_dump())
        db.add(rate_limit)
        await db.commit()
        await db.refresh(rate_limit)

        return RateLimitResponse.model_validate(rate_limit)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/rate-limits", response_model=List[RateLimitResponse])
async def list_rate_limits(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    enabled_only: bool = Query(False, description="Show only enabled limits"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset results"),
    db: AsyncSession = Depends(get_db),
):
    """List rate limits with filtering."""
    try:
        filters = []

        if tenant_id:
            filters.append(RateLimit.tenant_id == tenant_id)
        if service_name:
            filters.append(RateLimit.service_name == service_name)
        if enabled_only:
            filters.append(RateLimit.enabled == True)

        result = await db.execute(
            select(RateLimit)
            .where(and_(*filters) if filters else True)
            .order_by(desc(RateLimit.created_at))
            .limit(limit)
            .offset(offset)
        )

        rate_limits = result.scalars().all()

        # Calculate usage percentages
        response_limits = []
        for limit in rate_limits:
            usage_percentage = (limit.current_usage / limit.limit_value * 100) if limit.limit_value > 0 else 0

            limit_dict = {
                "id": limit.id,
                "tenant_id": limit.tenant_id,
                "service_name": limit.service_name,
                "route_pattern": limit.route_pattern,
                "limit_type": limit.limit_type,
                "limit_value": limit.limit_value,
                "current_usage": limit.current_usage,
                "usage_percentage": round(usage_percentage, 2),
                "window_start": limit.window_start,
                "window_end": limit.window_end,
                "enabled": limit.enabled,
                "enforcement_mode": limit.enforcement_mode,
                "description": limit.description,
                "created_by": limit.created_by,
                "updated_by": limit.updated_by,
                "created_at": limit.created_at,
                "updated_at": limit.updated_at,
            }

            response_limits.append(RateLimitResponse(**limit_dict))

        return response_limits

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/rate-limits/{limit_id}", response_model=RateLimitResponse)
async def get_rate_limit(
    limit_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get rate limit by ID."""
    try:
        result = await db.execute(
            select(RateLimit).where(RateLimit.id == limit_id)
        )
        rate_limit = result.scalar_one_or_none()

        if not rate_limit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate limit not found")

        usage_percentage = (rate_limit.current_usage / rate_limit.limit_value * 100) if rate_limit.limit_value > 0 else 0

        limit_dict = {
            "id": rate_limit.id,
            "tenant_id": rate_limit.tenant_id,
            "service_name": rate_limit.service_name,
            "route_pattern": rate_limit.route_pattern,
            "limit_type": rate_limit.limit_type,
            "limit_value": rate_limit.limit_value,
            "current_usage": rate_limit.current_usage,
            "usage_percentage": round(usage_percentage, 2),
            "window_start": rate_limit.window_start,
            "window_end": rate_limit.window_end,
            "enabled": rate_limit.enabled,
            "enforcement_mode": rate_limit.enforcement_mode,
            "description": rate_limit.description,
            "created_by": rate_limit.created_by,
            "updated_by": rate_limit.updated_by,
            "created_at": rate_limit.created_at,
            "updated_at": rate_limit.updated_at,
        }

        return RateLimitResponse(**limit_dict)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/rate-limits/{limit_id}", response_model=RateLimitResponse)
async def update_rate_limit(
    limit_id: str,
    request: RateLimitUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update rate limit."""
    try:
        result = await db.execute(
            select(RateLimit).where(RateLimit.id == limit_id)
        )
        rate_limit = result.scalar_one_or_none()

        if not rate_limit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate limit not found")

        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rate_limit, field, value)

        rate_limit.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(rate_limit)

        usage_percentage = (rate_limit.current_usage / rate_limit.limit_value * 100) if rate_limit.limit_value > 0 else 0

        limit_dict = {
            "id": rate_limit.id,
            "tenant_id": rate_limit.tenant_id,
            "service_name": rate_limit.service_name,
            "route_pattern": rate_limit.route_pattern,
            "limit_type": rate_limit.limit_type,
            "limit_value": rate_limit.limit_value,
            "current_usage": rate_limit.current_usage,
            "usage_percentage": round(usage_percentage, 2),
            "window_start": rate_limit.window_start,
            "window_end": rate_limit.window_end,
            "enabled": rate_limit.enabled,
            "enforcement_mode": rate_limit.enforcement_mode,
            "description": rate_limit.description,
            "created_by": rate_limit.created_by,
            "updated_by": rate_limit.updated_by,
            "created_at": rate_limit.created_at,
            "updated_at": rate_limit.updated_at,
        }

        return RateLimitResponse(**limit_dict)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/rate-limits/{limit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate_limit(
    limit_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete rate limit."""
    try:
        result = await db.execute(
            select(RateLimit).where(RateLimit.id == limit_id)
        )
        rate_limit = result.scalar_one_or_none()

        if not rate_limit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate limit not found")

        await db.delete(rate_limit)
        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Rate Limit Breaches
@router.get("/breaches", response_model=List[RateLimitBreachResponse])
async def list_rate_limit_breaches(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    unresolved_only: bool = Query(False, description="Show only unresolved breaches"),
    range_hours: int = Query(24, ge=1, le=168, description="Range in hours from now"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset results"),
    db: AsyncSession = Depends(get_db),
):
    """List rate limit breaches."""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=range_hours)

        filters = [
            RateLimitBreach.breach_timestamp >= start_date,
            RateLimitBreach.breach_timestamp <= end_date,
        ]

        if tenant_id:
            filters.append(RateLimitBreach.tenant_id == tenant_id)
        if service_name:
            filters.append(RateLimitBreach.service_name == service_name)
        if unresolved_only:
            filters.append(RateLimitBreach.resolved == False)

        result = await db.execute(
            select(RateLimitBreach)
            .where(and_(*filters))
            .order_by(desc(RateLimitBreach.breach_timestamp))
            .limit(limit)
            .offset(offset)
        )

        breaches = result.scalars().all()
        return [RateLimitBreachResponse.model_validate(breach) for breach in breaches]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# API Quotas Management
@router.post("/quotas", response_model=QuotaResponse, status_code=status.HTTP_201_CREATED)
async def create_quota(
    request: QuotaCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new API quota."""
    try:
        quota = ApiQuota(**request.model_dump())
        db.add(quota)
        await db.commit()
        await db.refresh(quota)

        quota_dict = {
            "id": quota.id,
            "tenant_id": quota.tenant_id,
            "service_name": quota.service_name,
            "monthly_request_limit": quota.monthly_request_limit,
            "daily_request_limit": quota.daily_request_limit,
            "hourly_request_limit": quota.hourly_request_limit,
            "monthly_usage": quota.monthly_usage,
            "daily_usage": quota.daily_usage,
            "hourly_usage": quota.hourly_usage,
            "monthly_usage_percentage": round((quota.monthly_usage / quota.monthly_request_limit * 100), 2) if quota.monthly_request_limit > 0 else 0,
            "daily_usage_percentage": round((quota.daily_usage / quota.daily_request_limit * 100), 2) if quota.daily_request_limit > 0 else 0,
            "hourly_usage_percentage": round((quota.hourly_usage / quota.hourly_request_limit * 100), 2) if quota.hourly_request_limit > 0 else 0,
            "monthly_reset_at": quota.monthly_reset_at,
            "daily_reset_at": quota.daily_reset_at,
            "hourly_reset_at": quota.hourly_reset_at,
            "enabled": quota.enabled,
            "soft_limit_enabled": quota.soft_limit_enabled,
            "soft_limit_percentage": quota.soft_limit_percentage,
            "created_by": quota.created_by,
            "updated_by": quota.updated_by,
            "created_at": quota.created_at,
            "updated_at": quota.updated_at,
        }

        return QuotaResponse(**quota_dict)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/quotas", response_model=List[QuotaResponse])
async def list_quotas(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset results"),
    db: AsyncSession = Depends(get_db),
):
    """List API quotas with filtering."""
    try:
        filters = []

        if tenant_id:
            filters.append(ApiQuota.tenant_id == tenant_id)
        if service_name:
            filters.append(ApiQuota.service_name == service_name)

        result = await db.execute(
            select(ApiQuota)
            .where(and_(*filters) if filters else True)
            .order_by(desc(ApiQuota.created_at))
            .limit(limit)
            .offset(offset)
        )

        quotas = result.scalars().all()

        response_quotas = []
        for quota in quotas:
            quota_dict = {
                "id": quota.id,
                "tenant_id": quota.tenant_id,
                "service_name": quota.service_name,
                "monthly_request_limit": quota.monthly_request_limit,
                "daily_request_limit": quota.daily_request_limit,
                "hourly_request_limit": quota.hourly_request_limit,
                "monthly_usage": quota.monthly_usage,
                "daily_usage": quota.daily_usage,
                "hourly_usage": quota.hourly_usage,
                "monthly_usage_percentage": round((quota.monthly_usage / quota.monthly_request_limit * 100), 2) if quota.monthly_request_limit > 0 else 0,
                "daily_usage_percentage": round((quota.daily_usage / quota.daily_request_limit * 100), 2) if quota.daily_request_limit > 0 else 0,
                "hourly_usage_percentage": round((quota.hourly_usage / quota.hourly_request_limit * 100), 2) if quota.hourly_request_limit > 0 else 0,
                "monthly_reset_at": quota.monthly_reset_at,
                "daily_reset_at": quota.daily_reset_at,
                "hourly_reset_at": quota.hourly_reset_at,
                "enabled": quota.enabled,
                "soft_limit_enabled": quota.soft_limit_enabled,
                "soft_limit_percentage": quota.soft_limit_percentage,
                "created_by": quota.created_by,
                "updated_by": quota.updated_by,
                "created_at": quota.created_at,
                "updated_at": quota.updated_at,
            }

            response_quotas.append(QuotaResponse(**quota_dict))

        return response_quotas

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/overview", response_model=LimitsOverviewResponse)
async def get_limits_overview(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get overview of limits and quotas."""
    try:
        # Rate limits stats
        rate_limits_result = await db.execute(
            select(
                func.count(RateLimit.id).label("total_rate_limits"),
                func.sum(func.case((RateLimit.enabled == True, 1), else_=0)).label("active_rate_limits"),
            )
            .where(RateLimit.tenant_id == tenant_id if tenant_id else True)
        )
        rate_limits_stats = rate_limits_result.fetchone()

        # Breaches in last 24 hours
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)

        breaches_result = await db.execute(
            select(func.count(RateLimitBreach.id))
            .where(
                and_(
                    RateLimitBreach.breach_timestamp >= start_date,
                    RateLimitBreach.tenant_id == tenant_id if tenant_id else True
                )
            )
        )
        breached_limits_24h = breaches_result.scalar() or 0

        # Recent breaches
        recent_breaches_result = await db.execute(
            select(RateLimitBreach)
            .where(
                and_(
                    RateLimitBreach.breach_timestamp >= start_date,
                    RateLimitBreach.tenant_id == tenant_id if tenant_id else True
                )
            )
            .order_by(desc(RateLimitBreach.breach_timestamp))
            .limit(5)
        )
        recent_breaches = recent_breaches_result.scalars().all()

        # Quotas stats
        quotas_result = await db.execute(
            select(
                func.count(ApiQuota.id).label("total_quotas"),
                func.sum(
                    func.case(
                        (
                            func.greatest(
                                ApiQuota.monthly_usage / ApiQuota.monthly_request_limit,
                                ApiQuota.daily_usage / ApiQuota.daily_request_limit,
                                ApiQuota.hourly_usage / ApiQuota.hourly_request_limit
                            ) >= ApiQuota.soft_limit_percentage,
                            1
                        ),
                        else_=0
                    )
                ).label("quota_warnings"),
                func.sum(
                    func.case(
                        (
                            func.greatest(
                                ApiQuota.monthly_usage / ApiQuota.monthly_request_limit,
                                ApiQuota.daily_usage / ApiQuota.daily_request_limit,
                                ApiQuota.hourly_usage / ApiQuota.hourly_request_limit
                            ) >= 1.0,
                            1
                        ),
                        else_=0
                    )
                ).label("quota_exceeded"),
            )
            .where(ApiQuota.tenant_id == tenant_id if tenant_id else True)
        )
        quotas_stats = quotas_result.fetchone()

        return LimitsOverviewResponse(
            total_rate_limits=rate_limits_stats.total_rate_limits or 0,
            active_rate_limits=rate_limits_stats.active_rate_limits or 0,
            breached_limits_24h=breached_limits_24h,
            total_quotas=quotas_stats.total_quotas or 0,
            quota_warnings=quotas_stats.quota_warnings or 0,
            quota_exceeded=quotas_stats.quota_exceeded or 0,
            recent_breaches=[RateLimitBreachResponse.model_validate(breach) for breach in recent_breaches],
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
