"""
Audit logging module for immutable compliance export audit trails.
Provides tamper-evident logging for regulatory compliance.
"""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditAction, AuditLog, ExportJob


class AuditLogger:
    """Immutable audit logger for compliance export operations."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize audit logger.

        Args:
            db_session: Async database session
        """
        self.db_session = db_session

    async def log_export_created(
        self,
        export_job: ExportJob,
        user_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log export job creation."""
        return await self._create_audit_log(
            export_job_id=export_job.id,
            action=AuditAction.EXPORT_CREATED,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            new_values={
                "job_id": str(export_job.id),
                "format": export_job.format.value,
                "name": export_job.name,
                "school_year": export_job.school_year,
                "state_code": export_job.state_code,
            },
        )

    async def log_export_started(
        self,
        export_job: ExportJob,
        user_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log export job start."""
        return await self._create_audit_log(
            export_job_id=export_job.id,
            action=AuditAction.EXPORT_STARTED,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            new_values={
                "started_at": export_job.started_at.isoformat() if export_job.started_at else None,
                "status": export_job.status.value,
            },
        )

    async def log_export_completed(
        self,
        export_job: ExportJob,
        user_id: str,
        file_path: str | None = None,
        encrypted_file_path: str | None = None,
        file_size: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log export job completion."""
        completion_details = details or {}
        completion_details.update(
            {
                "file_path": file_path,
                "encrypted_file_path": encrypted_file_path,
                "file_size": file_size,
                "total_records": export_job.total_records,
                "processed_records": export_job.processed_records,
            }
        )

        return await self._create_audit_log(
            export_job_id=export_job.id,
            action=AuditAction.EXPORT_COMPLETED,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=completion_details,
            new_values={
                "completed_at": export_job.completed_at.isoformat()
                if export_job.completed_at
                else None,
                "status": export_job.status.value,
                "progress_percentage": export_job.progress_percentage,
            },
        )

    async def log_export_failed(
        self,
        export_job: ExportJob,
        user_id: str,
        error_message: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log export job failure."""
        failure_details = details or {}
        failure_details.update(
            {
                "error_message": error_message,
                "processed_records": export_job.processed_records,
                "total_records": export_job.total_records,
            }
        )

        return await self._create_audit_log(
            export_job_id=export_job.id,
            action=AuditAction.EXPORT_FAILED,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=failure_details,
            new_values={
                "status": export_job.status.value,
                "error_message": error_message,
            },
        )

    async def log_export_downloaded(
        self,
        export_job_id: uuid.UUID,
        user_id: str,
        download_method: str = "web",
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log export file download."""
        download_details = details or {}
        download_details.update(
            {
                "download_method": download_method,
                "download_timestamp": datetime.utcnow().isoformat(),
            }
        )

        return await self._create_audit_log(
            export_job_id=export_job_id,
            action=AuditAction.EXPORT_DOWNLOADED,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=download_details,
        )

    async def log_export_deleted(
        self,
        export_job_id: uuid.UUID,
        user_id: str,
        deletion_reason: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log export job deletion."""
        deletion_details = details or {}
        deletion_details.update(
            {
                "deletion_reason": deletion_reason,
                "deletion_timestamp": datetime.utcnow().isoformat(),
            }
        )

        return await self._create_audit_log(
            export_job_id=export_job_id,
            action=AuditAction.EXPORT_DELETED,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=deletion_details,
        )

    async def log_file_encrypted(
        self,
        export_job_id: uuid.UUID,
        user_id: str,
        original_path: str,
        encrypted_path: str,
        encryption_key_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log file encryption."""
        encryption_details = details or {}
        encryption_details.update(
            {
                "original_path": original_path,
                "encrypted_path": encrypted_path,
                "encryption_key_id": encryption_key_id,
                "encryption_timestamp": datetime.utcnow().isoformat(),
            }
        )

        return await self._create_audit_log(
            export_job_id=export_job_id,
            action=AuditAction.FILE_ENCRYPTED,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=encryption_details,
        )

    async def log_file_decrypted(
        self,
        export_job_id: uuid.UUID,
        user_id: str,
        encrypted_path: str,
        decrypted_path: str,
        encryption_key_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log file decryption."""
        decryption_details = details or {}
        decryption_details.update(
            {
                "encrypted_path": encrypted_path,
                "decrypted_path": decrypted_path,
                "encryption_key_id": encryption_key_id,
                "decryption_timestamp": datetime.utcnow().isoformat(),
            }
        )

        return await self._create_audit_log(
            export_job_id=export_job_id,
            action=AuditAction.FILE_DECRYPTED,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=decryption_details,
        )

    async def _create_audit_log(
        self,
        export_job_id: uuid.UUID,
        action: AuditAction,
        user_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
        previous_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        compliance_officer: str | None = None,
        regulatory_requirement: str | None = None,
    ) -> AuditLog:
        """Create an immutable audit log entry."""

        # Generate integrity hash for tamper detection
        log_data = {
            "export_job_id": str(export_job_id),
            "action": action.value,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {},
            "previous_values": previous_values,
            "new_values": new_values,
        }

        integrity_hash = self._calculate_integrity_hash(log_data)

        # Add integrity hash to details
        if details is None:
            details = {}
        details["integrity_hash"] = integrity_hash

        audit_log = AuditLog(
            export_job_id=export_job_id,
            action=action,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            previous_values=previous_values,
            new_values=new_values,
            compliance_officer=compliance_officer,
            regulatory_requirement=regulatory_requirement,
        )

        self.db_session.add(audit_log)
        await self.db_session.flush()
        return audit_log

    def _calculate_integrity_hash(self, log_data: dict[str, Any]) -> str:
        """Calculate SHA-256 hash for audit log integrity verification."""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(log_data, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode()).hexdigest()

    async def verify_audit_integrity(self, audit_log: AuditLog) -> bool:
        """Verify the integrity of an audit log entry."""
        # Reconstruct log data
        log_data = {
            "export_job_id": str(audit_log.export_job_id),
            "action": audit_log.action.value,
            "timestamp": audit_log.timestamp.isoformat(),
            "user_id": audit_log.user_id,
            "ip_address": audit_log.ip_address,
            "user_agent": audit_log.user_agent,
            "details": {k: v for k, v in audit_log.details.items() if k != "integrity_hash"},
            "previous_values": audit_log.previous_values,
            "new_values": audit_log.new_values,
        }

        # Calculate expected hash
        expected_hash = self._calculate_integrity_hash(log_data)

        # Compare with stored hash
        stored_hash = audit_log.details.get("integrity_hash")
        return expected_hash == stored_hash

    async def generate_audit_report(
        self,
        export_job_id: uuid.UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_id: str | None = None,
        action: AuditAction | None = None,
    ) -> dict[str, Any]:
        """Generate comprehensive audit report."""
        from sqlalchemy import and_, select

        # Build query conditions
        conditions = []

        if export_job_id:
            conditions.append(AuditLog.export_job_id == export_job_id)
        if start_date:
            conditions.append(AuditLog.timestamp >= start_date)
        if end_date:
            conditions.append(AuditLog.timestamp <= end_date)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)

        # Execute query
        query = select(AuditLog)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(AuditLog.timestamp.desc())

        result = await self.db_session.execute(query)
        audit_logs = result.scalars().all()

        # Generate report
        report = {
            "report_generated_at": datetime.utcnow().isoformat(),
            "total_entries": len(audit_logs),
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "filters": {
                "export_job_id": str(export_job_id) if export_job_id else None,
                "user_id": user_id,
                "action": action.value if action else None,
            },
            "entries": [
                {
                    "id": str(log.id),
                    "export_job_id": str(log.export_job_id),
                    "action": log.action.value,
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id,
                    "ip_address": log.ip_address,
                    "details": log.details,
                    "integrity_verified": await self.verify_audit_integrity(log),
                }
                for log in audit_logs
            ],
        }

        return report
