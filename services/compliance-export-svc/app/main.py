"""
FastAPI application for compliance export service.
Provides admin download page, job management, and RPO/RTO 5 min export processing.
"""

import uuid
from datetime import datetime
from typing import Any

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .audit import AuditLogger
from .crypto import encryption_manager
from .jobs import (
    cleanup_old_exports,
    generate_compliance_report,
    process_compliance_export,
    validate_export_data,
)
from .models import ExportFormat, ExportJob, ExportStatus

# Setup structured logging
logger = structlog.get_logger()

# Database setup
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/compliance_db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# FastAPI app
app = FastAPI(
    title="Compliance Export Service",
    description="State-format exports with audit logs and encryption at rest",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates for admin pages
templates = Jinja2Templates(directory="templates")


# Dependency for database session
async def get_db_session() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Pydantic models for API
class ExportJobRequest(BaseModel):
    """Request model for creating export jobs."""

    format: ExportFormat = Field(..., description="Export format")
    name: str = Field(..., description="Job name")
    description: str | None = Field(None, description="Job description")
    school_year: str = Field(..., description="Academic year (e.g., 2023-24)")
    state_code: str = Field(..., description="State code (e.g., CA, TX)")
    district_id: str | None = Field(None, description="District ID filter")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Export parameters")


class ExportJobResponse(BaseModel):
    """Response model for export jobs."""

    id: str
    format: str
    status: str
    name: str
    description: str | None
    school_year: str
    state_code: str
    district_id: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    created_by: str
    progress_percentage: int
    total_records: int | None
    processed_records: int | None
    file_size: int | None
    error_message: str | None


class AuditLogResponse(BaseModel):
    """Response model for audit logs."""

    id: str
    export_job_id: str
    action: str
    timestamp: datetime
    user_id: str
    ip_address: str | None
    details: dict[str, Any]


class ValidationResponse(BaseModel):
    """Response model for data validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    record_counts: dict[str, int]


# API Endpoints


@app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Compliance Export Dashboard"},
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/exports", response_model=ExportJobResponse)
async def create_export_job(
    job_request: ExportJobRequest,
    user_id: str = "system",  # TODO: Get from authentication
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new compliance export job."""
    try:
        # Create export job
        export_job = ExportJob(
            format=job_request.format,
            name=job_request.name,
            description=job_request.description,
            school_year=job_request.school_year,
            state_code=job_request.state_code,
            district_id=job_request.district_id,
            parameters=job_request.parameters,
            created_by=user_id,
        )

        db.add(export_job)
        await db.flush()

        # Log job creation
        audit_logger = AuditLogger(db)
        await audit_logger.log_export_created(export_job, user_id)
        await db.commit()

        # Start background processing
        process_compliance_export.delay(
            str(export_job.id),
            job_request.format.value,
            job_request.parameters,
            user_id,
        )

        logger.info(
            "Export job created", job_id=str(export_job.id), format=job_request.format.value
        )

        return ExportJobResponse(
            id=str(export_job.id),
            format=export_job.format.value,
            status=export_job.status.value,
            name=export_job.name,
            description=export_job.description,
            school_year=export_job.school_year,
            state_code=export_job.state_code,
            district_id=export_job.district_id,
            created_at=export_job.created_at,
            started_at=export_job.started_at,
            completed_at=export_job.completed_at,
            created_by=export_job.created_by,
            progress_percentage=export_job.progress_percentage,
            total_records=export_job.total_records,
            processed_records=export_job.processed_records,
            file_size=export_job.file_size,
            error_message=export_job.error_message,
        )

    except Exception as e:
        logger.error("Failed to create export job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create export job: {str(e)}")


@app.get("/api/exports", response_model=list[ExportJobResponse])
async def list_export_jobs(
    status: ExportStatus | None = None,
    format: ExportFormat | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """List export jobs with optional filtering."""
    try:
        # Build query conditions
        conditions = []
        if status:
            conditions.append(ExportJob.status == status)
        if format:
            conditions.append(ExportJob.format == format)

        # Execute query
        query = select(ExportJob).order_by(desc(ExportJob.created_at))
        if conditions:
            query = query.where(and_(*conditions))
        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        jobs = result.scalars().all()

        return [
            ExportJobResponse(
                id=str(job.id),
                format=job.format.value,
                status=job.status.value,
                name=job.name,
                description=job.description,
                school_year=job.school_year,
                state_code=job.state_code,
                district_id=job.district_id,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                created_by=job.created_by,
                progress_percentage=job.progress_percentage,
                total_records=job.total_records,
                processed_records=job.processed_records,
                file_size=job.file_size,
                error_message=job.error_message,
            )
            for job in jobs
        ]

    except Exception as e:
        logger.error("Failed to list export jobs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list export jobs: {str(e)}")


@app.get("/api/exports/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Get export job by ID."""
    try:
        job_uuid = uuid.UUID(job_id)
        stmt = select(ExportJob).where(ExportJob.id == job_uuid)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")

        return ExportJobResponse(
            id=str(job.id),
            format=job.format.value,
            status=job.status.value,
            name=job.name,
            description=job.description,
            school_year=job.school_year,
            state_code=job.state_code,
            district_id=job.district_id,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_by=job.created_by,
            progress_percentage=job.progress_percentage,
            total_records=job.total_records,
            processed_records=job.processed_records,
            file_size=job.file_size,
            error_message=job.error_message,
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error("Failed to get export job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get export job: {str(e)}")


@app.get("/api/exports/{job_id}/download")
async def download_export_file(
    job_id: str,
    user_id: str = "system",  # TODO: Get from authentication
    db: AsyncSession = Depends(get_db_session),
):
    """Download exported file (decrypted)."""
    try:
        job_uuid = uuid.UUID(job_id)
        stmt = select(ExportJob).where(ExportJob.id == job_uuid)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")

        if job.status != ExportStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Export job not completed")

        if not job.encrypted_file_path:
            raise HTTPException(status_code=404, detail="Export file not found")

        # Get encryption key
        from .models import EncryptionKey

        key_stmt = select(EncryptionKey).where(EncryptionKey.key_id == job.encryption_key_id)
        key_result = await db.execute(key_stmt)
        encryption_key = key_result.scalar_one_or_none()

        if not encryption_key:
            raise HTTPException(status_code=500, detail="Encryption key not found")

        # Decrypt file to temporary location
        import tempfile
        from pathlib import Path

        encrypted_path = Path(job.encrypted_file_path)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        # Reconstruct key data (simplified)
        key_data = encryption_key.salt + encryption_key.encrypted_key

        # Decrypt file
        encryption_manager.decrypt_file(encrypted_path, temp_path, key_data)

        # Log download
        audit_logger = AuditLogger(db)
        await audit_logger.log_export_downloaded(job.id, user_id)
        await db.commit()

        # Generate filename
        format_name = job.format.value.lower()
        timestamp = job.created_at.strftime("%Y%m%d_%H%M%S")
        filename = f"{format_name}_export_{timestamp}.csv"

        return FileResponse(
            path=str(temp_path),
            filename=filename,
            media_type="text/csv",
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error("Failed to download export file", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@app.delete("/api/exports/{job_id}")
async def delete_export_job(
    job_id: str,
    user_id: str = "system",  # TODO: Get from authentication
    db: AsyncSession = Depends(get_db_session),
):
    """Delete export job and associated files."""
    try:
        job_uuid = uuid.UUID(job_id)
        stmt = select(ExportJob).where(ExportJob.id == job_uuid)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")

        # Delete files
        from pathlib import Path

        if job.encrypted_file_path:
            encrypted_path = Path(job.encrypted_file_path)
            if encrypted_path.exists():
                encryption_manager.secure_delete(encrypted_path)

        if job.file_path:
            original_path = Path(job.file_path)
            if original_path.exists():
                encryption_manager.secure_delete(original_path)

        # Log deletion
        audit_logger = AuditLogger(db)
        await audit_logger.log_export_deleted(job.id, user_id, "Manual deletion")

        # Update job status
        job.status = ExportStatus.CANCELLED
        await db.commit()

        logger.info("Export job deleted", job_id=job_id)

        return {"message": "Export job deleted successfully"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error("Failed to delete export job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete export job: {str(e)}")


@app.get("/api/exports/{job_id}/audit", response_model=list[AuditLogResponse])
async def get_export_audit_logs(
    job_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Get audit logs for export job."""
    try:
        from .models import AuditLog

        job_uuid = uuid.UUID(job_id)
        stmt = (
            select(AuditLog)
            .where(AuditLog.export_job_id == job_uuid)
            .order_by(desc(AuditLog.timestamp))
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()

        return [
            AuditLogResponse(
                id=str(log.id),
                export_job_id=str(log.export_job_id),
                action=log.action.value,
                timestamp=log.timestamp,
                user_id=log.user_id,
                ip_address=log.ip_address,
                details=log.details,
            )
            for log in logs
        ]

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error("Failed to get audit logs", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")


@app.post("/api/validate", response_model=ValidationResponse)
async def validate_data(
    format_type: ExportFormat,
    data_type: str,
    school_year: str,
    district_id: str | None = None,
):
    """Validate export data before processing."""
    try:
        result = validate_export_data.delay(format_type.value, data_type, school_year, district_id)
        validation_result = result.get(timeout=60)  # 1 minute timeout

        return ValidationResponse(**validation_result)

    except Exception as e:
        logger.error("Failed to validate data", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to validate data: {str(e)}")


@app.post("/api/cleanup")
async def cleanup_exports(retention_days: int = 30):
    """Clean up old export files."""
    try:
        result = cleanup_old_exports.delay(retention_days)
        cleanup_stats = result.get(timeout=300)  # 5 minute timeout

        logger.info("Cleanup completed", stats=cleanup_stats)

        return cleanup_stats

    except Exception as e:
        logger.error("Failed to cleanup exports", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to cleanup exports: {str(e)}")


@app.post("/api/reports/audit")
async def generate_audit_report(
    start_date: str,
    end_date: str,
    format_type: ExportFormat | None = None,
):
    """Generate compliance audit report."""
    try:
        result = generate_compliance_report.delay(
            start_date, end_date, format_type.value if format_type else None
        )
        report = result.get(timeout=300)  # 5 minute timeout

        return report

    except Exception as e:
        logger.error("Failed to generate audit report", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@app.get("/api/stats")
async def get_statistics(db: AsyncSession = Depends(get_db_session)):
    """Get export statistics."""
    try:
        from sqlalchemy import func

        # Count jobs by status
        status_counts = {}
        for status in ExportStatus:
            stmt = select(func.count(ExportJob.id)).where(ExportJob.status == status)
            result = await db.execute(stmt)
            status_counts[status.value] = result.scalar() or 0

        # Count jobs by format
        format_counts = {}
        for format_type in ExportFormat:
            stmt = select(func.count(ExportJob.id)).where(ExportJob.format == format_type)
            result = await db.execute(stmt)
            format_counts[format_type.value] = result.scalar() or 0

        # Recent activity
        stmt = (
            select(ExportJob)
            .where(ExportJob.created_at >= func.current_date())
            .order_by(desc(ExportJob.created_at))
            .limit(10)
        )
        result = await db.execute(stmt)
        recent_jobs = result.scalars().all()

        return {
            "status_counts": status_counts,
            "format_counts": format_counts,
            "recent_jobs_count": len(recent_jobs),
            "total_jobs": sum(status_counts.values()),
        }

    except Exception as e:
        logger.error("Failed to get statistics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
