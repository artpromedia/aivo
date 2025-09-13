"""
Cleanup Service - Background service for automated data retention and cleanup
"""

import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text

from ..database import AsyncSessionLocal
from ..models import (
    RetentionPolicy, DataInventoryItem, DSRRequest, DSRStatus,
    EntityType, LegalHoldStatus
)
from ..config import settings

logger = structlog.get_logger()


class CleanupService:
    """Background service for automated data cleanup and retention enforcement."""

    def __init__(self):
        self.running = False
        self.task = None

    async def start(self) -> None:
        """Start the cleanup service."""
        if self.running:
            return

        self.running = True
        logger.info("Starting data cleanup service")

        # Start the main cleanup loop
        while self.running:
            try:
                await self._run_cleanup_cycle()
                await asyncio.sleep(settings.CLEANUP_INTERVAL_MINUTES * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cleanup cycle", error=str(e))
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def stop(self) -> None:
        """Stop the cleanup service."""
        self.running = False
        logger.info("Stopping data cleanup service")

    async def _run_cleanup_cycle(self) -> None:
        """Run a single cleanup cycle."""
        logger.info("Starting cleanup cycle")

        async with AsyncSessionLocal() as db:
            # Clean up expired exports
            await self._cleanup_expired_exports(db)

            # Process automatic deletions
            await self._process_automatic_deletions(db)

            # Clean up completed DSR requests
            await self._cleanup_old_dsr_requests(db)

            # Update retention schedules
            await self._update_retention_schedules(db)

            await db.commit()

        logger.info("Cleanup cycle completed")

    async def _cleanup_expired_exports(self, db: AsyncSession) -> None:
        """Clean up expired export files."""
        logger.debug("Cleaning up expired exports")

        # Find expired export requests
        cutoff_time = datetime.utcnow()
        query = select(DSRRequest).where(
            DSRRequest.dsr_type == "export",
            DSRRequest.status == DSRStatus.COMPLETED,
            DSRRequest.export_expires_at < cutoff_time,
            DSRRequest.export_file_path.isnot(None)
        )

        result = await db.execute(query)
        expired_requests = result.scalars().all()

        import os
        for request in expired_requests:
            try:
                # Delete the export file
                if request.export_file_path and os.path.exists(request.export_file_path):
                    os.remove(request.export_file_path)
                    logger.debug("Deleted expired export file", file_path=request.export_file_path)

                # Clear file paths from database
                request.export_file_path = None
                request.export_download_url = None

            except Exception as e:
                logger.error("Failed to delete export file", file_path=request.export_file_path, error=str(e))

        if expired_requests:
            logger.info("Cleaned up expired exports", count=len(expired_requests))

    async def _process_automatic_deletions(self, db: AsyncSession) -> None:
        """Process automatic deletions based on retention policies."""
        logger.debug("Processing automatic deletions")

        # Get all retention policies with auto-delete enabled
        policies_query = select(RetentionPolicy).where(
            RetentionPolicy.auto_delete_enabled == True
        )

        result = await db.execute(policies_query)
        policies = result.scalars().all()

        deletion_summary = {}

        for policy in policies:
            try:
                deleted_count = await self._delete_expired_data(db, policy)
                if deleted_count > 0:
                    deletion_summary[f"{policy.entity_type.value}_{policy.tenant_id or 'global'}"] = deleted_count
            except Exception as e:
                logger.error(
                    "Failed to process deletions for policy",
                    policy_id=policy.id,
                    entity_type=policy.entity_type,
                    error=str(e)
                )

        if deletion_summary:
            logger.info("Automatic deletions processed", summary=deletion_summary)

    async def _delete_expired_data(self, db: AsyncSession, policy: RetentionPolicy) -> int:
        """Delete expired data for a specific retention policy."""
        # Calculate cutoff dates
        retention_cutoff = datetime.utcnow() - timedelta(days=policy.retention_days)
        grace_cutoff = retention_cutoff - timedelta(days=policy.grace_period_days)

        # Find data inventory items that are eligible for deletion
        query = select(DataInventoryItem).where(
            DataInventoryItem.entity_type == policy.entity_type,
            DataInventoryItem.created_at < grace_cutoff,
            DataInventoryItem.is_deleted == False,
            DataInventoryItem.has_legal_hold == False
        )

        if policy.tenant_id:
            query = query.where(DataInventoryItem.tenant_id == policy.tenant_id)

        result = await db.execute(query)
        items_to_delete = result.scalars().all()

        deleted_count = 0
        for item in items_to_delete:
            try:
                # Perform the actual deletion (this would call external services)
                await self._perform_physical_deletion(item)

                # Mark as deleted in inventory
                item.is_deleted = True
                item.updated_at = datetime.utcnow()
                deleted_count += 1

            except Exception as e:
                logger.error(
                    "Failed to delete data item",
                    item_id=item.id,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    error=str(e)
                )

        return deleted_count

    async def _perform_physical_deletion(self, item: DataInventoryItem) -> None:
        """Perform the actual physical deletion of data."""
        # This is where you would call external services to delete the actual data
        # For now, we'll just log the deletion

        logger.debug(
            "Performing physical deletion",
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            data_category=item.data_category,
            storage_location=item.storage_location
        )

        # Example implementations for different storage types:
        if item.storage_location == "database":
            await self._delete_from_database(item)
        elif item.storage_location == "file_system":
            await self._delete_from_filesystem(item)
        elif item.storage_location == "s3":
            await self._delete_from_s3(item)
        else:
            logger.warning("Unknown storage location", storage_location=item.storage_location)

    async def _delete_from_database(self, item: DataInventoryItem) -> None:
        """Delete data from database."""
        if not item.table_name:
            return

        # This would execute actual DELETE statements
        # For safety, we'll just log what would be deleted
        logger.debug(
            "Would delete from database",
            table=item.table_name,
            entity_id=item.entity_id,
            columns=item.column_names
        )

    async def _delete_from_filesystem(self, item: DataInventoryItem) -> None:
        """Delete data from filesystem."""
        if not item.file_path:
            return

        import os
        try:
            if os.path.exists(item.file_path):
                os.remove(item.file_path)
                logger.debug("Deleted file", file_path=item.file_path)
        except Exception as e:
            logger.error("Failed to delete file", file_path=item.file_path, error=str(e))
            raise

    async def _delete_from_s3(self, item: DataInventoryItem) -> None:
        """Delete data from S3."""
        # This would use boto3 to delete S3 objects
        logger.debug("Would delete from S3", file_path=item.file_path)

    async def _cleanup_old_dsr_requests(self, db: AsyncSession) -> None:
        """Clean up old completed DSR requests."""
        logger.debug("Cleaning up old DSR requests")

        # Keep completed requests for 1 year for audit purposes
        cutoff_date = datetime.utcnow() - timedelta(days=365)

        # Find old completed requests
        query = select(DSRRequest).where(
            DSRRequest.status.in_([DSRStatus.COMPLETED, DSRStatus.FAILED]),
            DSRRequest.completed_at < cutoff_date
        )

        result = await db.execute(query)
        old_requests = result.scalars().all()

        for request in old_requests:
            # Clean up any remaining export files
            if request.export_file_path:
                try:
                    import os
                    if os.path.exists(request.export_file_path):
                        os.remove(request.export_file_path)
                except Exception as e:
                    logger.error("Failed to delete old export file", error=str(e))

            # Archive or delete the request record
            await db.delete(request)

        if old_requests:
            logger.info("Cleaned up old DSR requests", count=len(old_requests))

    async def _update_retention_schedules(self, db: AsyncSession) -> None:
        """Update retention schedules for data inventory items."""
        logger.debug("Updating retention schedules")

        # Get all retention policies
        policies_query = select(RetentionPolicy)
        result = await db.execute(policies_query)
        policies = result.scalars().all()

        # Create a mapping of policies for quick lookup
        policy_map = {}
        for policy in policies:
            key = (policy.entity_type, policy.tenant_id)
            policy_map[key] = policy

        # Update data inventory items without retention dates
        items_query = select(DataInventoryItem).where(
            DataInventoryItem.retention_until.is_(None),
            DataInventoryItem.is_deleted == False
        )

        result = await db.execute(items_query)
        items = result.scalars().all()

        updated_count = 0
        for item in items:
            # Find matching policy
            policy_key = (item.entity_type, item.tenant_id)
            policy = policy_map.get(policy_key)

            if not policy:
                # Try global policy (tenant_id = None)
                policy_key = (item.entity_type, None)
                policy = policy_map.get(policy_key)

            if policy:
                # Calculate retention date
                retention_date = item.created_at + timedelta(days=policy.retention_days)
                item.retention_until = retention_date
                updated_count += 1

        if updated_count > 0:
            logger.info("Updated retention schedules", count=updated_count)

    async def force_cleanup_cycle(self) -> Dict[str, Any]:
        """Force a cleanup cycle and return summary."""
        logger.info("Force cleanup cycle requested")

        summary = {
            "started_at": datetime.utcnow().isoformat(),
            "expired_exports_cleaned": 0,
            "automatic_deletions": {},
            "old_requests_cleaned": 0,
            "retention_schedules_updated": 0
        }

        try:
            async with AsyncSessionLocal() as db:
                # Track each cleanup operation
                summary["expired_exports_cleaned"] = await self._count_expired_exports(db)
                await self._cleanup_expired_exports(db)

                await self._process_automatic_deletions(db)

                summary["old_requests_cleaned"] = await self._count_old_requests(db)
                await self._cleanup_old_dsr_requests(db)

                summary["retention_schedules_updated"] = await self._count_unscheduled_items(db)
                await self._update_retention_schedules(db)

                await db.commit()

            summary["completed_at"] = datetime.utcnow().isoformat()
            summary["status"] = "success"

        except Exception as e:
            logger.error("Force cleanup cycle failed", error=str(e))
            summary["status"] = "failed"
            summary["error"] = str(e)

        return summary

    async def _count_expired_exports(self, db: AsyncSession) -> int:
        """Count expired export files."""
        cutoff_time = datetime.utcnow()
        query = select(DSRRequest).where(
            DSRRequest.dsr_type == "export",
            DSRRequest.status == DSRStatus.COMPLETED,
            DSRRequest.export_expires_at < cutoff_time,
            DSRRequest.export_file_path.isnot(None)
        )

        result = await db.execute(query)
        return len(result.scalars().all())

    async def _count_old_requests(self, db: AsyncSession) -> int:
        """Count old completed DSR requests."""
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        query = select(DSRRequest).where(
            DSRRequest.status.in_([DSRStatus.COMPLETED, DSRStatus.FAILED]),
            DSRRequest.completed_at < cutoff_date
        )

        result = await db.execute(query)
        return len(result.scalars().all())

    async def _count_unscheduled_items(self, db: AsyncSession) -> int:
        """Count data inventory items without retention schedules."""
        query = select(DataInventoryItem).where(
            DataInventoryItem.retention_until.is_(None),
            DataInventoryItem.is_deleted == False
        )

        result = await db.execute(query)
        return len(result.scalars().all())
