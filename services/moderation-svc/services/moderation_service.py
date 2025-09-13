"""Core moderation service for processing content and decisions."""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select, and_, or_, desc, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import (
    ModerationQueueItem,
    ModerationDecision,
    ContentType,
    ModerationStatus,
    DecisionType,
    SeverityLevel,
    FlagReason
)
from schemas import (
    QueueItemResponse,
    QueueListResponse,
    ModerationDecisionResponse,
    QueueStatsResponse
)

logger = structlog.get_logger()

class ModerationService:
    """Service for handling content moderation operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_queue_items(
        self,
        status_filter: Optional[ModerationStatus] = None,
        content_type: Optional[ContentType] = None,
        severity: Optional[SeverityLevel] = None,
        limit: int = 50,
        offset: int = 0
    ) -> QueueListResponse:
        """Get moderation queue items with filtering and pagination."""

        # Build query with filters
        query = select(ModerationQueueItem).options(
            selectinload(ModerationQueueItem.decisions)
        )

        conditions = []
        if status_filter:
            conditions.append(ModerationQueueItem.status == status_filter)
        if content_type:
            conditions.append(ModerationQueueItem.content_type == content_type)
        if severity:
            conditions.append(ModerationQueueItem.severity_level == severity)

        if conditions:
            query = query.where(and_(*conditions))

        # Order by priority: severity desc, flagged_at asc
        query = query.order_by(
            desc(ModerationQueueItem.severity_level),
            ModerationQueueItem.flagged_at
        )

        # Get total count for pagination
        count_query = select(func.count(ModerationQueueItem.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_count = (await self.db.execute(count_query)).scalar()

        # Apply pagination
        items_query = query.offset(offset).limit(limit)
        result = await self.db.execute(items_query)
        items = result.scalars().all()

        # Transform to response objects
        queue_items = []
        for item in items:
            # Get the latest decision if any
            latest_decision = None
            if item.decisions:
                latest_decision = max(item.decisions, key=lambda d: d.decided_at)
                latest_decision = ModerationDecisionResponse.from_orm(latest_decision)

            queue_item = QueueItemResponse.from_orm(item)
            queue_item.latest_decision = latest_decision
            queue_items.append(queue_item)

        return QueueListResponse(
            items=queue_items,
            total_count=total_count,
            page_size=limit,
            offset=offset,
            has_more=offset + len(items) < total_count
        )

    async def get_queue_item(self, item_id: str) -> Optional[QueueItemResponse]:
        """Get a specific queue item by ID."""

        query = select(ModerationQueueItem).options(
            selectinload(ModerationQueueItem.decisions)
        ).where(ModerationQueueItem.id == UUID(item_id))

        result = await self.db.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            return None

        # Get the latest decision if any
        latest_decision = None
        if item.decisions:
            latest_decision = max(item.decisions, key=lambda d: d.decided_at)
            latest_decision = ModerationDecisionResponse.from_orm(latest_decision)

        queue_item = QueueItemResponse.from_orm(item)
        queue_item.latest_decision = latest_decision

        return queue_item

    async def make_decision(
        self,
        item_id: str,
        decision_type: DecisionType,
        reason: str,
        moderator_id: str,
        notes: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Make a moderation decision on a queue item."""

        # Get the queue item
        item_uuid = UUID(item_id)
        query = select(ModerationQueueItem).where(ModerationQueueItem.id == item_uuid)
        result = await self.db.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            raise ValueError(f"Queue item {item_id} not found")

        if item.status in [ModerationStatus.APPROVED, ModerationStatus.HARD_BLOCKED]:
            raise ValueError(f"Cannot modify item with status {item.status}")

        # Create the decision
        decision = ModerationDecision(
            queue_item_id=item_uuid,
            decision_type=decision_type,
            reason=reason,
            notes=notes,
            moderator_id=moderator_id,
            expires_at=expires_at,
            decided_at=datetime.now(timezone.utc)
        )

        # Update item status based on decision
        status_mapping = {
            DecisionType.APPROVE: ModerationStatus.APPROVED,
            DecisionType.SOFT_BLOCK: ModerationStatus.SOFT_BLOCKED,
            DecisionType.HARD_BLOCK: ModerationStatus.HARD_BLOCKED,
            DecisionType.ESCALATE: ModerationStatus.IN_REVIEW,
        }

        new_status = status_mapping.get(decision_type, ModerationStatus.IN_REVIEW)
        item.status = new_status
        item.reviewed_at = datetime.now(timezone.utc)

        # Set expiration for temporary blocks
        if decision_type in [DecisionType.SOFT_BLOCK, DecisionType.HARD_BLOCK] and expires_at:
            item.expires_at = expires_at

        # Set appeal deadline for blocks
        if decision_type in [DecisionType.SOFT_BLOCK, DecisionType.HARD_BLOCK]:
            decision.appeal_deadline = datetime.now(timezone.utc) + timedelta(days=7)

        self.db.add(decision)
        await self.db.commit()
        await self.db.refresh(decision)

        logger.info(
            "Moderation decision created",
            decision_id=str(decision.id),
            item_id=item_id,
            decision_type=decision_type.value,
            moderator_id=moderator_id
        )

        return {
            "id": str(decision.id),
            "queue_item_id": item_id,
            "decision_type": decision_type,
            "status": new_status,
            "decided_at": decision.decided_at,
            "expires_at": decision.expires_at
        }

    async def update_learner_pipeline(self, item_id: str, decision_type: DecisionType):
        """Update learner pipeline to reflect moderation decision."""

        # This would integrate with the actual learner pipeline
        # For now, we'll log the action that would be taken

        actions = {
            DecisionType.APPROVE: "Content visible in learner pipeline",
            DecisionType.SOFT_BLOCK: "Content hidden with warning in learner pipeline",
            DecisionType.HARD_BLOCK: "Content completely removed from learner pipeline",
            DecisionType.ESCALATE: "Content marked for human review in pipeline"
        }

        action = actions.get(decision_type, "No pipeline action")

        logger.info(
            "Learner pipeline updated",
            item_id=item_id,
            decision_type=decision_type.value,
            pipeline_action=action
        )

        # TODO: Implement actual pipeline integration
        # This could involve:
        # - Calling learner service API
        # - Publishing events to message queue
        # - Updating content visibility flags
        # - Triggering cache invalidation

    async def get_queue_stats(self, days: int = 30) -> QueueStatsResponse:
        """Get moderation queue statistics."""

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Basic counts
        pending_query = select(func.count(ModerationQueueItem.id)).where(
            ModerationQueueItem.status == ModerationStatus.PENDING
        )
        pending_count = (await self.db.execute(pending_query)).scalar()

        in_review_query = select(func.count(ModerationQueueItem.id)).where(
            ModerationQueueItem.status == ModerationStatus.IN_REVIEW
        )
        in_review_count = (await self.db.execute(in_review_query)).scalar()

        # Resolved counts
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        resolved_today_query = select(func.count(ModerationQueueItem.id)).where(
            and_(
                ModerationQueueItem.reviewed_at >= today_start,
                ModerationQueueItem.status.in_([
                    ModerationStatus.APPROVED,
                    ModerationStatus.SOFT_BLOCKED,
                    ModerationStatus.HARD_BLOCKED
                ])
            )
        )
        resolved_today = (await self.db.execute(resolved_today_query)).scalar()

        resolved_week_query = select(func.count(ModerationQueueItem.id)).where(
            and_(
                ModerationQueueItem.reviewed_at >= week_start,
                ModerationQueueItem.status.in_([
                    ModerationStatus.APPROVED,
                    ModerationStatus.SOFT_BLOCKED,
                    ModerationStatus.HARD_BLOCKED
                ])
            )
        )
        resolved_week = (await self.db.execute(resolved_week_query)).scalar()

        # Group by content type
        content_type_query = select(
            ModerationQueueItem.content_type,
            func.count(ModerationQueueItem.id)
        ).where(
            ModerationQueueItem.flagged_at >= cutoff_date
        ).group_by(ModerationQueueItem.content_type)

        content_type_result = await self.db.execute(content_type_query)
        by_content_type = {
            content_type.value: count
            for content_type, count in content_type_result.fetchall()
        }

        # Group by severity
        severity_query = select(
            ModerationQueueItem.severity_level,
            func.count(ModerationQueueItem.id)
        ).where(
            ModerationQueueItem.flagged_at >= cutoff_date
        ).group_by(ModerationQueueItem.severity_level)

        severity_result = await self.db.execute(severity_query)
        by_severity = {
            severity.value: count
            for severity, count in severity_result.fetchall()
        }

        # Group by status
        status_query = select(
            ModerationQueueItem.status,
            func.count(ModerationQueueItem.id)
        ).where(
            ModerationQueueItem.flagged_at >= cutoff_date
        ).group_by(ModerationQueueItem.status)

        status_result = await self.db.execute(status_query)
        by_status = {
            status.value: count
            for status, count in status_result.fetchall()
        }

        # Group by flag reason
        flag_reason_query = select(
            ModerationQueueItem.flag_reason,
            func.count(ModerationQueueItem.id)
        ).where(
            ModerationQueueItem.flagged_at >= cutoff_date
        ).group_by(ModerationQueueItem.flag_reason)

        flag_reason_result = await self.db.execute(flag_reason_query)
        by_flag_reason = {
            reason.value: count
            for reason, count in flag_reason_result.fetchall()
        }

        # Top moderators (last 30 days)
        moderator_query = select(
            ModerationDecision.moderator_id,
            func.count(ModerationDecision.id).label('decision_count')
        ).where(
            ModerationDecision.decided_at >= cutoff_date
        ).group_by(ModerationDecision.moderator_id).order_by(
            desc('decision_count')
        ).limit(10)

        moderator_result = await self.db.execute(moderator_query)
        top_moderators = [
            {"moderator_id": mod_id, "name": mod_id, "decisions_count": count}
            for mod_id, count in moderator_result.fetchall()
        ]

        return QueueStatsResponse(
            total_pending=pending_count,
            total_in_review=in_review_count,
            total_resolved_today=resolved_today,
            total_resolved_week=resolved_week,
            by_content_type=by_content_type,
            by_severity=by_severity,
            by_status=by_status,
            by_flag_reason=by_flag_reason,
            average_resolution_time_hours=None,  # TODO: Calculate
            median_resolution_time_hours=None,   # TODO: Calculate
            escalation_rate=0.0,  # TODO: Calculate
            appeal_rate=0.0,      # TODO: Calculate
            overturn_rate=0.0,    # TODO: Calculate
            top_moderators=top_moderators
        )
