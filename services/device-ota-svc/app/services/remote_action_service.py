"""Remote device action service for Device OTA & Heartbeat Service."""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RemoteActionStatus, RemoteActionType, RemoteDeviceAction

logger = structlog.get_logger(__name__)


class RemoteActionService:
    """Service for managing remote device actions."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service."""
        self.db = db

    async def create_action(
        self,
        device_id: UUID,
        action_type: RemoteActionType,
        initiated_by: UUID,
        reason: Optional[str] = None,
        parameters: Optional[dict] = None,
        priority: int = 1,
        correlation_id: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> RemoteDeviceAction:
        """Create a new remote device action."""
        try:
            action = RemoteDeviceAction(
                device_id=device_id,
                action_type=action_type,
                reason=reason,
                parameters=parameters or {},
                priority=priority,
                initiated_by=initiated_by,
                correlation_id=correlation_id,
                client_ip=client_ip,
            )

            self.db.add(action)
            await self.db.commit()
            await self.db.refresh(action)

            logger.info(
                "Remote device action created",
                action_id=action.action_id,
                device_id=device_id,
                action_type=action_type.value,
                initiated_by=initiated_by,
                priority=priority,
            )

            return action

        except Exception as e:
            logger.error(
                "Failed to create remote device action",
                device_id=device_id,
                action_type=action_type.value,
                error=str(e),
            )
            await self.db.rollback()
            raise

    async def get_pending_actions_for_device(
        self, device_id: UUID, limit: int = 10
    ) -> List[RemoteDeviceAction]:
        """Get pending actions for a specific device."""
        try:
            stmt = (
                select(RemoteDeviceAction)
                .where(
                    and_(
                        RemoteDeviceAction.device_id == device_id,
                        RemoteDeviceAction.status.in_([
                            RemoteActionStatus.PENDING,
                            RemoteActionStatus.SENT
                        ]),
                        RemoteDeviceAction.expires_at > datetime.utcnow(),
                    )
                )
                .order_by(
                    desc(RemoteDeviceAction.priority),
                    RemoteDeviceAction.created_at
                )
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(
                "Failed to get pending actions for device",
                device_id=device_id,
                error=str(e),
            )
            raise

    async def mark_action_sent(
        self, action_id: UUID, sent_at: Optional[datetime] = None
    ) -> bool:
        """Mark an action as sent to the device."""
        try:
            if sent_at is None:
                sent_at = datetime.utcnow()

            result = await self.db.execute(
                update(RemoteDeviceAction)
                .where(RemoteDeviceAction.action_id == action_id)
                .values(
                    status=RemoteActionStatus.SENT,
                    sent_at=sent_at,
                    attempts=RemoteDeviceAction.attempts + 1,
                    updated_at=datetime.utcnow(),
                )
            )
            await self.db.commit()

            if result.rowcount > 0:
                logger.info("Remote action marked as sent", action_id=action_id)
                return True
            else:
                logger.warning("Remote action not found for sent update", action_id=action_id)
                return False

        except Exception as e:
            logger.error("Failed to mark action as sent", action_id=action_id, error=str(e))
            await self.db.rollback()
            raise

    async def mark_action_acknowledged(
        self, action_id: UUID, acknowledged_at: Optional[datetime] = None
    ) -> bool:
        """Mark an action as acknowledged by the device."""
        try:
            if acknowledged_at is None:
                acknowledged_at = datetime.utcnow()

            result = await self.db.execute(
                update(RemoteDeviceAction)
                .where(RemoteDeviceAction.action_id == action_id)
                .values(
                    status=RemoteActionStatus.ACKNOWLEDGED,
                    acknowledged_at=acknowledged_at,
                    updated_at=datetime.utcnow(),
                )
            )
            await self.db.commit()

            if result.rowcount > 0:
                logger.info("Remote action acknowledged", action_id=action_id)
                return True
            else:
                logger.warning("Remote action not found for acknowledgment", action_id=action_id)
                return False

        except Exception as e:
            logger.error("Failed to mark action as acknowledged", action_id=action_id, error=str(e))
            await self.db.rollback()
            raise

    async def mark_action_completed(
        self,
        action_id: UUID,
        result_data: Optional[dict] = None,
        device_response: Optional[dict] = None,
        completed_at: Optional[datetime] = None,
    ) -> bool:
        """Mark an action as completed."""
        try:
            if completed_at is None:
                completed_at = datetime.utcnow()

            result = await self.db.execute(
                update(RemoteDeviceAction)
                .where(RemoteDeviceAction.action_id == action_id)
                .values(
                    status=RemoteActionStatus.COMPLETED,
                    result_data=result_data,
                    device_response=device_response,
                    completed_at=completed_at,
                    updated_at=datetime.utcnow(),
                )
            )
            await self.db.commit()

            if result.rowcount > 0:
                logger.info("Remote action completed", action_id=action_id)
                return True
            else:
                logger.warning("Remote action not found for completion", action_id=action_id)
                return False

        except Exception as e:
            logger.error("Failed to mark action as completed", action_id=action_id, error=str(e))
            await self.db.rollback()
            raise

    async def mark_action_failed(
        self,
        action_id: UUID,
        error_message: str,
        device_response: Optional[dict] = None,
    ) -> bool:
        """Mark an action as failed."""
        try:
            result = await self.db.execute(
                update(RemoteDeviceAction)
                .where(RemoteDeviceAction.action_id == action_id)
                .values(
                    status=RemoteActionStatus.FAILED,
                    error_message=error_message,
                    device_response=device_response,
                    updated_at=datetime.utcnow(),
                )
            )
            await self.db.commit()

            if result.rowcount > 0:
                logger.warning(
                    "Remote action failed",
                    action_id=action_id,
                    error=error_message,
                )
                return True
            else:
                logger.warning("Remote action not found for failure update", action_id=action_id)
                return False

        except Exception as e:
            logger.error("Failed to mark action as failed", action_id=action_id, error=str(e))
            await self.db.rollback()
            raise

    async def get_action_by_id(self, action_id: UUID) -> Optional[RemoteDeviceAction]:
        """Get a specific action by ID."""
        try:
            stmt = select(RemoteDeviceAction).where(RemoteDeviceAction.action_id == action_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error("Failed to get action by ID", action_id=action_id, error=str(e))
            raise

    async def get_device_actions(
        self,
        device_id: UUID,
        status_filter: Optional[RemoteActionStatus] = None,
        limit: int = 50,
    ) -> List[RemoteDeviceAction]:
        """Get actions for a specific device with optional status filtering."""
        try:
            stmt = select(RemoteDeviceAction).where(RemoteDeviceAction.device_id == device_id)

            if status_filter:
                stmt = stmt.where(RemoteDeviceAction.status == status_filter)

            stmt = stmt.order_by(desc(RemoteDeviceAction.created_at)).limit(limit)

            result = await self.db.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(
                "Failed to get device actions",
                device_id=device_id,
                status_filter=status_filter,
                error=str(e),
            )
            raise

    async def cleanup_expired_actions(self) -> int:
        """Clean up expired actions that haven't been processed."""
        try:
            current_time = datetime.utcnow()

            # Mark expired pending/sent actions as expired
            result = await self.db.execute(
                update(RemoteDeviceAction)
                .where(
                    and_(
                        RemoteDeviceAction.expires_at <= current_time,
                        RemoteDeviceAction.status.in_([
                            RemoteActionStatus.PENDING,
                            RemoteActionStatus.SENT,
                        ]),
                    )
                )
                .values(
                    status=RemoteActionStatus.EXPIRED,
                    updated_at=current_time,
                )
            )
            await self.db.commit()

            expired_count = result.rowcount
            if expired_count > 0:
                logger.info("Expired remote actions cleaned up", count=expired_count)

            return expired_count

        except Exception as e:
            logger.error("Failed to cleanup expired actions", error=str(e))
            await self.db.rollback()
            raise

    async def retry_failed_actions(self, max_retries: int = 3) -> int:
        """Retry failed actions that haven't exceeded max attempts."""
        try:
            current_time = datetime.utcnow()
            retry_cutoff = current_time - timedelta(minutes=30)  # Wait 30 minutes before retry

            # Find failed actions eligible for retry
            stmt = select(RemoteDeviceAction).where(
                and_(
                    RemoteDeviceAction.status == RemoteActionStatus.FAILED,
                    RemoteDeviceAction.attempts < max_retries,
                    RemoteDeviceAction.updated_at <= retry_cutoff,
                    RemoteDeviceAction.expires_at > current_time,
                )
            )

            result = await self.db.execute(stmt)
            failed_actions = result.scalars().all()

            retry_count = 0
            for action in failed_actions:
                await self.db.execute(
                    update(RemoteDeviceAction)
                    .where(RemoteDeviceAction.action_id == action.action_id)
                    .values(
                        status=RemoteActionStatus.PENDING,
                        error_message=None,
                        updated_at=current_time,
                    )
                )
                retry_count += 1

            if retry_count > 0:
                await self.db.commit()
                logger.info("Remote actions retried", count=retry_count)

            return retry_count

        except Exception as e:
            logger.error("Failed to retry failed actions", error=str(e))
            await self.db.rollback()
            raise

    async def get_action_statistics(self, days: int = 7) -> dict:
        """Get action statistics for the last N days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Count actions by status
            status_counts = {}
            for status in RemoteActionStatus:
                stmt = select(RemoteDeviceAction).where(
                    and_(
                        RemoteDeviceAction.status == status,
                        RemoteDeviceAction.created_at >= cutoff_date,
                    )
                )
                result = await self.db.execute(stmt)
                status_counts[status.value] = len(result.scalars().all())

            # Count actions by type
            type_counts = {}
            for action_type in RemoteActionType:
                stmt = select(RemoteDeviceAction).where(
                    and_(
                        RemoteDeviceAction.action_type == action_type,
                        RemoteDeviceAction.created_at >= cutoff_date,
                    )
                )
                result = await self.db.execute(stmt)
                type_counts[action_type.value] = len(result.scalars().all())

            return {
                "period_days": days,
                "status_distribution": status_counts,
                "action_type_distribution": type_counts,
                "total_actions": sum(status_counts.values()),
            }

        except Exception as e:
            logger.error("Failed to get action statistics", error=str(e))
            raise
