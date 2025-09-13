"""Audit service for comprehensive logging of moderation actions."""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

import structlog
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models import AuditLog, DecisionType
from schemas import AuditLogResponse

logger = structlog.get_logger()

class AuditService:
    """Service for handling audit logging of moderation actions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        action: str,
        actor_id: str,
        actor_type: str = "moderator",
        actor_name: Optional[str] = None,
        description: Optional[str] = None,
        queue_item_id: Optional[UUID] = None,
        decision_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log a moderation action."""

        audit_log = AuditLog(
            action=action,
            description=description,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_name=actor_name,
            queue_item_id=queue_item_id,
            decision_id=decision_id,
            context=context,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc)
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        logger.info(
            "Audit log created",
            audit_id=str(audit_log.id),
            action=action,
            actor_id=actor_id,
            actor_type=actor_type
        )

        return audit_log

    async def log_moderation_decision(
        self,
        decision_id: UUID,
        item_id: str,
        decision_type: DecisionType,
        moderator_id: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log a moderation decision action."""

        action_context = {
            "decision_type": decision_type.value,
            "reason": reason,
            **(context or {})
        }

        await self.log_action(
            action="moderation_decision",
            actor_id=moderator_id,
            actor_type="moderator",
            description=f"Made {decision_type.value} decision: {reason}",
            queue_item_id=UUID(item_id),
            decision_id=decision_id,
            context=action_context
        )

    async def log_queue_item_created(
        self,
        item_id: UUID,
        content_type: str,
        flag_reason: str,
        flagged_by_system: bool,
        flagged_by_user_id: Optional[str] = None
    ):
        """Log creation of a queue item."""

        actor_id = flagged_by_user_id if not flagged_by_system else "system"
        actor_type = "user" if not flagged_by_system else "system"

        context = {
            "content_type": content_type,
            "flag_reason": flag_reason,
            "flagged_by_system": flagged_by_system
        }

        await self.log_action(
            action="queue_item_created",
            actor_id=actor_id,
            actor_type=actor_type,
            description=f"Content flagged for {flag_reason}",
            queue_item_id=item_id,
            context=context
        )

    async def log_appeal_submitted(
        self,
        appeal_id: UUID,
        decision_id: UUID,
        appellant_id: str,
        reason: str
    ):
        """Log appeal submission."""

        await self.log_action(
            action="appeal_submitted",
            actor_id=appellant_id,
            actor_type="user",
            description=f"Appeal submitted: {reason[:100]}",
            decision_id=decision_id,
            context={"appeal_id": str(appeal_id), "reason": reason}
        )

    async def log_appeal_reviewed(
        self,
        appeal_id: UUID,
        decision_id: UUID,
        reviewer_id: str,
        resolution: str,
        approved: bool
    ):
        """Log appeal review."""

        action = "appeal_approved" if approved else "appeal_denied"

        await self.log_action(
            action=action,
            actor_id=reviewer_id,
            actor_type="moderator",
            description=f"Appeal {action}: {resolution[:100]}",
            decision_id=decision_id,
            context={
                "appeal_id": str(appeal_id),
                "resolution": resolution,
                "approved": approved
            }
        )

    async def log_bulk_action(
        self,
        action: str,
        actor_id: str,
        item_ids: List[UUID],
        context: Optional[Dict[str, Any]] = None
    ):
        """Log bulk moderation actions."""

        bulk_context = {
            "item_count": len(item_ids),
            "item_ids": [str(id) for id in item_ids],
            **(context or {})
        }

        await self.log_action(
            action=f"bulk_{action}",
            actor_id=actor_id,
            actor_type="moderator",
            description=f"Bulk {action} on {len(item_ids)} items",
            context=bulk_context
        )

    async def log_rule_change(
        self,
        rule_id: UUID,
        action: str,  # created, updated, activated, deactivated
        actor_id: str,
        changes: Optional[Dict[str, Any]] = None
    ):
        """Log moderation rule changes."""

        await self.log_action(
            action=f"rule_{action}",
            actor_id=actor_id,
            actor_type="admin",
            description=f"Moderation rule {action}",
            context={
                "rule_id": str(rule_id),
                "changes": changes or {}
            }
        )

    async def get_audit_logs(
        self,
        item_id: Optional[str] = None,
        moderator_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        days: int = 30
    ) -> List[AuditLogResponse]:
        """Get audit logs with filtering."""

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = select(AuditLog).where(AuditLog.timestamp >= cutoff_date)

        # Apply filters
        if item_id:
            query = query.where(AuditLog.queue_item_id == UUID(item_id))
        if moderator_id:
            query = query.where(AuditLog.actor_id == moderator_id)
        if action:
            query = query.where(AuditLog.action == action)

        # Order by timestamp descending
        query = query.order_by(desc(AuditLog.timestamp))

        # Apply pagination
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        return [AuditLogResponse.from_orm(log) for log in logs]

    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get activity summary for a specific user/moderator."""

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get all logs for the user
        query = select(AuditLog).where(
            and_(
                AuditLog.actor_id == user_id,
                AuditLog.timestamp >= cutoff_date
            )
        ).order_by(desc(AuditLog.timestamp))

        result = await self.db.execute(query)
        logs = result.scalars().all()

        # Aggregate activity
        actions_count = {}
        daily_activity = {}

        for log in logs:
            # Count actions
            actions_count[log.action] = actions_count.get(log.action, 0) + 1

            # Count daily activity
            day = log.timestamp.date().isoformat()
            daily_activity[day] = daily_activity.get(day, 0) + 1

        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": len(logs),
            "actions_by_type": actions_count,
            "daily_activity": daily_activity,
            "most_recent_action": logs[0].timestamp.isoformat() if logs else None,
            "actions_per_day": len(logs) / days if days > 0 else 0
        }

    async def get_system_activity_summary(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get system-wide activity summary."""

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get all logs in the period
        query = select(AuditLog).where(AuditLog.timestamp >= cutoff_date)
        result = await self.db.execute(query)
        logs = result.scalars().all()

        # Aggregate data
        total_actions = len(logs)
        actions_by_type = {}
        actions_by_actor_type = {}
        unique_actors = set()

        for log in logs:
            actions_by_type[log.action] = actions_by_type.get(log.action, 0) + 1
            actions_by_actor_type[log.actor_type] = actions_by_actor_type.get(log.actor_type, 0) + 1
            unique_actors.add(log.actor_id)

        return {
            "period_days": days,
            "total_actions": total_actions,
            "unique_actors": len(unique_actors),
            "actions_by_type": actions_by_type,
            "actions_by_actor_type": actions_by_actor_type,
            "actions_per_day": total_actions / days if days > 0 else 0
        }
