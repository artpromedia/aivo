"""Export endpoints for audit log data export functionality."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database import get_db, get_readonly_db
from app.models.export_job import ExportFormat, ExportJob, ExportStatus
from app.services.export_service import ExportService

logger = structlog.get_logger(__name__)
router = APIRouter()
export_service = ExportService()


# Pydantic schemas
class ExportJobCreate(BaseModel):
    """Schema for creating an export job."""

    job_name: str = Field(..., min_length=1, max_length=255, description="Name for the export job")
    export_format: ExportFormat = Field(..., description="Export format (csv, json, xlsx)")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Filter criteria")
    start_date: Optional[datetime] = Field(None, description="Start date for export range")
    end_date: Optional[datetime] = Field(None, description="End date for export range")


class ExportJobResponse(BaseModel):
    """Schema for export job response."""

    id: UUID
    job_name: str
    requested_by: str
    status: ExportStatus
    export_format: ExportFormat
    filters: Optional[Dict[str, Any]]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    total_records: Optional[int]
    file_size_bytes: Optional[int]
    download_url: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ExportJobList(BaseModel):
    """Schema for export job list response."""

    jobs: List[ExportJobResponse]
    pagination: Dict[str, Any]


@router.post("/export", response_model=ExportJobResponse, status_code=status.HTTP_201_CREATED)
async def create_export_job(
    export_data: ExportJobCreate,
    requested_by: str = Query(..., description="User ID requesting the export"),
    db: AsyncSession = Depends(get_db),
) -> ExportJobResponse:
    """Create a new audit log export job."""
    try:
        # Validate export format
        if export_data.export_format not in [ExportFormat.CSV, ExportFormat.JSON, ExportFormat.XLSX]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {export_data.export_format}"
            )

        # Create export job
        export_job = await export_service.create_export_job(
            db=db,
            job_name=export_data.job_name,
            requested_by=requested_by,
            export_format=export_data.export_format,
            filters=export_data.filters,
            start_date=export_data.start_date,
            end_date=export_data.end_date,
        )

        logger.info(
            "Export job created",
            job_id=str(export_job.id),
            requested_by=requested_by,
            format=export_data.export_format,
        )

        return ExportJobResponse.model_validate(export_job)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create export job", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create export job"
        )


@router.get("/export", response_model=ExportJobList)
async def list_export_jobs(
    requested_by: Optional[str] = Query(None, description="Filter by requester"),
    status_filter: Optional[ExportStatus] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_readonly_db),
) -> ExportJobList:
    """List export jobs with filtering and pagination."""
    try:
        result = await export_service.get_export_jobs(
            db=db,
            requested_by=requested_by,
            status=status_filter,
            page=page,
            page_size=page_size,
        )

        return ExportJobList(
            jobs=[ExportJobResponse.model_validate(job) for job in result["jobs"]],
            pagination=result["pagination"],
        )

    except Exception as e:
        logger.error("Failed to list export jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list export jobs"
        )


@router.get("/export/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_readonly_db),
) -> ExportJobResponse:
    """Get a specific export job by ID."""
    from sqlalchemy import select

    try:
        stmt = select(ExportJob).where(ExportJob.id == job_id)
        result = await db.execute(stmt)
        export_job = result.scalar_one_or_none()

        if not export_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export job not found"
            )

        return ExportJobResponse.model_validate(export_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get export job", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get export job"
        )


@router.get("/export/{job_id}/download")
async def download_export(
    job_id: UUID,
    db: AsyncSession = Depends(get_readonly_db),
) -> Dict[str, Any]:
    """Get download information for a completed export job."""
    from sqlalchemy import select

    try:
        stmt = select(ExportJob).where(ExportJob.id == job_id)
        result = await db.execute(stmt)
        export_job = result.scalar_one_or_none()

        if not export_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export job not found"
            )

        if export_job.status != ExportStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Export job not completed. Current status: {export_job.status}"
            )

        if export_job.is_expired:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Export download link has expired"
            )

        if not export_job.download_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Download URL not available"
            )

        return {
            "download_url": export_job.download_url,
            "expires_at": export_job.expires_at.isoformat() if export_job.expires_at else None,
            "file_size_bytes": export_job.file_size_bytes,
            "total_records": export_job.total_records,
            "format": export_job.export_format,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get download info", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get download information"
        )


@router.get("/export/formats")
async def get_export_formats() -> Dict[str, Any]:
    """Get available export formats and their descriptions."""
    return {
        "formats": [
            {
                "value": ExportFormat.CSV,
                "name": "CSV",
                "description": "Comma-separated values format",
                "mime_type": "text/csv",
                "file_extension": "csv",
            },
            {
                "value": ExportFormat.JSON,
                "name": "JSON",
                "description": "JavaScript Object Notation format",
                "mime_type": "application/json",
                "file_extension": "json",
            },
            {
                "value": ExportFormat.XLSX,
                "name": "Excel",
                "description": "Microsoft Excel format",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "file_extension": "xlsx",
            },
        ]
    }
