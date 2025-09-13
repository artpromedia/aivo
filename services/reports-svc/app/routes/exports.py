"""Exports API routes."""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import uuid
import io

from ..database import database, exports_table, reports_table, schedules_table
from ..schemas import Export, ExportCreate, ExportListResponse
from ..services.auth_service import get_current_tenant
from ..services.export_service import ExportService

router = APIRouter()
export_service = ExportService()

@router.get("/", response_model=ExportListResponse)
async def list_exports(
    tenant_id: str = Depends(get_current_tenant),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    report_id: Optional[UUID] = Query(None),
    schedule_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None)
):
    """List exports for a tenant with pagination and filtering."""
    offset = (page - 1) * per_page

    # Build query conditions
    conditions = [exports_table.c.tenant_id == tenant_id]

    if report_id:
        conditions.append(exports_table.c.report_id == report_id)

    if schedule_id:
        conditions.append(exports_table.c.schedule_id == schedule_id)

    if status:
        conditions.append(exports_table.c.status == status)

    # Count total
    count_query = f"""
        SELECT COUNT(*) FROM exports
        WHERE {" AND ".join([str(c) for c in conditions])}
    """
    total = await database.fetch_val(count_query)

    # Fetch exports
    query = exports_table.select().where(*conditions).order_by(
        exports_table.c.created_at.desc()
    ).offset(offset).limit(per_page)

    exports = await database.fetch_all(query)

    return ExportListResponse(
        exports=[Export(**dict(export)) for export in exports],
        total=total,
        page=page,
        per_page=per_page
    )

@router.post("/", response_model=Export)
async def create_export(
    export: ExportCreate,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new export job."""
    # Verify report exists
    report = await database.fetch_one(
        reports_table.select().where(
            reports_table.c.id == export.report_id,
            reports_table.c.tenant_id == tenant_id
        )
    )

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Verify schedule exists if provided
    if export.schedule_id:
        schedule = await database.fetch_one(
            schedules_table.select().where(
                schedules_table.c.id == export.schedule_id,
                schedules_table.c.tenant_id == tenant_id
            )
        )

        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

    export_data = export.dict()
    export_data["id"] = uuid.uuid4()
    export_data["tenant_id"] = tenant_id
    export_data["status"] = "pending"

    query = exports_table.insert().values(**export_data)
    await database.execute(query)

    # Start export processing in background
    background_tasks.add_task(
        _process_export,
        export_data["id"]
    )

    # Fetch and return created export
    created_export = await database.fetch_one(
        exports_table.select().where(exports_table.c.id == export_data["id"])
    )

    return Export(**dict(created_export))

@router.get("/{export_id}", response_model=Export)
async def get_export(
    export_id: UUID,
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a specific export."""
    query = exports_table.select().where(
        exports_table.c.id == export_id,
        exports_table.c.tenant_id == tenant_id
    )

    export = await database.fetch_one(query)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")

    return Export(**dict(export))

@router.get("/{export_id}/download")
async def download_export(
    export_id: UUID,
    tenant_id: str = Depends(get_current_tenant)
):
    """Download an export file."""
    # Get export details
    export = await database.fetch_one(
        exports_table.select().where(
            exports_table.c.id == export_id,
            exports_table.c.tenant_id == tenant_id
        )
    )

    if not export:
        raise HTTPException(status_code=404, detail="Export not found")

    if export["status"] != "completed":
        raise HTTPException(status_code=400, detail="Export not completed")

    if export["expires_at"] and export["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Download link expired")

    try:
        # Get file content from storage (S3 or local)
        file_content, content_type, filename = await export_service.get_export_file(
            export["file_path"],
            export["format"]
        )

        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@router.delete("/{export_id}")
async def delete_export(
    export_id: UUID,
    tenant_id: str = Depends(get_current_tenant)
):
    """Delete an export and its associated file."""
    # Check if export exists
    export = await database.fetch_one(
        exports_table.select().where(
            exports_table.c.id == export_id,
            exports_table.c.tenant_id == tenant_id
        )
    )

    if not export:
        raise HTTPException(status_code=404, detail="Export not found")

    # Delete file from storage if it exists
    if export["file_path"]:
        try:
            await export_service.delete_export_file(export["file_path"])
        except Exception as e:
            # Log error but continue with database deletion
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to delete export file",
                         export_id=str(export_id),
                         file_path=export["file_path"],
                         error=str(e))

    # Delete export record
    query = exports_table.delete().where(
        exports_table.c.id == export_id,
        exports_table.c.tenant_id == tenant_id
    )

    await database.execute(query)

    return {"message": "Export deleted successfully"}

@router.post("/{export_id}/retry", response_model=Export)
async def retry_export(
    export_id: UUID,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant)
):
    """Retry a failed export."""
    # Get export details
    export = await database.fetch_one(
        exports_table.select().where(
            exports_table.c.id == export_id,
            exports_table.c.tenant_id == tenant_id
        )
    )

    if not export:
        raise HTTPException(status_code=404, detail="Export not found")

    if export["status"] not in ["failed"]:
        raise HTTPException(status_code=400, detail="Only failed exports can be retried")

    # Reset export status and clear error
    update_data = {
        "status": "pending",
        "error_message": None,
        "file_path": None,
        "file_size": None,
        "download_url": None,
        "expires_at": None,
        "completed_at": None
    }

    query = exports_table.update().where(
        exports_table.c.id == export_id,
        exports_table.c.tenant_id == tenant_id
    ).values(**update_data)

    await database.execute(query)

    # Start export processing in background
    background_tasks.add_task(_process_export, export_id)

    # Return updated export
    updated_export = await database.fetch_one(
        exports_table.select().where(exports_table.c.id == export_id)
    )

    return Export(**dict(updated_export))

@router.get("/stats/summary")
async def get_export_stats(
    tenant_id: str = Depends(get_current_tenant),
    days: int = Query(30, ge=1, le=365)
):
    """Get export statistics for the tenant."""
    from_date = datetime.utcnow() - timedelta(days=days)

    # Query export statistics
    stats_query = f"""
    SELECT
        status,
        format,
        COUNT(*) as count,
        AVG(file_size) as avg_file_size,
        AVG(execution_time_ms) as avg_execution_time,
        SUM(CASE WHEN schedule_id IS NOT NULL THEN 1 ELSE 0 END) as scheduled_count
    FROM exports
    WHERE tenant_id = '{tenant_id}'
    AND created_at >= '{from_date}'
    GROUP BY status, format
    ORDER BY status, format
    """

    stats = await database.fetch_all(stats_query)

    # Summary statistics
    summary_query = f"""
    SELECT
        COUNT(*) as total_exports,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_exports,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_exports,
        SUM(file_size) as total_file_size,
        AVG(execution_time_ms) as avg_execution_time
    FROM exports
    WHERE tenant_id = '{tenant_id}'
    AND created_at >= '{from_date}'
    """

    summary = await database.fetch_one(summary_query)

    return {
        "period_days": days,
        "summary": dict(summary) if summary else {},
        "by_status_format": [dict(stat) for stat in stats]
    }

# Background task functions
async def _process_export(export_id: UUID):
    """Process an export job in the background."""
    import structlog
    logger = structlog.get_logger()

    try:
        # Update status to processing
        await database.execute(
            exports_table.update().where(
                exports_table.c.id == export_id
            ).values(status="processing")
        )

        # Get export and report details
        export_query = f"""
        SELECT e.*, r.query_config, r.row_limit, r.name as report_name
        FROM exports e
        JOIN reports r ON e.report_id = r.id
        WHERE e.id = '{export_id}'
        """

        export_data = await database.fetch_one(export_query)
        if not export_data:
            raise Exception("Export or report not found")

        # Execute the export
        result = await export_service.generate_export(
            export_id=export_id,
            query_config=export_data["query_config"],
            format=export_data["format"],
            tenant_id=export_data["tenant_id"],
            report_name=export_data["report_name"],
            row_limit=export_data["row_limit"]
        )

        # Update export with success details
        update_data = {
            "status": "completed",
            "file_path": result["file_path"],
            "file_size": result["file_size"],
            "row_count": result["row_count"],
            "download_url": result["download_url"],
            "expires_at": result["expires_at"],
            "execution_time_ms": result["execution_time_ms"],
            "completed_at": datetime.utcnow()
        }

        await database.execute(
            exports_table.update().where(
                exports_table.c.id == export_id
            ).values(**update_data)
        )

        logger.info("Export completed successfully", export_id=str(export_id))

    except Exception as e:
        # Update export with failure details
        await database.execute(
            exports_table.update().where(
                exports_table.c.id == export_id
            ).values(
                status="failed",
                error_message=str(e),
                completed_at=datetime.utcnow()
            )
        )

        logger.error("Export failed", export_id=str(export_id), error=str(e))
