"""Heartbeat service for Device OTA & Heartbeat Service."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeviceHeartbeat
from app.schemas import HeartbeatRequest, HeartbeatResponse

if TYPE_CHECKING:
    pass


class HeartbeatService:
    """Service for managing device heartbeats."""

    def __init__(self: "HeartbeatService", db: AsyncSession) -> None:
        """Initialize service."""
        self.db = db

    async def process_heartbeat(
        self: "HeartbeatService", heartbeat: HeartbeatRequest
    ) -> HeartbeatResponse:
        """Process incoming device heartbeat."""
        # Create heartbeat record
        device_heartbeat = DeviceHeartbeat(
            device_id=heartbeat.device_id,
            device_type=heartbeat.device_type,
            hardware_model=heartbeat.hardware_model,
            serial_number=heartbeat.serial_number,
            firmware_version=heartbeat.firmware_version,
            application_version=heartbeat.application_version,
            bootloader_version=heartbeat.bootloader_version,
            uptime_seconds=heartbeat.uptime_seconds,
            battery_level=heartbeat.battery_level,
            charging_status=heartbeat.charging_status,
            cpu_usage_percent=heartbeat.cpu_usage_percent,
            memory_usage_percent=heartbeat.memory_usage_percent,
            storage_used_mb=heartbeat.storage_used_mb,
            storage_total_mb=heartbeat.storage_total_mb,
            network_type=heartbeat.network_type,
            signal_strength=heartbeat.signal_strength,
            ip_address=heartbeat.ip_address,
            latitude=heartbeat.latitude,
            longitude=heartbeat.longitude,
            location_accuracy=heartbeat.location_accuracy,
            pending_update_id=heartbeat.pending_update_id,
            last_update_check=heartbeat.last_update_check,
            recent_errors=heartbeat.recent_errors,
            crash_count_24h=heartbeat.crash_count_24h,
            last_crash_at=heartbeat.last_crash_at,
            custom_metrics=heartbeat.custom_metrics,
            tags=heartbeat.tags,
        )

        self.db.add(device_heartbeat)
        await self.db.commit()
        await self.db.refresh(device_heartbeat)

        # Determine if device should check for updates
        update_check_required = await self._should_check_for_updates(
            heartbeat.device_id, heartbeat.last_update_check
        )

        return HeartbeatResponse(
            heartbeat_id=device_heartbeat.heartbeat_id,
            device_id=heartbeat.device_id,
            received_at=device_heartbeat.received_at,
            update_check_required=update_check_required,
            # NOTE: Configuration updates not implemented
            configuration_update=None,
            # NOTE: Device commands not implemented
            commands=None,
        )

    async def get_device_heartbeats(
        self: "HeartbeatService", device_id: UUID, limit: int = 50
    ) -> list[dict]:
        """Get recent heartbeats for a device."""
        stmt = (
            select(DeviceHeartbeat)
            .where(DeviceHeartbeat.device_id == device_id)
            .order_by(desc(DeviceHeartbeat.received_at))
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        heartbeats = result.scalars().all()

        return [
            {
                "heartbeat_id": str(hb.heartbeat_id),
                "received_at": hb.received_at.isoformat(),
                "firmware_version": hb.firmware_version,
                "battery_level": hb.battery_level,
                "uptime_seconds": hb.uptime_seconds,
                "network_type": hb.network_type,
                "signal_strength": hb.signal_strength,
            }
            for hb in heartbeats
        ]

    async def get_device_status(self: "HeartbeatService", device_id: UUID) -> dict:
        """Get current device status based on latest heartbeat."""
        # Get latest heartbeat
        stmt = (
            select(DeviceHeartbeat)
            .where(DeviceHeartbeat.device_id == device_id)
            .order_by(desc(DeviceHeartbeat.received_at))
            .limit(1)
        )

        result = await self.db.execute(stmt)
        latest_heartbeat = result.scalar_one_or_none()

        if not latest_heartbeat:
            return {
                "device_id": str(device_id),
                "status": "unknown",
                "last_seen": None,
                "message": "No heartbeats received",
            }

        # Determine device status
        now = datetime.utcnow()
        time_since_heartbeat = now - latest_heartbeat.received_at

        if time_since_heartbeat <= timedelta(minutes=5):
            status = "online"
        elif time_since_heartbeat <= timedelta(minutes=30):
            status = "recently_seen"
        else:
            status = "offline"

        return {
            "device_id": str(device_id),
            "status": status,
            "last_seen": latest_heartbeat.received_at.isoformat(),
            "firmware_version": latest_heartbeat.firmware_version,
            "battery_level": latest_heartbeat.battery_level,
            "uptime_seconds": latest_heartbeat.uptime_seconds,
            "network_type": latest_heartbeat.network_type,
            "time_since_heartbeat_minutes": int(time_since_heartbeat.total_seconds() / 60),
        }

    async def _should_check_for_updates(
        self: "HeartbeatService", _device_id: UUID, last_update_check: datetime | None
    ) -> bool:
        """Determine if device should check for updates."""
        # If never checked, should check
        if not last_update_check:
            return True

        # Check every 4 hours
        check_interval = timedelta(hours=4)
        return datetime.utcnow() - last_update_check > check_interval
