"""Firmware update service for Device OTA & Heartbeat Service."""
# flake8: noqa: E501

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    DeploymentRing,
    DeviceUpdate,
    DeviceUpdateStatus,
    FirmwareUpdate,
    UpdateStatus,
    UpdateType,
)
from app.schemas import FirmwareUpdateRequest


class FirmwareService:
    """Service for managing firmware updates."""

    def __init__(self: "FirmwareService", db: AsyncSession) -> None:
        """Initialize service."""
        self.db = db

    async def create_update(
        self: "FirmwareService", request: FirmwareUpdateRequest
    ) -> FirmwareUpdate:
        """Create a new firmware update."""
        # Create firmware update
        firmware_update = FirmwareUpdate(
            update_type=request.update_type,
            version=request.version,
            previous_version=request.previous_version,
            title=request.title,
            description=request.description,
            release_notes=request.release_notes,
            changelog=request.changelog,
            target_device_types=request.target_device_types,
            minimum_battery_level=request.minimum_battery_level,
            file_path=request.file_path,
            file_size=request.file_size,
            checksum=request.checksum,
            signature=request.signature,
            canary_percentage=request.canary_percentage,
            early_percentage=request.early_percentage,
            broad_percentage=request.broad_percentage,
            auto_rollback_enabled=request.auto_rollback_enabled,
            failure_threshold_percentage=request.failure_threshold_percentage,
            scheduled_deployment=request.scheduled_deployment,
            deployment_window_hours=request.deployment_window_hours,
            force_update=request.force_update,
            status=UpdateStatus.CREATED,
            deployment_ring=DeploymentRing.CANARY,
        )

        self.db.add(firmware_update)
        await self.db.commit()
        await self.db.refresh(firmware_update)

        return firmware_update

    async def list_updates(
        self: "FirmwareService",
        page: int = 1,
        size: int = 50,
        status_filter: UpdateStatus | None = None,
        ring_filter: DeploymentRing | None = None,
    ) -> tuple[list[FirmwareUpdate], int]:
        """List firmware updates with pagination."""
        # Build query
        query = select(FirmwareUpdate).where(
            ~FirmwareUpdate.is_deleted  # pylint: disable=no-member
        )

        if status_filter:
            query = query.where(FirmwareUpdate.status == status_filter)

        if ring_filter:
            query = query.where(FirmwareUpdate.deployment_ring == ring_filter)

        # Get all results first to count them (simple approach)
        all_query = query.order_by(FirmwareUpdate.created_at.desc())
        all_result = await self.db.execute(all_query)
        all_updates = all_result.scalars().all()
        total = len(all_updates)

        # Get paginated results
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        updates = all_updates[start_idx:end_idx]

        return list(updates), total

    async def get_update_by_id(
        self: "FirmwareService", update_id: UUID
    ) -> FirmwareUpdate | None:
        """Get firmware update by ID."""
        stmt = (
            select(FirmwareUpdate)
            .options(selectinload(FirmwareUpdate.device_updates))  # pylint: disable=no-member
            .where(
                and_(
                    FirmwareUpdate.update_id == update_id,
                    ~FirmwareUpdate.is_deleted,  # pylint: disable=no-member
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def deploy_to_ring(
        self: "FirmwareService", update_id: UUID, target_ring: DeploymentRing
    ) -> None:
        """Deploy update to a specific deployment ring."""
        firmware_update = await self.get_update_by_id(update_id)
        if not firmware_update:
            raise ValueError("Firmware update not found")

        # Update deployment ring and status
        firmware_update.deployment_ring = target_ring
        firmware_update.status = UpdateStatus.DEPLOYED
        firmware_update.deployed_at = datetime.utcnow()
        firmware_update.updated_at = datetime.utcnow()

        await self.db.commit()

    async def get_latest_update_for_device(
        self: "FirmwareService",
        device_type: str,
        current_version: str,
        update_type: UpdateType = UpdateType.FIRMWARE,
    ) -> FirmwareUpdate | None:
        """Get the latest available update for a device."""
        stmt = (
            select(FirmwareUpdate)
            .where(
                and_(
                    FirmwareUpdate.target_device_types.op("@>")(f'["{device_type}"]'),
                    FirmwareUpdate.update_type == update_type,
                    FirmwareUpdate.status == UpdateStatus.DEPLOYED,
                    FirmwareUpdate.version != current_version,
                    ~FirmwareUpdate.is_deleted,  # pylint: disable=no-member
                )
            )
            .order_by(FirmwareUpdate.created_at.desc())
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def is_device_eligible_for_update(
        self: "FirmwareService",
        firmware_update: FirmwareUpdate,
        device_id: UUID,
        battery_level: int | None = None,
        storage_available_mb: int | None = None,
    ) -> tuple[bool, str | None]:
        """Check if device is eligible for update."""
        # Check battery level
        if (
            battery_level is not None
            and battery_level < firmware_update.minimum_battery_level
        ):
            return (
                False,
                f"Battery level {battery_level}% below minimum "
                f"{firmware_update.minimum_battery_level}%"
            )

        # Check storage space (estimate 50MB overhead)
        required_storage = firmware_update.file_size // (1024 * 1024) + 50
        if (
            storage_available_mb is not None
            and storage_available_mb < required_storage
        ):
            return (
                False,
                f"Insufficient storage: {storage_available_mb}MB available, "
                f"{required_storage}MB required"
            )

        # Check if device already has this update
        stmt = select(DeviceUpdate).where(
            and_(
                DeviceUpdate.device_id == device_id,
                DeviceUpdate.update_id == firmware_update.update_id,
                DeviceUpdate.status.in_([
                    DeviceUpdateStatus.INSTALLED,
                    DeviceUpdateStatus.INSTALLING,
                    DeviceUpdateStatus.DOWNLOADING,
                ]),
            )
        )
        result = await self.db.execute(stmt)
        existing_update = result.scalar_one_or_none()

        if existing_update:
            return False, f"Device already has update {existing_update.status.value}"

        return True, None
