"""Reports API routes."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
import uuid

from ..database import database, reports_table, query_templates_table
from ..schemas import (
    Report, ReportCreate, ReportUpdate, ReportListResponse,
    QueryPreviewResponse, QueryTemplate, QueryConfig
)
from ..services.query_service import QueryService
from ..services.auth_service import get_current_tenant

router = APIRouter()
query_service = QueryService()

@router.get("/", response_model=ReportListResponse)
async def list_reports(
    tenant_id: str = Depends(get_current_tenant),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    public_only: bool = Query(False)
):
    """List reports for a tenant with pagination and filtering."""
    offset = (page - 1) * per_page

    # Build query conditions
    conditions = [reports_table.c.tenant_id == tenant_id]

    if public_only:
        conditions.append(reports_table.c.is_public == True)

    if search:
        conditions.append(reports_table.c.name.ilike(f"%{search}%"))

    if tags:
        # PostgreSQL JSONB query for array overlap
        conditions.append(reports_table.c.tags.op("&&")(tags))

    # Count total
    count_query = f"""
        SELECT COUNT(*) FROM reports
        WHERE {" AND ".join([str(c) for c in conditions])}
    """
    total = await database.fetch_val(count_query)

    # Fetch reports
    query = reports_table.select().where(*conditions).order_by(
        reports_table.c.updated_at.desc()
    ).offset(offset).limit(per_page)

    reports = await database.fetch_all(query)

    return ReportListResponse(
        reports=[Report(**dict(report)) for report in reports],
        total=total,
        page=page,
        per_page=per_page
    )

@router.post("/", response_model=Report)
async def create_report(
    report: ReportCreate,
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new report."""
    # Validate query configuration
    try:
        query_config = QueryConfig(**report.query_config)
        await query_service.validate_query(query_config, tenant_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid query configuration: {str(e)}")

    report_data = report.dict()
    report_data["id"] = uuid.uuid4()
    report_data["tenant_id"] = tenant_id

    query = reports_table.insert().values(**report_data)
    await database.execute(query)

    # Fetch and return created report
    created_report = await database.fetch_one(
        reports_table.select().where(reports_table.c.id == report_data["id"])
    )

    return Report(**dict(created_report))

@router.get("/{report_id}", response_model=Report)
async def get_report(
    report_id: UUID,
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a specific report."""
    query = reports_table.select().where(
        reports_table.c.id == report_id,
        reports_table.c.tenant_id == tenant_id
    )

    report = await database.fetch_one(query)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return Report(**dict(report))

@router.put("/{report_id}", response_model=Report)
async def update_report(
    report_id: UUID,
    report_update: ReportUpdate,
    tenant_id: str = Depends(get_current_tenant)
):
    """Update a report."""
    # Check if report exists
    existing_report = await database.fetch_one(
        reports_table.select().where(
            reports_table.c.id == report_id,
            reports_table.c.tenant_id == tenant_id
        )
    )

    if not existing_report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Validate query configuration if provided
    update_data = report_update.dict(exclude_unset=True)
    if "query_config" in update_data:
        try:
            query_config = QueryConfig(**update_data["query_config"])
            await query_service.validate_query(query_config, tenant_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid query configuration: {str(e)}")

    # Update report
    query = reports_table.update().where(
        reports_table.c.id == report_id,
        reports_table.c.tenant_id == tenant_id
    ).values(**update_data)

    await database.execute(query)

    # Fetch and return updated report
    updated_report = await database.fetch_one(
        reports_table.select().where(reports_table.c.id == report_id)
    )

    return Report(**dict(updated_report))

@router.delete("/{report_id}")
async def delete_report(
    report_id: UUID,
    tenant_id: str = Depends(get_current_tenant)
):
    """Delete a report."""
    # Check if report exists
    existing_report = await database.fetch_one(
        reports_table.select().where(
            reports_table.c.id == report_id,
            reports_table.c.tenant_id == tenant_id
        )
    )

    if not existing_report:
        raise HTTPException(status_code=404, detail="Report not found")

    # TODO: Check if report has active schedules and handle accordingly

    # Delete report
    query = reports_table.delete().where(
        reports_table.c.id == report_id,
        reports_table.c.tenant_id == tenant_id
    )

    await database.execute(query)

    return {"message": "Report deleted successfully"}

@router.post("/{report_id}/preview", response_model=QueryPreviewResponse)
async def preview_report(
    report_id: UUID,
    filters: Optional[dict] = None,
    limit: int = Query(100, ge=1, le=1000),
    tenant_id: str = Depends(get_current_tenant)
):
    """Preview report data with optional filters."""
    # Get report
    report = await database.fetch_one(
        reports_table.select().where(
            reports_table.c.id == report_id,
            reports_table.c.tenant_id == tenant_id
        )
    )

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Execute query with preview limit
    try:
        query_config = QueryConfig(**report["query_config"])

        # Apply additional filters if provided
        if filters:
            if query_config.filters:
                query_config.filters.extend(filters.get("filters", []))
            else:
                query_config.filters = filters.get("filters", [])

        # Override limit for preview
        query_config.limit = limit

        result = await query_service.execute_query(query_config, tenant_id)

        return QueryPreviewResponse(
            data=result["data"],
            columns=result["columns"],
            total_rows=result["total_rows"],
            execution_time_ms=result["execution_time_ms"]
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")

@router.get("/templates/", response_model=List[QueryTemplate])
async def list_query_templates(
    category: Optional[str] = Query(None),
    tenant_id: str = Depends(get_current_tenant)
):
    """List available query templates."""
    conditions = []

    # Include system templates and user templates for this tenant
    conditions.append(
        (query_templates_table.c.is_system == True) |
        (query_templates_table.c.created_by == tenant_id)
    )

    if category:
        conditions.append(query_templates_table.c.category == category)

    query = query_templates_table.select().where(*conditions).order_by(
        query_templates_table.c.name
    )

    templates = await database.fetch_all(query)

    return [QueryTemplate(**dict(template)) for template in templates]

@router.post("/validate-query", response_model=dict)
async def validate_query(
    query_config: QueryConfig,
    tenant_id: str = Depends(get_current_tenant)
):
    """Validate a query configuration without executing it."""
    try:
        await query_service.validate_query(query_config, tenant_id)
        return {"valid": True, "message": "Query configuration is valid"}
    except Exception as e:
        return {"valid": False, "message": str(e)}
