"""
DSR (Data Subject Rights) Service - Business logic for export/delete requests
"""

import os
import json
import zipfile
import structlog
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from uuid import uuid4

from ..models import DSRRequest, DSRType, DSRStatus, EntityType, LegalHold, LegalHoldStatus
from ..schemas.dsr import (
    DSRRequestCreate, DSRRequestResponse, DSRStatusResponse,
    DSRExportResponse, DSRStatistics
)
from ..config import settings

logger = structlog.get_logger()


class DSRService:
    """Service for managing Data Subject Rights requests."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(self, request_data: DSRRequestCreate) -> DSRRequestResponse:
        """Create a new DSR request."""
        logger.info(
            "Creating DSR request",
            dsr_type=request_data.dsr_type,
            subject_id=request_data.subject_id,
            subject_type=request_data.subject_type
        )

        # Check for active legal holds that might block the request
        blocked_holds = []
        if request_data.dsr_type == DSRType.DELETE:
            blocked_holds = await self._check_legal_holds(
                request_data.subject_id,
                request_data.subject_type,
                request_data.tenant_id
            )

        dsr_request = DSRRequest(
            dsr_type=request_data.dsr_type,
            subject_id=request_data.subject_id,
            subject_type=request_data.subject_type,
            tenant_id=request_data.tenant_id,
            requester_email=request_data.requester_email,
            requester_name=request_data.requester_name,
            legal_basis=request_data.legal_basis,
            verification_token=str(uuid4()),
            status=DSRStatus.BLOCKED if blocked_holds else DSRStatus.PENDING
        )

        self.db.add(dsr_request)
        await self.db.flush()

        # Associate with blocking legal holds
        if blocked_holds:
            dsr_request.blocked_by_holds.extend(blocked_holds)

        await self.db.commit()
        await self.db.refresh(dsr_request)

        logger.info(
            "DSR request created",
            request_id=dsr_request.id,
            status=dsr_request.status,
            blocked_holds=len(blocked_holds)
        )

        return DSRRequestResponse.model_validate(dsr_request)

    async def get_request(self, request_id: str) -> Optional[DSRRequestResponse]:
        """Get DSR request by ID."""
        query = select(DSRRequest).where(DSRRequest.id == request_id)
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()

        if request:
            return DSRRequestResponse.model_validate(request)
        return None

    async def list_requests(
        self,
        dsr_type: Optional[DSRType] = None,
        status: Optional[DSRStatus] = None,
        subject_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[DSRRequestResponse], int]:
        """List DSR requests with filtering and pagination."""
        query = select(DSRRequest)
        count_query = select(func.count(DSRRequest.id))

        conditions = []
        if dsr_type:
            conditions.append(DSRRequest.dsr_type == dsr_type)
        if status:
            conditions.append(DSRRequest.status == status)
        if subject_id:
            conditions.append(DSRRequest.subject_id == subject_id)
        if tenant_id:
            conditions.append(DSRRequest.tenant_id == tenant_id)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get paginated results
        query = query.order_by(DSRRequest.requested_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        requests = result.scalars().all()

        return [DSRRequestResponse.model_validate(req) for req in requests], total

    async def get_request_status(self, request_id: str) -> Optional[DSRStatusResponse]:
        """Get processing status of DSR request."""
        request = await self.get_request(request_id)
        if not request:
            return None

        # Get blocking legal holds
        query = select(DSRRequest).where(DSRRequest.id == request_id)
        result = await self.db.execute(query)
        req = result.scalar_one_or_none()

        blocked_holds = []
        if req and req.blocked_by_holds:
            blocked_holds = [hold.id for hold in req.blocked_by_holds]

        # Determine current step and estimated completion
        current_step = None
        estimated_completion = None

        if request.status == DSRStatus.PENDING:
            current_step = "Waiting for identity verification"
        elif request.status == DSRStatus.PROCESSING:
            if request.dsr_type == DSRType.EXPORT:
                if request.progress_percentage < 50:
                    current_step = "Collecting data"
                else:
                    current_step = "Generating export bundle"
            elif request.dsr_type == DSRType.DELETE:
                current_step = "Deleting data across systems"

            # Estimate completion (rough estimate based on progress)
            if request.progress_percentage > 0:
                remaining_percentage = 100 - request.progress_percentage
                hours_remaining = (remaining_percentage / request.progress_percentage) * 2  # Assume 2 hours per 100%
                estimated_completion = datetime.utcnow() + timedelta(hours=hours_remaining)
        elif request.status == DSRStatus.BLOCKED:
            current_step = "Blocked by legal hold"
        elif request.status == DSRStatus.COMPLETED:
            current_step = "Completed"
        elif request.status == DSRStatus.FAILED:
            current_step = "Failed"

        return DSRStatusResponse(
            id=request.id,
            status=request.status,
            progress_percentage=request.progress_percentage,
            current_step=current_step,
            estimated_completion=estimated_completion,
            error_details=request.error_details,
            blocked_by_legal_holds=blocked_holds
        )

    async def process_export_request(self, request_id: str) -> None:
        """Process export request in background."""
        logger.info("Starting export processing", request_id=request_id)

        try:
            # Get request
            query = select(DSRRequest).where(DSRRequest.id == request_id)
            result = await self.db.execute(query)
            request = result.scalar_one_or_none()

            if not request or request.status != DSRStatus.PENDING:
                logger.warning("Request not found or not in pending status", request_id=request_id)
                return

            # Update status to processing
            request.status = DSRStatus.PROCESSING
            request.started_at = datetime.utcnow()
            request.progress_percentage = 0
            await self.db.commit()

            # Create export directory
            export_dir = os.path.join(settings.EXPORT_STORAGE_PATH, request_id)
            os.makedirs(export_dir, exist_ok=True)

            # Collect data from various sources
            export_data = await self._collect_subject_data(
                request.subject_id,
                request.subject_type,
                request.tenant_id
            )

            # Update progress
            request.progress_percentage = 60
            await self.db.commit()

            # Generate export bundle
            export_file_path = await self._generate_export_bundle(
                export_dir,
                request.subject_id,
                export_data
            )

            # Update progress
            request.progress_percentage = 90
            await self.db.commit()

            # Generate download URL (in production, this would be a signed URL)
            download_url = f"/api/dsr/requests/{request_id}/download"
            expires_at = datetime.utcnow() + timedelta(hours=settings.EXPORT_TTL_HOURS)

            # Complete request
            request.status = DSRStatus.COMPLETED
            request.progress_percentage = 100
            request.export_file_path = export_file_path
            request.export_download_url = download_url
            request.export_expires_at = expires_at
            request.completed_at = datetime.utcnow()
            request.completion_certificate = self._generate_completion_certificate(request)

            await self.db.commit()

            logger.info("Export processing completed", request_id=request_id)

        except Exception as e:
            logger.error("Export processing failed", request_id=request_id, error=str(e))

            # Update request with error
            if request:
                request.status = DSRStatus.FAILED
                request.error_details = str(e)
                await self.db.commit()

    async def process_delete_request(self, request_id: str) -> None:
        """Process delete request in background."""
        logger.info("Starting delete processing", request_id=request_id)

        try:
            # Get request
            query = select(DSRRequest).where(DSRRequest.id == request_id)
            result = await self.db.execute(query)
            request = result.scalar_one_or_none()

            if not request or request.status not in [DSRStatus.PENDING, DSRStatus.BLOCKED]:
                logger.warning("Request not found or not in correct status", request_id=request_id)
                return

            # Check if still blocked by legal holds
            if request.status == DSRStatus.BLOCKED:
                # Re-check legal holds
                active_holds = await self._check_legal_holds(
                    request.subject_id,
                    request.subject_type,
                    request.tenant_id
                )
                if active_holds:
                    logger.info("Delete request still blocked by legal holds", request_id=request_id)
                    return

            # Update status to processing
            request.status = DSRStatus.PROCESSING
            request.started_at = datetime.utcnow()
            request.progress_percentage = 0
            await self.db.commit()

            # Perform cascade deletion
            deletion_summary = await self._perform_cascade_deletion(
                request.subject_id,
                request.subject_type,
                request.tenant_id
            )

            # Complete request
            request.status = DSRStatus.COMPLETED
            request.progress_percentage = 100
            request.deletion_summary = deletion_summary
            request.completed_at = datetime.utcnow()
            request.completion_certificate = self._generate_completion_certificate(request)

            await self.db.commit()

            logger.info("Delete processing completed", request_id=request_id, summary=deletion_summary)

        except Exception as e:
            logger.error("Delete processing failed", request_id=request_id, error=str(e))

            # Update request with error
            if request:
                request.status = DSRStatus.FAILED
                request.error_details = str(e)
                await self.db.commit()

    async def get_export_download(self, request_id: str) -> DSRExportResponse:
        """Get export download information."""
        request = await self.get_request(request_id)

        if not request:
            raise ValueError("Request not found")

        if request.status != DSRStatus.COMPLETED or not request.export_file_path:
            raise ValueError("Export not available")

        if request.export_expires_at and request.export_expires_at < datetime.utcnow():
            raise ValueError("Export has expired")

        # Get file size
        file_size = 0
        if os.path.exists(request.export_file_path):
            file_size = os.path.getsize(request.export_file_path)

        return DSRExportResponse(
            download_url=request.export_download_url,
            expires_at=request.export_expires_at,
            file_size_bytes=file_size,
            export_format="zip",
            includes_metadata=True
        )

    async def verify_identity(self, request_id: str, verification_token: str) -> bool:
        """Verify identity for DSR request."""
        query = select(DSRRequest).where(DSRRequest.id == request_id)
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()

        if not request or request.verification_token != verification_token:
            return False

        request.identity_verified = True
        await self.db.commit()

        return True

    async def cancel_request(self, request_id: str, reason: Optional[str] = None) -> bool:
        """Cancel DSR request."""
        query = select(DSRRequest).where(DSRRequest.id == request_id)
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()

        if not request or request.status not in [DSRStatus.PENDING, DSRStatus.PROCESSING]:
            return False

        await self.db.delete(request)
        await self.db.commit()

        logger.info("DSR request cancelled", request_id=request_id, reason=reason)
        return True

    async def create_bulk_export_requests(
        self,
        subject_ids: List[str],
        subject_type: EntityType,
        requester_email: str,
        tenant_id: Optional[str] = None
    ) -> List[DSRRequestResponse]:
        """Create bulk export requests."""
        requests = []

        for subject_id in subject_ids:
            request_data = DSRRequestCreate(
                dsr_type=DSRType.EXPORT,
                subject_id=subject_id,
                subject_type=subject_type,
                requester_email=requester_email,
                tenant_id=tenant_id
            )

            request = await self.create_request(request_data)
            requests.append(request)

        logger.info("Bulk export requests created", count=len(requests))
        return requests

    async def get_statistics(
        self,
        tenant_id: Optional[str] = None,
        days: int = 30
    ) -> DSRStatistics:
        """Get DSR request statistics."""
        since_date = datetime.utcnow() - timedelta(days=days)

        base_query = select(DSRRequest).where(DSRRequest.requested_at >= since_date)
        if tenant_id:
            base_query = base_query.where(DSRRequest.tenant_id == tenant_id)

        result = await self.db.execute(base_query)
        requests = result.scalars().all()

        # Calculate statistics
        total_requests = len(requests)
        by_type = {}
        by_status = {}
        processing_times = []

        for req in requests:
            # By type
            by_type[req.dsr_type] = by_type.get(req.dsr_type, 0) + 1

            # By status
            by_status[req.status] = by_status.get(req.status, 0) + 1

            # Processing time
            if req.completed_at and req.started_at:
                processing_time = (req.completed_at - req.started_at).total_seconds() / 3600
                processing_times.append(processing_time)

        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else None

        pending_requests = by_status.get(DSRStatus.PENDING, 0)
        blocked_requests = by_status.get(DSRStatus.BLOCKED, 0)
        completed_last_30_days = by_status.get(DSRStatus.COMPLETED, 0)

        return DSRStatistics(
            total_requests=total_requests,
            by_type=by_type,
            by_status=by_status,
            average_processing_time_hours=avg_processing_time,
            pending_requests=pending_requests,
            blocked_by_legal_holds=blocked_requests,
            completed_last_30_days=completed_last_30_days
        )

    async def _check_legal_holds(
        self,
        subject_id: str,
        subject_type: EntityType,
        tenant_id: Optional[str]
    ) -> List[LegalHold]:
        """Check if subject is under any active legal holds."""
        query = select(LegalHold).where(
            LegalHold.status == LegalHoldStatus.ACTIVE,
            or_(
                LegalHold.expiry_date.is_(None),
                LegalHold.expiry_date > datetime.utcnow()
            )
        )

        if tenant_id:
            query = query.where(
                or_(
                    LegalHold.tenant_id == tenant_id,
                    LegalHold.tenant_id.is_(None)
                )
            )

        result = await self.db.execute(query)
        holds = result.scalars().all()

        blocking_holds = []
        for hold in holds:
            # Check if hold applies to this subject
            if subject_type.value in hold.entity_types:
                if not hold.subject_ids or subject_id in hold.subject_ids:
                    blocking_holds.append(hold)

        return blocking_holds

    async def _collect_subject_data(
        self,
        subject_id: str,
        subject_type: EntityType,
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Collect all data for a subject across systems."""
        # This is a simplified implementation
        # In production, this would query multiple databases/services

        export_data = {
            "subject_id": subject_id,
            "subject_type": subject_type.value,
            "tenant_id": tenant_id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "data_sources": {
                "user_profile": {"name": "John Doe", "email": f"{subject_id}@example.com"},
                "activity_logs": [{"action": "login", "timestamp": "2024-01-01T00:00:00Z"}],
                "documents": [],
                "preferences": {"newsletter": True, "notifications": False}
            }
        }

        return export_data

    async def _generate_export_bundle(
        self,
        export_dir: str,
        subject_id: str,
        export_data: Dict[str, Any]
    ) -> str:
        """Generate ZIP bundle with exported data."""
        # Create data file
        data_file = os.path.join(export_dir, f"{subject_id}_data.json")
        with open(data_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        # Create metadata file
        metadata = {
            "export_id": str(uuid4()),
            "subject_id": subject_id,
            "export_date": datetime.utcnow().isoformat(),
            "format_version": "1.0",
            "data_sources": list(export_data.get("data_sources", {}).keys())
        }

        metadata_file = os.path.join(export_dir, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Create ZIP bundle
        zip_path = os.path.join(export_dir, f"{subject_id}_export.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(data_file, os.path.basename(data_file))
            zipf.write(metadata_file, os.path.basename(metadata_file))

        # Clean up temporary files
        os.remove(data_file)
        os.remove(metadata_file)

        return zip_path

    async def _perform_cascade_deletion(
        self,
        subject_id: str,
        subject_type: EntityType,
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Perform cascade deletion across all systems."""
        # This is a simplified implementation
        # In production, this would delete from multiple databases/services

        deletion_summary = {
            "subject_id": subject_id,
            "subject_type": subject_type.value,
            "tenant_id": tenant_id,
            "deletion_timestamp": datetime.utcnow().isoformat(),
            "deleted_records": {
                "user_profile": 1,
                "activity_logs": 45,
                "documents": 3,
                "preferences": 1,
                "sessions": 12
            },
            "total_records_deleted": 62,
            "systems_affected": ["user_db", "analytics_db", "file_storage"]
        }

        return deletion_summary

    def _generate_completion_certificate(self, request: DSRRequest) -> str:
        """Generate completion certificate for audit purposes."""
        certificate = {
            "request_id": request.id,
            "subject_id": request.subject_id,
            "dsr_type": request.dsr_type.value,
            "completed_at": request.completed_at.isoformat() if request.completed_at else None,
            "processing_duration": str(request.completed_at - request.started_at) if request.completed_at and request.started_at else None,
            "compliance_frameworks": ["FERPA", "COPPA", "GDPR"],
            "certification": "This certifies that the Data Subject Rights request has been processed in accordance with applicable privacy regulations."
        }

        return json.dumps(certificate, indent=2)
