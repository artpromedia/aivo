"""Export service for generating and managing audit log exports."""

import asyncio
import csv
import io
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import boto3
from botocore.exceptions import ClientError
import pandas as pd
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config import settings
from app.models.audit_event import AuditEvent
from app.models.export_job import ExportJob, ExportFormat, ExportStatus

logger = structlog.get_logger(__name__)


class ExportService:
    """Service for managing audit log exports to various formats."""

    def __init__(self):
        self.s3_client = None
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            )

    async def create_export_job(
        self,
        db: AsyncSession,
        job_name: str,
        requested_by: str,
        export_format: ExportFormat,
        filters: Optional[Dict[str, Any]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ExportJob:
        """Create a new export job."""
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise ValueError("Start date must be before end date")

        # Create export job
        export_job = ExportJob(
            job_name=job_name,
            requested_by=requested_by,
            export_format=export_format,
            filters=filters or {},
            start_date=start_date,
            end_date=end_date,
            expires_at=datetime.utcnow() + timedelta(hours=settings.export_signed_url_expiry_hours),
        )

        db.add(export_job)
        await db.commit()
        await db.refresh(export_job)

        logger.info(
            "Export job created",
            job_id=str(export_job.id),
            requested_by=requested_by,
            format=export_format,
            filters=filters,
        )

        # Start processing asynchronously
        asyncio.create_task(self._process_export_job(export_job.id))

        return export_job

    async def _process_export_job(self, job_id: UUID) -> None:
        """Process an export job asynchronously."""
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            try:
                # Get the job
                stmt = select(ExportJob).where(ExportJob.id == job_id)
                result = await db.execute(stmt)
                job = result.scalar_one_or_none()

                if not job:
                    logger.error("Export job not found", job_id=str(job_id))
                    return

                # Update status to processing
                job.status = ExportStatus.PROCESSING
                job.started_at = datetime.utcnow()
                await db.commit()

                logger.info("Starting export job processing", job_id=str(job_id))

                # Query audit events based on filters
                events = await self._query_audit_events(db, job)

                # Generate export file
                file_content, file_size = await self._generate_export_file(events, job.export_format)

                # Upload to S3 if configured
                download_url = None
                if self.s3_client:
                    s3_key = f"{settings.s3_export_prefix}/{job_id}.{job.export_format.value}"
                    await self._upload_to_s3(file_content, s3_key)
                    download_url = await self._generate_signed_url(s3_key)

                    job.s3_bucket = settings.s3_bucket_name
                    job.s3_key = s3_key

                # Update job with results
                job.status = ExportStatus.COMPLETED
                job.total_records = len(events)
                job.file_size_bytes = file_size
                job.download_url = download_url
                job.completed_at = datetime.utcnow()

                await db.commit()

                logger.info(
                    "Export job completed",
                    job_id=str(job_id),
                    total_records=len(events),
                    file_size_bytes=file_size,
                )

            except Exception as e:
                # Update job status to failed
                async with AsyncSessionLocal() as error_db:
                    stmt = select(ExportJob).where(ExportJob.id == job_id)
                    result = await error_db.execute(stmt)
                    job = result.scalar_one_or_none()

                    if job:
                        job.status = ExportStatus.FAILED
                        job.error_message = str(e)[:1000]  # Truncate long error messages
                        job.completed_at = datetime.utcnow()
                        await error_db.commit()

                logger.error(
                    "Export job failed",
                    job_id=str(job_id),
                    error=str(e),
                )

    async def _query_audit_events(self, db: AsyncSession, job: ExportJob) -> List[AuditEvent]:
        """Query audit events based on export job filters."""
        conditions = []
        filters = job.filters or {}

        # Apply filters
        if filters.get("actor"):
            conditions.append(AuditEvent.actor.ilike(f"%{filters['actor']}%"))
        if filters.get("action"):
            conditions.append(AuditEvent.action == filters["action"])
        if filters.get("resource_type"):
            conditions.append(AuditEvent.resource_type == filters["resource_type"])
        if filters.get("resource_id"):
            conditions.append(AuditEvent.resource_id == filters["resource_id"])
        if filters.get("ip_address"):
            conditions.append(AuditEvent.ip_address == filters["ip_address"])

        # Apply date range
        if job.start_date:
            conditions.append(AuditEvent.timestamp >= job.start_date)
        if job.end_date:
            conditions.append(AuditEvent.timestamp <= job.end_date)

        # Build query with limit for safety
        stmt = (
            select(AuditEvent)
            .where(and_(*conditions) if conditions else True)
            .order_by(AuditEvent.timestamp.desc())
            .limit(settings.max_export_records)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def _generate_export_file(
        self,
        events: List[AuditEvent],
        format: ExportFormat
    ) -> tuple[bytes, int]:
        """Generate export file in the specified format."""
        if format == ExportFormat.CSV:
            return await self._generate_csv(events)
        elif format == ExportFormat.JSON:
            return await self._generate_json(events)
        elif format == ExportFormat.XLSX:
            return await self._generate_xlsx(events)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def _generate_csv(self, events: List[AuditEvent]) -> tuple[bytes, int]:
        """Generate CSV export."""
        output = io.StringIO()

        if not events:
            return b"", 0

        # Define CSV columns
        fieldnames = [
            'id', 'timestamp', 'actor', 'actor_role', 'action',
            'resource_type', 'resource_id', 'ip_address', 'user_agent',
            'request_id', 'session_id', 'before_state', 'after_state',
            'metadata', 'current_hash', 'previous_hash'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for event in events:
            row = {
                'id': str(event.id),
                'timestamp': event.timestamp.isoformat(),
                'actor': event.actor,
                'actor_role': event.actor_role,
                'action': event.action,
                'resource_type': event.resource_type,
                'resource_id': event.resource_id,
                'ip_address': event.ip_address,
                'user_agent': event.user_agent,
                'request_id': event.request_id,
                'session_id': event.session_id,
                'before_state': json.dumps(event.before_state) if event.before_state else None,
                'after_state': json.dumps(event.after_state) if event.after_state else None,
                'metadata': json.dumps(event.metadata) if event.metadata else None,
                'current_hash': event.current_hash,
                'previous_hash': event.previous_hash,
            }
            writer.writerow(row)

        content = output.getvalue().encode('utf-8')
        return content, len(content)

    async def _generate_json(self, events: List[AuditEvent]) -> tuple[bytes, int]:
        """Generate JSON export."""
        export_data = {
            "export_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_records": len(events),
                "format": "json",
                "version": "1.0",
            },
            "audit_events": []
        }

        for event in events:
            event_data = {
                "id": str(event.id),
                "timestamp": event.timestamp.isoformat(),
                "actor": event.actor,
                "actor_role": event.actor_role,
                "action": event.action,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "before_state": event.before_state,
                "after_state": event.after_state,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "request_id": event.request_id,
                "session_id": event.session_id,
                "metadata": event.metadata,
                "current_hash": event.current_hash,
                "previous_hash": event.previous_hash,
                "created_at": event.created_at.isoformat(),
            }
            export_data["audit_events"].append(event_data)

        content = json.dumps(export_data, indent=2, separators=(',', ': ')).encode('utf-8')
        return content, len(content)

    async def _generate_xlsx(self, events: List[AuditEvent]) -> tuple[bytes, int]:
        """Generate Excel export."""
        # Convert events to DataFrame
        data = []
        for event in events:
            row = {
                'ID': str(event.id),
                'Timestamp': event.timestamp,
                'Actor': event.actor,
                'Actor Role': event.actor_role,
                'Action': event.action,
                'Resource Type': event.resource_type,
                'Resource ID': event.resource_id,
                'IP Address': event.ip_address,
                'User Agent': event.user_agent,
                'Request ID': event.request_id,
                'Session ID': event.session_id,
                'Before State': json.dumps(event.before_state) if event.before_state else None,
                'After State': json.dumps(event.after_state) if event.after_state else None,
                'Metadata': json.dumps(event.metadata) if event.metadata else None,
                'Current Hash': event.current_hash,
                'Previous Hash': event.previous_hash,
                'Created At': event.created_at,
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Write to Excel format
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Audit Events', index=False)

        content = output.getvalue()
        return content, len(content)

    async def _upload_to_s3(self, content: bytes, s3_key: str) -> None:
        """Upload file content to S3."""
        if not self.s3_client:
            raise ValueError("S3 client not configured")

        try:
            self.s3_client.put_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key,
                Body=content,
                ServerSideEncryption='AES256',
                Metadata={
                    'service': 'audit-log-svc',
                    'generated_at': datetime.utcnow().isoformat(),
                }
            )
            logger.info("File uploaded to S3", s3_key=s3_key, size=len(content))

        except ClientError as e:
            logger.error("Failed to upload to S3", s3_key=s3_key, error=str(e))
            raise

    async def _generate_signed_url(self, s3_key: str) -> str:
        """Generate a signed URL for downloading the export."""
        if not self.s3_client:
            raise ValueError("S3 client not configured")

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.s3_bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=settings.export_signed_url_expiry_hours * 3600
            )
            return url

        except ClientError as e:
            logger.error("Failed to generate signed URL", s3_key=s3_key, error=str(e))
            raise

    async def get_export_jobs(
        self,
        db: AsyncSession,
        requested_by: Optional[str] = None,
        status: Optional[ExportStatus] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Get export jobs with filtering and pagination."""
        conditions = []

        if requested_by:
            conditions.append(ExportJob.requested_by == requested_by)
        if status:
            conditions.append(ExportJob.status == status)

        # Count total
        count_stmt = select(func.count(ExportJob.id)).where(and_(*conditions) if conditions else True)
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar()

        # Query jobs
        offset = (page - 1) * page_size
        stmt = (
            select(ExportJob)
            .where(and_(*conditions) if conditions else True)
            .order_by(ExportJob.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(stmt)
        jobs = result.scalars().all()

        return {
            "jobs": jobs,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
            }
        }
