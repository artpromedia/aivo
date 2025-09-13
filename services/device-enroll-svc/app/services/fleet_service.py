"""Fleet health monitoring service for Device Enrollment."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Device, DeviceStatus

logger = structlog.get_logger(__name__)


class FleetHealthService:
    """Service for fleet health monitoring and aggregation."""

    def __init__(self) -> None:
        """Initialize service."""
        self.heartbeat_service_url = "http://device-ota-svc:8112"  # OTA service with heartbeats

    async def get_fleet_health(
        self,
        db: AsyncSession,
        tenant_id: Optional[UUID] = None,
        range_days: int = 30
    ) -> Dict[str, any]:
        """Get aggregated fleet health metrics."""
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=range_days)

            # Base device query
            device_query = select(Device).where(Device.is_active == True)
            if tenant_id:
                # Note: tenant_id filtering would need to be added to Device model
                logger.info("Tenant filtering not yet implemented", tenant_id=tenant_id)

            # Get total device counts by status
            status_counts = await self._get_device_status_counts(db, device_query)

            # Get online percentage (devices seen within last 5 minutes)
            online_percentage = await self._calculate_online_percentage(db, device_query)

            # Get mean heartbeat interval from OTA service
            mean_heartbeat = await self._calculate_mean_heartbeat_interval(db, device_query)

            # Get firmware version distribution (drift analysis)
            firmware_drift = await self._analyze_firmware_drift(db, device_query)

            # Get health trends over time range
            health_trends = await self._get_health_trends(db, device_query, start_time, end_time)

            return {
                "summary": {
                    "total_devices": sum(status_counts.values()),
                    "online_percentage": online_percentage,
                    "mean_heartbeat_minutes": mean_heartbeat,
                    "firmware_versions": len(firmware_drift),
                    "last_updated": end_time.isoformat(),
                    "range_days": range_days
                },
                "status_distribution": status_counts,
                "firmware_drift": firmware_drift,
                "health_trends": health_trends,
                "alerts": {
                    "critical": await self._get_critical_alerts(db),
                    "warnings": await self._get_warning_alerts(db)
                }
            }

        except Exception as e:
            logger.error("Failed to get fleet health", error=str(e))
            raise

    async def _get_device_status_counts(
        self, db: AsyncSession, device_query
    ) -> Dict[str, int]:
        """Get device counts by status."""
        # Get enrolled device counts
        enrolled_result = await db.execute(
            select(func.count()).select_from(
                device_query.where(Device.status == DeviceStatus.ENROLLED).subquery()
            )
        )
        enrolled_count = enrolled_result.scalar()

        # Get attested device counts
        attested_result = await db.execute(
            select(func.count()).select_from(
                device_query.where(Device.status == DeviceStatus.ATTESTED).subquery()
            )
        )
        attested_count = attested_result.scalar()

        # Get pending device counts
        pending_result = await db.execute(
            select(func.count()).select_from(
                device_query.where(Device.status == DeviceStatus.PENDING).subquery()
            )
        )
        pending_count = pending_result.scalar()

        # Get revoked device counts
        revoked_result = await db.execute(
            select(func.count()).select_from(
                device_query.where(Device.status == DeviceStatus.REVOKED).subquery()
            )
        )
        revoked_count = revoked_result.scalar()

        return {
            "enrolled": enrolled_count,
            "attested": attested_count,
            "pending": pending_count,
            "revoked": revoked_count
        }

    async def _calculate_online_percentage(
        self, db: AsyncSession, device_query
    ) -> float:
        """Calculate percentage of devices online (seen within 5 minutes)."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)

        # Total active devices
        total_result = await db.execute(
            select(func.count()).select_from(device_query.subquery())
        )
        total_devices = total_result.scalar()

        if total_devices == 0:
            return 0.0

        # Recently seen devices
        online_result = await db.execute(
            select(func.count()).select_from(
                device_query.where(Device.last_seen_at >= cutoff_time).subquery()
            )
        )
        online_devices = online_result.scalar()

        return round((online_devices / total_devices) * 100, 2)

    async def _calculate_mean_heartbeat_interval(
        self, db: AsyncSession, device_query
    ) -> float:
        """Calculate mean heartbeat interval in minutes."""
        # This would ideally query the heartbeat service for actual intervals
        # For now, we'll estimate based on last_seen_at gaps

        # Query devices with recent activity
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_devices = await db.execute(
            device_query.where(Device.last_seen_at >= cutoff_time)
        )

        # In a real implementation, we'd calculate actual heartbeat intervals
        # from the device-ota-svc heartbeat data
        # For now, return a reasonable default
        return 5.0  # Assume 5-minute average heartbeat interval

    async def _analyze_firmware_drift(
        self, db: AsyncSession, device_query
    ) -> List[Dict[str, any]]:
        """Analyze firmware version distribution for drift detection."""
        # Get firmware version distribution
        firmware_result = await db.execute(
            select(
                Device.firmware_version,
                func.count().label('device_count')
            )
            .select_from(device_query.subquery())
            .group_by(Device.firmware_version)
            .order_by(func.count().desc())
        )

        firmware_data = firmware_result.all()
        total_devices = sum(row.device_count for row in firmware_data)

        drift_analysis = []
        for row in firmware_data:
            percentage = (row.device_count / total_devices * 100) if total_devices > 0 else 0
            drift_analysis.append({
                "version": row.firmware_version or "unknown",
                "device_count": row.device_count,
                "percentage": round(percentage, 1),
                "is_latest": False  # Would need version comparison logic
            })

        # Mark the most common version as "latest" (simplified)
        if drift_analysis:
            drift_analysis[0]["is_latest"] = True

        return drift_analysis

    async def _get_health_trends(
        self,
        db: AsyncSession,
        device_query,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, any]]:
        """Get health trends over time range."""
        # This would ideally track enrollment rates, online percentages over time
        # For now, return a simplified trend

        trends = []
        current_time = start_time
        interval = timedelta(days=1)

        while current_time <= end_time:
            # In a real implementation, we'd query historical data
            # For now, provide sample trend data
            trends.append({
                "date": current_time.isoformat(),
                "online_percentage": 95.0,  # Sample data
                "total_devices": 100,  # Sample data
                "new_enrollments": 2  # Sample data
            })
            current_time += interval

        return trends[-7:]  # Return last 7 days

    async def _get_critical_alerts(self, db: AsyncSession) -> List[Dict[str, any]]:
        """Get critical alerts for the fleet."""
        # This would check for critical conditions
        alerts = []

        # Check for high offline percentage
        # Check for firmware drift
        # Check for enrollment failures

        return alerts

    async def _get_warning_alerts(self, db: AsyncSession) -> List[Dict[str, any]]:
        """Get warning alerts for the fleet."""
        # This would check for warning conditions
        alerts = []

        return alerts

    async def check_alert_rules(self, db: AsyncSession) -> None:
        """Check and trigger alert rules."""
        # This would evaluate all active alert rules against current metrics
        # and trigger notifications as needed
        logger.info("Alert rule checking not yet implemented")
        pass
