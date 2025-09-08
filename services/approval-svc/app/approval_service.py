"""
Core approval service with business logic.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .config import settings
from .enums import ApprovalStatus, WebhookEventType
from .models import Approval, ApprovalDecision, ApprovalParticipant
from .notification_service import notification_service
from .schemas import (
    ApprovalCreateInput,
    ApprovalListQuery,
    ApprovalResponse,
    ApprovalSummary,
    DecisionInput,
    DecisionResult,
)
from .webhook_service import webhook_service

logger = logging.getLogger(__name__)


class ApprovalService:
    """Core approval service."""

    async def create_approval(
        self, db: AsyncSession, approval_data: ApprovalCreateInput
    ) -> ApprovalResponse:
        """Create a new approval request."""
        try:
            # Calculate expiry time
            ttl_hours = approval_data.ttl_hours or settings.default_ttl_hours
            expires_at = datetime.now(UTC) + timedelta(hours=ttl_hours)

            # Determine required participants count
            required_participants = approval_data.required_participants
            if required_participants is None:
                if approval_data.require_all_participants:
                    required_participants = len(approval_data.participants)
                else:
                    required_participants = 2  # Default: guardian + one staff

            # Create approval
            approval = Approval(
                tenant_id=approval_data.tenant_id,
                approval_type=approval_data.approval_type,
                status=ApprovalStatus.PENDING,
                priority=approval_data.priority,
                resource_type=approval_data.resource_type,
                resource_id=approval_data.resource_id,
                resource_data=approval_data.resource_data,
                title=approval_data.title,
                description=approval_data.description,
                created_by=approval_data.created_by,
                expires_at=expires_at,
                required_participants=required_participants,
                require_all_participants=approval_data.require_all_participants,
                webhook_url=approval_data.webhook_url,
                webhook_events=approval_data.webhook_events,
                callback_data=approval_data.callback_data,
            )

            # Add participants
            for participant_data in approval_data.participants:
                participant = ApprovalParticipant(
                    user_id=participant_data.user_id,
                    email=participant_data.email,
                    role=participant_data.role,
                    display_name=participant_data.display_name,
                    is_required=participant_data.is_required,
                    participant_metadata=participant_data.metadata,
                )
                approval.participants.append(participant)

            db.add(approval)
            await db.commit()
            await db.refresh(approval)

            # Load relationships for response
            approval = await self._load_approval_with_relations(db, approval.id)

            # Send notifications
            await self._send_approval_notifications(approval)

            # Send webhook
            if approval.webhook_url:
                await webhook_service.send_webhook(approval, WebhookEventType.APPROVAL_REQUESTED)

            logger.info(f"Created approval {approval.id} for tenant {approval.tenant_id}")

            return self._approval_to_response(approval)

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create approval: {e}")
            raise

    async def get_approval(
        self, db: AsyncSession, approval_id: UUID, tenant_id: str | None = None
    ) -> ApprovalResponse | None:
        """Get approval by ID."""
        approval = await self._load_approval_with_relations(db, approval_id, tenant_id)
        if not approval:
            return None

        return self._approval_to_response(approval)

    async def list_approvals(self, db: AsyncSession, query: ApprovalListQuery) -> dict[str, Any]:
        """List approvals with filtering."""
        # Build base query
        stmt = select(Approval)

        # Apply filters
        conditions = []

        if query.tenant_id:
            conditions.append(Approval.tenant_id == query.tenant_id)

        if query.status:
            conditions.append(Approval.status == query.status)

        if query.approval_type:
            conditions.append(Approval.approval_type == query.approval_type)

        if query.priority:
            conditions.append(Approval.priority == query.priority)

        if query.resource_type:
            conditions.append(Approval.resource_type == query.resource_type)

        if query.created_by:
            conditions.append(Approval.created_by == query.created_by)

        if query.expires_before:
            conditions.append(Approval.expires_at <= query.expires_before)

        if query.expires_after:
            conditions.append(Approval.expires_at >= query.expires_after)

        if query.created_before:
            conditions.append(Approval.created_at <= query.created_before)

        if query.created_after:
            conditions.append(Approval.created_at >= query.created_after)

        if query.participant_user_id:
            # Join with participants to filter by user
            stmt = stmt.join(ApprovalParticipant)
            conditions.append(ApprovalParticipant.user_id == query.participant_user_id)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Apply ordering
        if query.order_by == "created_at":
            order_column = Approval.created_at
        elif query.order_by == "expires_at":
            order_column = Approval.expires_at
        elif query.order_by == "priority":
            order_column = Approval.priority
        else:
            order_column = Approval.created_at

        if query.order_desc:
            order_column = order_column.desc()

        stmt = stmt.order_by(order_column)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.alias())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()

        # Apply pagination
        stmt = stmt.offset(query.offset).limit(query.limit)

        # Load with relationships
        stmt = stmt.options(selectinload(Approval.participants), selectinload(Approval.decisions))

        result = await db.execute(stmt)
        approvals = result.scalars().all()

        # Convert to response format
        items = [self._approval_to_summary(approval) for approval in approvals]

        return {
            "items": items,
            "total": total,
            "limit": query.limit,
            "offset": query.offset,
            "has_more": query.offset + len(items) < total,
        }

    async def make_decision(
        self,
        db: AsyncSession,
        approval_id: UUID,
        user_id: str,
        decision_data: DecisionInput,
        tenant_id: str | None = None,
        request_metadata: dict[str, Any] | None = None,
    ) -> DecisionResult:
        """Make a decision on an approval."""
        try:
            # Load approval with relationships
            approval = await self._load_approval_with_relations(db, approval_id, tenant_id)
            if not approval:
                return DecisionResult(
                    success=False,
                    message="Approval not found",
                    approval_status=ApprovalStatus.PENDING,
                    decision_id=UUID("00000000-0000-0000-0000-000000000000"),
                    approval_completed=False,
                    errors=["Approval not found"],
                )

            # Check if approval is still pending
            if approval.status != ApprovalStatus.PENDING:
                return DecisionResult(
                    success=False,
                    message=f"Approval is already {approval.status.value}",
                    approval_status=approval.status,
                    decision_id=UUID("00000000-0000-0000-0000-000000000000"),
                    approval_completed=True,
                    errors=[f"Approval is already {approval.status.value}"],
                )

            # Check if approval has expired
            if approval.is_expired:
                approval.status = ApprovalStatus.EXPIRED
                await db.commit()
                return DecisionResult(
                    success=False,
                    message="Approval has expired",
                    approval_status=ApprovalStatus.EXPIRED,
                    decision_id=UUID("00000000-0000-0000-0000-000000000000"),
                    approval_completed=True,
                    errors=["Approval has expired"],
                )

            # Find participant
            participant = None
            for p in approval.participants:
                if p.user_id == user_id:
                    participant = p
                    break

            if not participant:
                return DecisionResult(
                    success=False,
                    message="User is not a participant in this approval",
                    approval_status=approval.status,
                    decision_id=UUID("00000000-0000-0000-0000-000000000000"),
                    approval_completed=False,
                    errors=["User is not a participant in this approval"],
                )

            # Check if participant already made a decision
            if participant.has_responded:
                return DecisionResult(
                    success=False,
                    message="Participant has already made a decision",
                    approval_status=approval.status,
                    decision_id=UUID("00000000-0000-0000-0000-000000000000"),
                    approval_completed=False,
                    errors=["Participant has already made a decision"],
                )

            # Create decision
            decision = ApprovalDecision(
                approval_id=approval.id,
                participant_id=participant.id,
                decision_type=decision_data.decision_type,
                comments=decision_data.comments,
                ip_address=request_metadata.get("ip_address") if request_metadata else None,
                user_agent=request_metadata.get("user_agent") if request_metadata else None,
                decision_metadata=decision_data.metadata,
            )

            # Update participant
            participant.has_responded = True

            db.add(decision)
            await db.commit()
            await db.refresh(decision)

            # Check if approval is complete
            approval_completed = await self._check_approval_completion(db, approval)

            # Send webhook
            if approval.webhook_url:
                await webhook_service.send_webhook(
                    approval,
                    WebhookEventType.DECISION_MADE,
                    additional_data={
                        "decision_id": str(decision.id),
                        "participant_id": str(participant.id),
                        "decision_type": decision.decision_type.value,
                        "user_id": user_id,
                    },
                )

            logger.info(
                f"Decision {decision.decision_type.value} made by {user_id} for approval {approval.id}"
            )

            return DecisionResult(
                success=True,
                message="Decision recorded successfully",
                approval_status=approval.status,
                decision_id=decision.id,
                approval_completed=approval_completed,
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to make decision: {e}")
            raise

    async def expire_approvals(self, db: AsyncSession) -> int:
        """Expire overdue approvals. Returns count of expired approvals."""
        now = datetime.now(UTC)

        # Find pending approvals that have expired
        stmt = (
            select(Approval)
            .where(and_(Approval.status == ApprovalStatus.PENDING, Approval.expires_at <= now))
            .options(selectinload(Approval.participants))
        )

        result = await db.execute(stmt)
        expired_approvals = result.scalars().all()

        count = 0
        for approval in expired_approvals:
            approval.status = ApprovalStatus.EXPIRED
            approval.completed_at = now

            # Send webhook
            if approval.webhook_url:
                await webhook_service.send_webhook(approval, WebhookEventType.APPROVAL_EXPIRED)

            count += 1

        if count > 0:
            await db.commit()
            logger.info(f"Expired {count} overdue approvals")

        return count

    async def _load_approval_with_relations(
        self, db: AsyncSession, approval_id: UUID, tenant_id: str | None = None
    ) -> Approval | None:
        """Load approval with all relationships."""
        stmt = select(Approval).where(Approval.id == approval_id)

        if tenant_id:
            stmt = stmt.where(Approval.tenant_id == tenant_id)

        stmt = stmt.options(
            selectinload(Approval.participants).selectinload(ApprovalParticipant.decisions),
            selectinload(Approval.decisions),
            selectinload(Approval.notifications),
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_approval_completion(self, db: AsyncSession, approval: Approval) -> bool:
        """Check if approval is complete and update status."""
        approved_count = sum(1 for p in approval.participants if p.has_approved)
        rejected_count = sum(1 for p in approval.participants if p.has_rejected)

        approval_completed = False

        if rejected_count > 0:
            # Any rejection completes the approval as rejected
            approval.status = ApprovalStatus.REJECTED
            approval.completed_at = datetime.now(UTC)
            approval_completed = True

            # Send webhook
            if approval.webhook_url:
                await webhook_service.send_webhook(approval, WebhookEventType.APPROVAL_REJECTED)

        elif approved_count >= approval.required_participants:
            # Sufficient approvals
            approval.status = ApprovalStatus.APPROVED
            approval.completed_at = datetime.now(UTC)
            approval_completed = True

            # Send webhook
            if approval.webhook_url:
                await webhook_service.send_webhook(approval, WebhookEventType.APPROVAL_COMPLETED)

        if approval_completed:
            await db.commit()
            logger.info(f"Approval {approval.id} completed with status {approval.status.value}")

        return approval_completed

    async def _send_approval_notifications(self, approval: Approval) -> None:
        """Send notifications to all participants."""
        for participant in approval.participants:
            await notification_service.send_approval_notification(approval, participant)

    def _approval_to_response(self, approval: Approval) -> ApprovalResponse:
        """Convert approval model to response schema."""
        return ApprovalResponse(
            id=approval.id,
            tenant_id=approval.tenant_id,
            approval_type=approval.approval_type,
            status=approval.status,
            priority=approval.priority,
            resource_type=approval.resource_type,
            resource_id=approval.resource_id,
            resource_data=approval.resource_data,
            title=approval.title,
            description=approval.description,
            created_by=approval.created_by,
            created_at=approval.created_at,
            expires_at=approval.expires_at,
            completed_at=approval.completed_at,
            required_participants=approval.required_participants,
            require_all_participants=approval.require_all_participants,
            webhook_url=approval.webhook_url,
            webhook_events=approval.webhook_events,
            callback_data=approval.callback_data,
            approval_progress=approval.approval_progress,
            is_expired=approval.is_expired,
            participants=[
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "email": p.email,
                    "role": p.role,
                    "display_name": p.display_name,
                    "is_required": p.is_required,
                    "has_responded": p.has_responded,
                    "has_approved": p.has_approved,
                    "has_rejected": p.has_rejected,
                    "notified_at": p.notified_at,
                    "metadata": p.participant_metadata,
                }
                for p in approval.participants
            ],
            decisions=[
                {
                    "id": d.id,
                    "participant_id": d.participant_id,
                    "decision_type": d.decision_type,
                    "comments": d.comments,
                    "created_at": d.created_at,
                    "metadata": d.decision_metadata,
                }
                for d in approval.decisions
            ],
        )

    def _approval_to_summary(self, approval: Approval) -> ApprovalSummary:
        """Convert approval model to summary schema."""
        return ApprovalSummary(
            id=approval.id,
            tenant_id=approval.tenant_id,
            approval_type=approval.approval_type,
            status=approval.status,
            priority=approval.priority,
            resource_type=approval.resource_type,
            resource_id=approval.resource_id,
            title=approval.title,
            created_by=approval.created_by,
            created_at=approval.created_at,
            expires_at=approval.expires_at,
            completed_at=approval.completed_at,
            approval_progress=approval.approval_progress,
            is_expired=approval.is_expired,
        )


# Global service instance
approval_service = ApprovalService()
