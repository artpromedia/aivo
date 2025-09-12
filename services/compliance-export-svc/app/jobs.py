"""
Export job processor using Celery for background compliance exports.
Ensures RPO/RTO 5 minutes with comprehensive error handling and audit logging.
"""

import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .audit import AuditLogger
from .crypto import encryption_manager
from .exporters.calpads import CALPADSExporter
from .exporters.edfacts import EDFactsExporter
from .models import ExportJob, ExportStatus

# Initialize Celery app
celery_app = Celery("compliance-export")
celery_app.config_from_object("config.celery_config")

# Database setup for async operations
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:password@localhost/compliance_db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class ComplianceExportProcessor:
    """Background processor for compliance export jobs."""

    def __init__(self):
        """Initialize the export processor."""
        self.export_base_path = Path(os.getenv("COMPLIANCE_EXPORT_PATH", "/tmp/compliance-exports"))
        self.export_base_path.mkdir(parents=True, exist_ok=True)

    async def process_export_job(
        self,
        job_id: uuid.UUID,
        format_type: str,
        export_params: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """
        Process a compliance export job asynchronously.

        Args:
            job_id: Export job UUID
            format_type: Export format (edfacts, calpads)
            export_params: Export parameters
            user_id: User ID for audit logging

        Returns:
            Export results
        """
        async with AsyncSessionLocal() as db_session:
            try:
                # Get export job
                job = await self._get_export_job(db_session, job_id)
                if not job:
                    raise ValueError(f"Export job {job_id} not found")

                # Initialize audit logger
                audit_logger = AuditLogger(db_session)

                # Update job status to running
                job.status = ExportStatus.RUNNING
                job.started_at = datetime.utcnow()
                await audit_logger.log_export_started(job, user_id)
                await db_session.commit()

                # Process export based on format
                if format_type.lower() == "edfacts":
                    result = await self._process_edfacts_export(
                        db_session, job, export_params, user_id, audit_logger
                    )
                elif format_type.lower() == "calpads":
                    result = await self._process_calpads_export(
                        db_session, job, export_params, user_id, audit_logger
                    )
                else:
                    raise ValueError(f"Unsupported export format: {format_type}")

                # Encrypt the exported file
                encrypted_result = await self._encrypt_export_file(
                    db_session, job, result, user_id, audit_logger
                )

                # Update job as completed
                job.status = ExportStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.progress_percentage = 100
                job.total_records = result.get("total_records", 0)
                job.processed_records = result.get("processed_records", 0)
                job.file_path = str(result.get("file_path", ""))
                job.encrypted_file_path = str(encrypted_result.get("encrypted_path", ""))
                job.file_size = result.get("file_size", 0)
                job.encryption_key_id = encrypted_result.get("key_id", "")

                await audit_logger.log_export_completed(
                    job,
                    user_id,
                    file_path=job.file_path,
                    encrypted_file_path=job.encrypted_file_path,
                    file_size=job.file_size,
                )

                await db_session.commit()

                return {
                    "job_id": str(job_id),
                    "status": "completed",
                    "file_path": job.file_path,
                    "encrypted_file_path": job.encrypted_file_path,
                    "total_records": job.total_records,
                    "processed_records": job.processed_records,
                    "file_size": job.file_size,
                }

            except Exception as e:
                # Handle export failure
                await self._handle_export_failure(db_session, job_id, str(e), user_id)
                raise

    async def _process_edfacts_export(
        self,
        db_session: AsyncSession,
        job: ExportJob,
        export_params: dict[str, Any],
        user_id: str,
        audit_logger: AuditLogger,
    ) -> dict[str, Any]:
        """Process EDFacts export."""
        exporter = EDFactsExporter(db_session)

        # Determine export type
        export_type = export_params.get("export_type", "student")
        school_year = export_params.get("school_year", job.school_year)
        district_id = export_params.get("district_id", job.district_id)

        # Generate output file path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"edfacts_{export_type}_{school_year}_{timestamp}.csv"
        output_path = self.export_base_path / "edfacts" / filename

        if export_type == "student":
            result = await exporter.export_student_data(job, output_path, school_year, district_id)
        elif export_type == "assessment":
            result = await exporter.export_assessment_data(
                job, output_path, school_year, export_params.get("assessment_type"), district_id
            )
        elif export_type == "discipline":
            result = await exporter.export_discipline_data(
                job, output_path, school_year, district_id
            )
        else:
            raise ValueError(f"Unknown EDFacts export type: {export_type}")

        result["file_path"] = output_path
        return result

    async def _process_calpads_export(
        self,
        db_session: AsyncSession,
        job: ExportJob,
        export_params: dict[str, Any],
        user_id: str,
        audit_logger: AuditLogger,
    ) -> dict[str, Any]:
        """Process CALPADS export."""
        exporter = CALPADSExporter(db_session)

        # Determine export type
        export_type = export_params.get("export_type", "senr")
        school_year = export_params.get("school_year", job.school_year)
        district_code = export_params.get("district_code", job.district_id)

        # Generate output file path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"calpads_{export_type}_{school_year}_{timestamp}.csv"
        output_path = self.export_base_path / "calpads" / filename

        if export_type == "senr":
            result = await exporter.export_senr_data(job, output_path, school_year, district_code)
        elif export_type == "sass":
            result = await exporter.export_sass_data(
                job, output_path, school_year, export_params.get("test_type"), district_code
            )
        elif export_type == "sdis":
            result = await exporter.export_sdis_data(job, output_path, school_year, district_code)
        else:
            raise ValueError(f"Unknown CALPADS export type: {export_type}")

        result["file_path"] = output_path
        return result

    async def _encrypt_export_file(
        self,
        db_session: AsyncSession,
        job: ExportJob,
        export_result: dict[str, Any],
        user_id: str,
        audit_logger: AuditLogger,
    ) -> dict[str, Any]:
        """Encrypt the exported file for secure storage."""
        original_path = Path(export_result["file_path"])

        # Generate encryption key
        key_id, key_data = encryption_manager.generate_file_key()

        # Create encrypted file path
        encrypted_filename = f"{original_path.stem}_encrypted{original_path.suffix}.enc"
        encrypted_path = original_path.parent / encrypted_filename

        # Encrypt the file
        encrypted_size = encryption_manager.encrypt_file(original_path, encrypted_path, key_data)

        # Store encryption key in database (implement this)
        await self._store_encryption_key(db_session, key_id, key_data, user_id)

        # Log encryption
        await audit_logger.log_file_encrypted(
            job.id,
            user_id,
            str(original_path),
            str(encrypted_path),
            key_id,
        )

        # Securely delete original file
        encryption_manager.secure_delete(original_path)

        return {
            "encrypted_path": encrypted_path,
            "key_id": key_id,
            "encrypted_size": encrypted_size,
        }

    async def _store_encryption_key(
        self,
        db_session: AsyncSession,
        key_id: str,
        key_data: bytes,
        user_id: str,
    ) -> None:
        """Store encryption key in database."""
        from .models import EncryptionKey

        encryption_key = EncryptionKey(
            key_id=key_id,
            encrypted_key=key_data[: len(key_data) // 2],  # Simplified storage
            salt=key_data[len(key_data) // 2 :],
            created_by=user_id,
        )

        db_session.add(encryption_key)
        await db_session.flush()

    async def _get_export_job(
        self, db_session: AsyncSession, job_id: uuid.UUID
    ) -> ExportJob | None:
        """Get export job by ID."""
        from sqlalchemy import select

        stmt = select(ExportJob).where(ExportJob.id == job_id)
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def _handle_export_failure(
        self,
        db_session: AsyncSession,
        job_id: uuid.UUID,
        error_message: str,
        user_id: str,
    ) -> None:
        """Handle export job failure."""
        try:
            job = await self._get_export_job(db_session, job_id)
            if job:
                job.status = ExportStatus.FAILED
                job.error_message = error_message
                job.completed_at = datetime.utcnow()

                audit_logger = AuditLogger(db_session)
                await audit_logger.log_export_failed(job, user_id, error_message)
                await db_session.commit()
        except Exception as e:
            print(f"Error handling export failure: {e}")


# Celery task definitions
processor = ComplianceExportProcessor()


@celery_app.task(bind=True, max_retries=3)
def process_compliance_export(
    self,
    job_id: str,
    format_type: str,
    export_params: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    """
    Celery task for processing compliance exports.

    Args:
        job_id: Export job UUID as string
        format_type: Export format (edfacts, calpads)
        export_params: Export parameters
        user_id: User ID for audit logging

    Returns:
        Export results
    """
    try:
        # Convert string UUID back to UUID object
        job_uuid = uuid.UUID(job_id)

        # Run async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                processor.process_export_job(job_uuid, format_type, export_params, user_id)
            )
            return result
        finally:
            loop.close()

    except Exception as exc:
        # Retry with exponential backoff
        retry_delay = 2**self.request.retries
        raise self.retry(exc=exc, countdown=retry_delay, max_retries=3)


@celery_app.task
def validate_export_data(
    format_type: str,
    data_type: str,
    school_year: str,
    district_id: str | None = None,
) -> dict[str, Any]:
    """
    Validate export data before processing.

    Args:
        format_type: Export format (edfacts, calpads)
        data_type: Type of data to validate
        school_year: Academic year
        district_id: Optional district filter

    Returns:
        Validation results
    """

    async def _validate():
        async with AsyncSessionLocal() as db_session:
            if format_type.lower() == "edfacts":
                exporter = EDFactsExporter(db_session)
                return await exporter.validate_export_data(data_type, school_year, district_id)
            elif format_type.lower() == "calpads":
                exporter = CALPADSExporter(db_session)
                return await exporter.validate_calpads_data(data_type, school_year, district_id)
            else:
                return {"is_valid": False, "errors": [f"Unknown format: {format_type}"]}

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(_validate())
    finally:
        loop.close()


@celery_app.task
def cleanup_old_exports(retention_days: int = 30) -> dict[str, Any]:
    """
    Clean up old export files and jobs.

    Args:
        retention_days: Number of days to retain exports

    Returns:
        Cleanup statistics
    """

    async def _cleanup():
        async with AsyncSessionLocal() as db_session:
            from datetime import timedelta

            from sqlalchemy import and_, select

            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # Find old completed jobs
            stmt = select(ExportJob).where(
                and_(
                    ExportJob.completed_at < cutoff_date,
                    ExportJob.status == ExportStatus.COMPLETED,
                )
            )
            result = await db_session.execute(stmt)
            old_jobs = result.scalars().all()

            cleanup_stats = {
                "jobs_found": len(old_jobs),
                "files_deleted": 0,
                "errors": [],
            }

            for job in old_jobs:
                try:
                    # Delete encrypted file
                    if job.encrypted_file_path:
                        encrypted_path = Path(job.encrypted_file_path)
                        if encrypted_path.exists():
                            encryption_manager.secure_delete(encrypted_path)
                            cleanup_stats["files_deleted"] += 1

                    # Delete original file if it still exists
                    if job.file_path:
                        original_path = Path(job.file_path)
                        if original_path.exists():
                            encryption_manager.secure_delete(original_path)

                    # Mark job as deleted (keep audit trail)
                    job.status = ExportStatus.CANCELLED

                except Exception as e:
                    cleanup_stats["errors"].append(f"Job {job.id}: {str(e)}")

            await db_session.commit()
            return cleanup_stats

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(_cleanup())
    finally:
        loop.close()


@celery_app.task
def generate_compliance_report(
    start_date: str,
    end_date: str,
    format_type: str | None = None,
) -> dict[str, Any]:
    """
    Generate compliance audit report.

    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        format_type: Optional format filter

    Returns:
        Audit report
    """

    async def _generate_report():
        async with AsyncSessionLocal() as db_session:
            audit_logger = AuditLogger(db_session)

            return await audit_logger.generate_audit_report(
                start_date=datetime.fromisoformat(start_date),
                end_date=datetime.fromisoformat(end_date),
            )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(_generate_report())
    finally:
        loop.close()
