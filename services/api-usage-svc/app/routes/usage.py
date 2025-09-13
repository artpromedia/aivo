"""API usage tracking endpoints."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import ApiUsage, RateLimit, RateLimitBreach

router = APIRouter(prefix="/usage", tags=["usage"])


# Response Models
class UsageStatsResponse(BaseModel):
    """Usage statistics response model."""

    tenant_id: str
    service_name: str
    route_path: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    total_bandwidth_bytes: int
    rate_limited_requests: int
    last_request_at: Optional[datetime]


class UsageSummaryResponse(BaseModel):
    """Usage summary response model."""

    total_requests: int
    total_tenants: int
    total_services: int
    total_routes: int
    average_response_time: float
    total_bandwidth_gb: float
    rate_limited_percentage: float
    top_services: List[Dict[str, Any]]
    top_routes: List[Dict[str, Any]]
    hourly_distribution: List[Dict[str, Any]]


class UsageDetailResponse(BaseModel):
    """Detailed usage response model."""

    id: str
    tenant_id: str
    service_name: str
    route_path: str
    method: str
    timestamp: datetime
    request_size_bytes: int
    response_size_bytes: int
    response_time_ms: float
    status_code: int
    user_id: Optional[str]
    client_ip: Optional[str]
    rate_limited: bool
    rate_limit_reason: Optional[str]

    class Config:
        from_attributes = True


class TimeSeriesPoint(BaseModel):
    """Time series data point."""

    timestamp: datetime
    value: float
    label: str


class TimeSeriesResponse(BaseModel):
    """Time series response model."""

    series: List[TimeSeriesPoint]
    metric: str
    time_range: str


@router.get("/stats", response_model=List[UsageStatsResponse])
async def get_usage_stats(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    route_path: Optional[str] = Query(None, description="Filter by route path"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    range_days: int = Query(30, ge=1, le=365, description="Range in days from now"),
    db: AsyncSession = Depends(get_db),
):
    """Get usage statistics with filtering."""
    try:
        # Calculate date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=range_days)

        # Build query filters
        filters = [
            ApiUsage.timestamp >= start_date,
            ApiUsage.timestamp <= end_date,
        ]

        if tenant_id:
            filters.append(ApiUsage.tenant_id == tenant_id)
        if service_name:
            filters.append(ApiUsage.service_name == service_name)
        if route_path:
            filters.append(ApiUsage.route_path.like(f"%{route_path}%"))

        # Query for aggregated stats
        result = await db.execute(
            select(
                ApiUsage.tenant_id,
                ApiUsage.service_name,
                ApiUsage.route_path,
                func.count(ApiUsage.id).label("total_requests"),
                func.sum(func.case((ApiUsage.status_code < 400, 1), else_=0)).label("successful_requests"),
                func.sum(func.case((ApiUsage.status_code >= 400, 1), else_=0)).label("failed_requests"),
                func.avg(ApiUsage.response_time_ms).label("average_response_time"),
                func.sum(ApiUsage.request_size_bytes + ApiUsage.response_size_bytes).label("total_bandwidth_bytes"),
                func.sum(func.case((ApiUsage.rate_limited == True, 1), else_=0)).label("rate_limited_requests"),
                func.max(ApiUsage.timestamp).label("last_request_at"),
            )
            .where(and_(*filters))
            .group_by(ApiUsage.tenant_id, ApiUsage.service_name, ApiUsage.route_path)
            .order_by(desc("total_requests"))
        )

        rows = result.fetchall()

        return [
            UsageStatsResponse(
                tenant_id=row.tenant_id,
                service_name=row.service_name,
                route_path=row.route_path,
                total_requests=row.total_requests or 0,
                successful_requests=row.successful_requests or 0,
                failed_requests=row.failed_requests or 0,
                average_response_time=float(row.average_response_time or 0),
                total_bandwidth_bytes=row.total_bandwidth_bytes or 0,
                rate_limited_requests=row.rate_limited_requests or 0,
                last_request_at=row.last_request_at,
            )
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    range_days: int = Query(30, ge=1, le=365, description="Range in days from now"),
    db: AsyncSession = Depends(get_db),
):
    """Get overall usage summary."""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=range_days)

        filters = [
            ApiUsage.timestamp >= start_date,
            ApiUsage.timestamp <= end_date,
        ]

        if tenant_id:
            filters.append(ApiUsage.tenant_id == tenant_id)

        # Overall stats
        result = await db.execute(
            select(
                func.count(ApiUsage.id).label("total_requests"),
                func.count(func.distinct(ApiUsage.tenant_id)).label("total_tenants"),
                func.count(func.distinct(ApiUsage.service_name)).label("total_services"),
                func.count(func.distinct(ApiUsage.route_path)).label("total_routes"),
                func.avg(ApiUsage.response_time_ms).label("average_response_time"),
                func.sum(ApiUsage.request_size_bytes + ApiUsage.response_size_bytes).label("total_bandwidth_bytes"),
                func.sum(func.case((ApiUsage.rate_limited == True, 1), else_=0)).label("rate_limited_requests"),
            )
            .where(and_(*filters))
        )

        summary = result.fetchone()

        # Top services
        top_services_result = await db.execute(
            select(
                ApiUsage.service_name,
                func.count(ApiUsage.id).label("request_count"),
            )
            .where(and_(*filters))
            .group_by(ApiUsage.service_name)
            .order_by(desc("request_count"))
            .limit(10)
        )

        top_services = [
            {"service_name": row.service_name, "request_count": row.request_count}
            for row in top_services_result.fetchall()
        ]

        # Top routes
        top_routes_result = await db.execute(
            select(
                ApiUsage.route_path,
                func.count(ApiUsage.id).label("request_count"),
            )
            .where(and_(*filters))
            .group_by(ApiUsage.route_path)
            .order_by(desc("request_count"))
            .limit(10)
        )

        top_routes = [
            {"route_path": row.route_path, "request_count": row.request_count}
            for row in top_routes_result.fetchall()
        ]

        # Hourly distribution
        hourly_result = await db.execute(
            select(
                func.extract("hour", ApiUsage.timestamp).label("hour"),
                func.count(ApiUsage.id).label("request_count"),
            )
            .where(and_(*filters))
            .group_by(func.extract("hour", ApiUsage.timestamp))
            .order_by("hour")
        )

        hourly_distribution = [
            {"hour": int(row.hour), "request_count": row.request_count}
            for row in hourly_result.fetchall()
        ]

        total_requests = summary.total_requests or 0
        rate_limited_requests = summary.rate_limited_requests or 0
        total_bandwidth_bytes = summary.total_bandwidth_bytes or 0

        return UsageSummaryResponse(
            total_requests=total_requests,
            total_tenants=summary.total_tenants or 0,
            total_services=summary.total_services or 0,
            total_routes=summary.total_routes or 0,
            average_response_time=float(summary.average_response_time or 0),
            total_bandwidth_gb=round(total_bandwidth_bytes / (1024**3), 2),
            rate_limited_percentage=round(
                (rate_limited_requests / total_requests * 100) if total_requests > 0 else 0, 2
            ),
            top_services=top_services,
            top_routes=top_routes,
            hourly_distribution=hourly_distribution,
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/details", response_model=List[UsageDetailResponse])
async def get_usage_details(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    route_path: Optional[str] = Query(None, description="Filter by route path"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status_code: Optional[int] = Query(None, description="Filter by status code"),
    rate_limited_only: bool = Query(False, description="Show only rate-limited requests"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    range_hours: int = Query(24, ge=1, le=168, description="Range in hours from now"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset results"),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed usage records."""
    try:
        # Calculate date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(hours=range_hours)

        # Build query filters
        filters = [
            ApiUsage.timestamp >= start_date,
            ApiUsage.timestamp <= end_date,
        ]

        if tenant_id:
            filters.append(ApiUsage.tenant_id == tenant_id)
        if service_name:
            filters.append(ApiUsage.service_name == service_name)
        if route_path:
            filters.append(ApiUsage.route_path.like(f"%{route_path}%"))
        if user_id:
            filters.append(ApiUsage.user_id == user_id)
        if status_code:
            filters.append(ApiUsage.status_code == status_code)
        if rate_limited_only:
            filters.append(ApiUsage.rate_limited == True)

        # Query for detailed records
        result = await db.execute(
            select(ApiUsage)
            .where(and_(*filters))
            .order_by(desc(ApiUsage.timestamp))
            .limit(limit)
            .offset(offset)
        )

        usage_records = result.scalars().all()

        return [UsageDetailResponse.model_validate(record) for record in usage_records]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/timeseries", response_model=TimeSeriesResponse)
async def get_usage_timeseries(
    metric: str = Query("requests", description="Metric to track: requests, response_time, bandwidth"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    granularity: str = Query("hour", description="Time granularity: hour, day"),
    range_days: int = Query(7, ge=1, le=30, description="Range in days from now"),
    db: AsyncSession = Depends(get_db),
):
    """Get time series data for usage metrics."""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=range_days)

        filters = [
            ApiUsage.timestamp >= start_date,
            ApiUsage.timestamp <= end_date,
        ]

        if tenant_id:
            filters.append(ApiUsage.tenant_id == tenant_id)
        if service_name:
            filters.append(ApiUsage.service_name == service_name)

        # Determine time grouping
        if granularity == "hour":
            time_group = func.date_trunc("hour", ApiUsage.timestamp)
        else:  # day
            time_group = func.date_trunc("day", ApiUsage.timestamp)

        # Determine metric aggregation
        if metric == "requests":
            metric_value = func.count(ApiUsage.id)
        elif metric == "response_time":
            metric_value = func.avg(ApiUsage.response_time_ms)
        elif metric == "bandwidth":
            metric_value = func.sum(ApiUsage.request_size_bytes + ApiUsage.response_size_bytes)
        else:
            raise HTTPException(status_code=400, detail="Invalid metric. Use: requests, response_time, bandwidth")

        # Query for time series data
        result = await db.execute(
            select(
                time_group.label("time_bucket"),
                metric_value.label("value"),
            )
            .where(and_(*filters))
            .group_by(time_group)
            .order_by(time_group)
        )

        rows = result.fetchall()

        series = [
            TimeSeriesPoint(
                timestamp=row.time_bucket,
                value=float(row.value or 0),
                label=row.time_bucket.strftime("%Y-%m-%d %H:%M" if granularity == "hour" else "%Y-%m-%d"),
            )
            for row in rows
        ]

        return TimeSeriesResponse(
            series=series,
            metric=metric,
            time_range=f"{range_days}d",
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/record", status_code=status.HTTP_201_CREATED)
async def record_api_usage(
    tenant_id: str,
    service_name: str,
    route_path: str,
    method: str,
    status_code: int,
    response_time_ms: float = 0.0,
    request_size_bytes: int = 0,
    response_size_bytes: int = 0,
    user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    rate_limited: bool = False,
    rate_limit_reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Record API usage (for internal use by API gateways)."""
    try:
        usage_record = ApiUsage(
            tenant_id=tenant_id,
            service_name=service_name,
            route_path=route_path,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent,
            rate_limited=rate_limited,
            rate_limit_reason=rate_limit_reason,
        )

        db.add(usage_record)
        await db.commit()

        return {"status": "recorded", "id": usage_record.id}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
