"""Update service for Device OTA & Heartbeat Service."""
# flake8: noqa: E501

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DeviceUpdate,
    DeviceUpdateStatus,
    UpdateRolloutMetrics,
    UpdateStatus,
)
from app.schemas import (
    RollbackRequest,
    UpdateCheckRequest,
    UpdateCheckResponse,
    UpdateMetrics,
    UpdateProgressReport,
    UpdateRolloutStatus,
)
from app.services.firmware_service import FirmwareService

if TYPE_CHECKING:
    pass


class UpdateService:
    """Service for managing device updates."""

    def __init__(self: "UpdateService", db: AsyncSession) -> None:
        """Initialize service."""
        self.db = db
        self.firmware_service = FirmwareService(db)

    async def check_for_updates(
        self: "UpdateService", request: UpdateCheckRequest
    ) -> UpdateCheckResponse:
        """Check for available updates for a device."""
        # Get latest available update
        firmware_update = await self.firmware_service.get_latest_update_for_device(
            device_type=request.device_type,
            current_version=request.current_firmware_version,
        )

        if not firmware_update:
            return UpdateCheckResponse(update_available=False)

        # Check if device is eligible
        eligible, _reason = await self.firmware_service.is_device_eligible_for_update(
            firmware_update=firmware_update,
            device_id=request.device_id,
            battery_level=request.battery_level,
            storage_available_mb=request.storage_available_mb,
        )

        if not eligible:
            return UpdateCheckResponse(
                update_available=False,
                # Note: In production, you might not want to expose the reason
            )

        # Calculate deployment window
        deployment_window_start = None
        deployment_window_end = None
        if firmware_update.scheduled_deployment:
            deployment_window_start = firmware_update.scheduled_deployment
            deployment_window_end = firmware_update.scheduled_deployment + (
                firmware_update.deployment_window_hours * 3600  # Convert to seconds
            )

        return UpdateCheckResponse(
            update_available=True,
            update_id=firmware_update.update_id,
            update_type=firmware_update.update_type,
            target_version=firmware_update.version,
            title=firmware_update.title,
            description=firmware_update.description,
            release_notes=firmware_update.release_notes,
            download_url=f"/api/v1/updates/{firmware_update.update_id}/download",
            file_size=firmware_update.file_size,
            checksum=firmware_update.checksum,
            minimum_battery_level=firmware_update.minimum_battery_level,
            required_storage_mb=firmware_update.file_size // (1024 * 1024) + 50,
            force_update=firmware_update.force_update,
            deployment_window_start=deployment_window_start,
            deployment_window_end=deployment_window_end,
        )

    async def update_progress(
        self: "UpdateService", update_id: UUID, progress: UpdateProgressReport
    ) -> None:
        """Update device update progress."""
        # Find or create device update record
        stmt = select(DeviceUpdate).where(
            and_(
                DeviceUpdate.device_id == progress.device_id,
                DeviceUpdate.update_id == update_id,
            )
        )
        result = await self.db.execute(stmt)
        device_update = result.scalar_one_or_none()

        if not device_update:
            # Create new device update record
            device_update = DeviceUpdate(
                device_id=progress.device_id,
                update_id=update_id,
                status=progress.status,
                download_progress=progress.download_progress,
                install_progress=progress.install_progress,
                error_message=progress.error_message,
                battery_level=progress.battery_level,
            )
            self.db.add(device_update)
        else:
            # Update existing record
            device_update.status = progress.status
            device_update.download_progress = progress.download_progress
            device_update.install_progress = progress.install_progress
            device_update.error_message = progress.error_message
            device_update.battery_level = progress.battery_level
            device_update.updated_at = datetime.utcnow()

            # Set completion timestamps
            if progress.status == DeviceUpdateStatus.INSTALLED:
                device_update.completed_at = datetime.utcnow()
            elif progress.status == DeviceUpdateStatus.FAILED:
                device_update.failed_at = datetime.utcnow()

        await self.db.commit()

        # Update rollout metrics
        await self._update_rollout_metrics(update_id)

    async def get_rollout_status(self: "UpdateService", update_id: UUID) -> UpdateRolloutStatus:
        """Get update rollout status."""
        # Get firmware update
        firmware_update = await self.firmware_service.get_update_by_id(update_id)
        if not firmware_update:
            raise ValueError("Firmware update not found")

        # Get device update counts
        count_query = (
            select(
                DeviceUpdate.status,
                func.count(DeviceUpdate.device_id).label("count"),  # pylint: disable=not-callable
            )
            .where(DeviceUpdate.update_id == update_id)
            .group_by(DeviceUpdate.status)
        )
        result = await self.db.execute(count_query)
        status_counts = {row.status: row.count for row in result}

        # Calculate metrics
        total_devices = sum(status_counts.values())
        pending_devices = status_counts.get(DeviceUpdateStatus.PENDING, 0)
        downloading_devices = status_counts.get(DeviceUpdateStatus.DOWNLOADING, 0)
        installing_devices = status_counts.get(DeviceUpdateStatus.INSTALLING, 0)
        completed_devices = status_counts.get(DeviceUpdateStatus.INSTALLED, 0)
        failed_devices = status_counts.get(DeviceUpdateStatus.FAILED, 0)

        success_rate = (completed_devices / total_devices * 100) if total_devices > 0 else 0.0
        failure_rate = (failed_devices / total_devices * 100) if total_devices > 0 else 0.0

        return UpdateRolloutStatus(
            update_id=update_id,
            deployment_ring=firmware_update.deployment_ring,
            total_devices=total_devices,
            pending_devices=pending_devices,
            downloading_devices=downloading_devices,
            installing_devices=installing_devices,
            completed_devices=completed_devices,
            failed_devices=failed_devices,
            success_rate=success_rate,
            failure_rate=failure_rate,
            # NOTE: Metrics calculations not implemented yet
            average_download_time_minutes=None,
            average_install_time_minutes=None,
        )

    async def get_update_metrics(self: "UpdateService", update_id: UUID) -> UpdateMetrics:
        """Get update deployment metrics."""
        rollout_status = await self.get_rollout_status(update_id)

        # Get rollback information
        firmware_update = await self.firmware_service.get_update_by_id(update_id)
        if not firmware_update:
            raise ValueError("Firmware update not found")

        return UpdateMetrics(
            update_id=update_id,
            total_devices_targeted=rollout_status.total_devices,
            devices_completed=rollout_status.completed_devices,
            devices_failed=rollout_status.failed_devices,
            devices_pending=rollout_status.pending_devices,
            success_rate_percentage=rollout_status.success_rate,
            failure_rate_percentage=rollout_status.failure_rate,
            # NOTE: Deployment time calculation not implemented yet
            average_deployment_time_hours=None,
            rollback_triggered=firmware_update.status == UpdateStatus.ROLLED_BACK,
            rollback_reason=firmware_update.rollback_reason,
        )

    async def initiate_rollback(
        self: "UpdateService", update_id: UUID, request: RollbackRequest
    ) -> None:
        """Initiate update rollback."""
        firmware_update = await self.firmware_service.get_update_by_id(update_id)
        if not firmware_update:
            raise ValueError("Firmware update not found")

        # Update firmware status
        firmware_update.status = UpdateStatus.ROLLING_BACK
        firmware_update.rollback_reason = request.reason
        firmware_update.rollback_initiated_at = datetime.utcnow()
        firmware_update.updated_at = datetime.utcnow()

        # Update device updates to rollback status
        rollback_query = (
            update(DeviceUpdate)
            .where(
                and_(
                    DeviceUpdate.update_id == update_id,
                    DeviceUpdate.status.in_(
                        [
                            DeviceUpdateStatus.PENDING,
                            DeviceUpdateStatus.DOWNLOADING,
                            DeviceUpdateStatus.INSTALLING,
                        ]
                    ),
                )
            )
            .values(
                status=DeviceUpdateStatus.ROLLED_BACK,
                updated_at=datetime.utcnow(),
            )
        )
        await self.db.execute(rollback_query)

        await self.db.commit()

    async def _update_rollout_metrics(self: "UpdateService", update_id: UUID) -> None:
        """Update rollout metrics for an update."""
        # Get current rollout status
        rollout_status = await self.get_rollout_status(update_id)

        # Find or create metrics record
        stmt = select(UpdateRolloutMetrics).where(UpdateRolloutMetrics.update_id == update_id)
        result = await self.db.execute(stmt)
        metrics = result.scalar_one_or_none()

        if not metrics:
            metrics = UpdateRolloutMetrics(
                update_id=update_id,
                total_devices=rollout_status.total_devices,
                devices_completed=rollout_status.completed_devices,
                devices_failed=rollout_status.failed_devices,
                success_rate=rollout_status.success_rate,
                failure_rate=rollout_status.failure_rate,
            )
            self.db.add(metrics)
        else:
            metrics.total_devices = rollout_status.total_devices
            metrics.devices_completed = rollout_status.completed_devices
            metrics.devices_failed = rollout_status.failed_devices
            metrics.success_rate = rollout_status.success_rate
            metrics.failure_rate = rollout_status.failure_rate
            metrics.updated_at = datetime.utcnow()

        await self.db.commit()

        # Check for auto-rollback conditions
        firmware_update = await self.firmware_service.get_update_by_id(update_id)
        if (
            firmware_update
            and firmware_update.auto_rollback_enabled
            and rollout_status.failure_rate >= firmware_update.failure_threshold_percentage
            and rollout_status.total_devices >= 10  # Minimum devices for rollback
        ):
            # Trigger auto-rollback
            await self.initiate_rollback(
                update_id,
                RollbackRequest(
                    update_id=update_id,
                    reason=(
                        f"Auto-rollback triggered: failure rate "
                        f"{rollout_status.failure_rate:.1f}% exceeded threshold "
                        f"{firmware_update.failure_threshold_percentage:.1f}%"
                    ),
                    force_immediate=True,
                ),
            )
