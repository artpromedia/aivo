"""
Data export API endpoints.

GDPR Article 20 compliant data portability with 10 days requirement.
"""

from datetime import datetime
from uuid import UUID

from config import get_db
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExportFormat, ExportStatus
from app.services import DataExportService
from app.tasks import process_data_export

router = APIRouter()


# Request/Response models
class ExportRequest(BaseModel):
    """Request model for data export."""

    user_id: str = Field(..., description="User identifier")
    export_format: ExportFormat = Field(ExportFormat.JSON, description="Export format")
    include_consent_history: bool = Field(True, description="Include consent history")
    include_audit_logs: bool = Field(False, description="Include audit logs")
    metadata: dict | None = Field(None, description="Additional metadata")

    @validator("user_id")
    def validate_user_id(self, v):
        """Validate user ID format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("User ID cannot be empty")
        return v.strip()


class ExportResponse(BaseModel):
    """Response model for export requests."""

    id: UUID
    user_id: str
    status: ExportStatus
    export_format: ExportFormat
    file_size_bytes: int | None
    file_path: str | None
    download_url: str | None
    expires_at: datetime
    created_at: datetime
    completed_at: datetime | None
    progress_percentage: int

    class Config:
        from_attributes = True


class ExportListResponse(BaseModel):
    """Response model for export list."""

    exports: list[ExportResponse]
    total: int
    page: int
    per_page: int


def get_export_service(db: AsyncSession = Depends(get_db)) -> DataExportService:
    """Get data export service instance."""
    return DataExportService(db)


def create_download_url(export_id: UUID) -> str:
    """Create download URL for export."""
    return f"/api/v1/export/{export_id}/download"


@router.post("/", response_model=ExportResponse, status_code=201)
async def create_export_request(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    export_service: DataExportService = Depends(get_export_service),
):
    """
    Create a new data export request.

    Initiates GDPR Article 20 data export with 10 days completion requirement.
    """
    try:
        export_request = await export_service.create_export_request(
            user_id=request.user_id,
            export_format=request.export_format,
            include_consent_history=request.include_consent_history,
            include_audit_logs=request.include_audit_logs,
            metadata=request.metadata or {},
        )

        # Start background processing
        background_tasks.add_task(process_data_export.delay, str(export_request.id))

        response = ExportResponse.from_orm(export_request)
        if export_request.status == ExportStatus.COMPLETED:
            response.download_url = create_download_url(export_request.id)

        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create export request")


@router.get("/user/{user_id}", response_model=ExportListResponse)
async def get_user_exports(
    user_id: str,
    status: ExportStatus | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page"),
    export_service: DataExportService = Depends(get_export_service),
):
    """
    Get export requests for a user.

    Returns paginated list of export requests with optional status filtering.
    """
    try:
        exports, total = await export_service.get_user_exports(
            user_id=user_id, status=status, limit=per_page, offset=(page - 1) * per_page
        )

        export_responses = []
        for export in exports:
            response = ExportResponse.from_orm(export)
            if export.status == ExportStatus.COMPLETED and export.file_path:
                response.download_url = create_download_url(export.id)
            export_responses.append(response)

        return ExportListResponse(
            exports=export_responses, total=total, page=page, per_page=per_page
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve exports")


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export_request(
    export_id: UUID, export_service: DataExportService = Depends(get_export_service)
):
    """
    Get specific export request by ID.

    Returns detailed export information including status and download URL.
    """
    try:
        export = await export_service.get_export_request(export_id)
        if not export:
            raise HTTPException(status_code=404, detail="Export request not found")

        response = ExportResponse.from_orm(export)
        if export.status == ExportStatus.COMPLETED and export.file_path:
            response.download_url = create_download_url(export.id)

        return response
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve export")


@router.get("/{export_id}/download")
async def download_export(
    export_id: UUID, export_service: DataExportService = Depends(get_export_service)
):
    """
    Download completed export file.

    Returns the export file as a downloadable response.
    """
    try:
        export = await export_service.get_export_request(export_id)
        if not export:
            raise HTTPException(status_code=404, detail="Export request not found")

        if export.status != ExportStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Export not completed")

        if not export.file_path or not await export_service.file_exists(export.file_path):
            raise HTTPException(status_code=404, detail="Export file not found")

        # Determine filename and media type
        filename = f"data_export_{export.user_id}_{export.created_at.strftime('%Y%m%d')}"
        if export.export_format == ExportFormat.JSON:
            filename += ".json"
            media_type = "application/json"
        elif export.export_format == ExportFormat.CSV:
            filename += ".csv"
            media_type = "text/csv"
        else:  # ZIP
            filename += ".zip"
            media_type = "application/zip"

        return FileResponse(
            path=export.file_path,
            filename=filename,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Export-ID": str(export.id),
                "X-Export-Date": export.created_at.isoformat(),
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to download export")


@router.delete("/{export_id}", status_code=204)
async def cancel_export_request(
    export_id: UUID, export_service: DataExportService = Depends(get_export_service)
):
    """
    Cancel pending export request.

    Cancels export if still pending, removes file if completed.
    """
    try:
        success = await export_service.cancel_export_request(export_id)
        if not success:
            raise HTTPException(status_code=404, detail="Export request not found")

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to cancel export")


@router.get("/")
async def list_all_exports(
    status: ExportStatus | None = Query(None, description="Filter by status"),
    overdue_only: bool = Query(False, description="Show only overdue exports"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    export_service: DataExportService = Depends(get_export_service),
):
    """
    List all export requests (admin endpoint).

    Returns paginated list of all export requests with filtering options.
    """
    try:
        exports, total = await export_service.list_all_exports(
            status=status, overdue_only=overdue_only, limit=per_page, offset=(page - 1) * per_page
        )

        export_responses = []
        for export in exports:
            response = ExportResponse.from_orm(export)
            if export.status == ExportStatus.COMPLETED and export.file_path:
                response.download_url = create_download_url(export.id)
            export_responses.append(response)

        return ExportListResponse(
            exports=export_responses, total=total, page=page, per_page=per_page
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list exports")


@router.get("/stats/summary")
async def get_export_statistics(export_service: DataExportService = Depends(get_export_service)):
    """
    Get export statistics and metrics.

    Returns summary of export requests by status and performance metrics.
    """
    try:
        stats = await export_service.get_export_statistics()
        return stats
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get export statistics")


@router.post("/{export_id}/retry", response_model=ExportResponse)
async def retry_failed_export(
    export_id: UUID,
    background_tasks: BackgroundTasks,
    export_service: DataExportService = Depends(get_export_service),
):
    """
    Retry failed export request.

    Resets failed export to pending and starts processing again.
    """
    try:
        export = await export_service.retry_export_request(export_id)
        if not export:
            raise HTTPException(status_code=404, detail="Export request not found or not failed")

        # Start background processing
        background_tasks.add_task(process_data_export.delay, str(export.id))

        return ExportResponse.from_orm(export)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retry export")
