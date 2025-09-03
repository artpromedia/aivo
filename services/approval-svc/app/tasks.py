"""
Background tasks for approval service.
"""
import logging
from datetime import datetime, timezone, timedelta
from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import AsyncSessionLocal
from .approval_service import approval_service
from .notification_service import notification_service

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "approval_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "expire-approvals": {
            "task": "app.tasks.expire_approvals_task",
            "schedule": 300.0,  # Every 5 minutes
        },
        "send-reminders": {
            "task": "app.tasks.send_reminder_notifications_task",
            "schedule": 3600.0,  # Every hour
        },
    },
)


@celery_app.task(bind=True)
def expire_approvals_task(self):
    """Task to expire overdue approvals."""
    try:
        import asyncio
        
        async def _expire_approvals():
            async with AsyncSessionLocal() as db:
                count = await approval_service.expire_approvals(db)
                return count
        
        # Run the async function
        count = asyncio.run(_expire_approvals())
        logger.info(f"Expired {count} approvals")
        return {"expired_count": count}
        
    except Exception as e:
        logger.error(f"Failed to expire approvals: {e}")
        self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True)
def send_reminder_notifications_task(self):
    """Task to send reminder notifications."""
    try:
        import asyncio
        
        async def _send_reminders():
            from sqlalchemy import select, and_
            from .models import Approval, ApprovalParticipant
            from .enums import ApprovalStatus
            
            async with AsyncSessionLocal() as db:
                now = datetime.now(timezone.utc)
                sent_count = 0
                
                # Find approvals that need reminders
                for hours_before in settings.reminder_hours_before_expiry:
                    reminder_time = now + timedelta(hours=hours_before)
                    
                    # Get pending approvals expiring around this time
                    stmt = select(Approval).where(
                        and_(
                            Approval.status == ApprovalStatus.PENDING,
                            Approval.expires_at <= reminder_time,
                            Approval.expires_at > now
                        )
                    )
                    
                    result = await db.execute(stmt)
                    approvals = result.scalars().all()
                    
                    for approval in approvals:
                        # Send reminders to participants who haven't responded
                        for participant in approval.participants:
                            if not participant.has_responded:
                                success = await notification_service.send_reminder_notification(
                                    approval, participant
                                )
                                if success:
                                    sent_count += 1
                
                await db.commit()
                return sent_count
        
        # Run the async function
        count = asyncio.run(_send_reminders())
        logger.info(f"Sent {count} reminder notifications")
        return {"reminders_sent": count}
        
    except Exception as e:
        logger.error(f"Failed to send reminder notifications: {e}")
        self.retry(countdown=300, max_retries=3)


@celery_app.task(bind=True)
def send_approval_notification_task(self, approval_id: str, participant_id: str):
    """Task to send approval notification to a participant."""
    try:
        import asyncio
        from uuid import UUID
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from .models import Approval, ApprovalParticipant
        
        async def _send_notification():
            async with AsyncSessionLocal() as db:
                # Load approval and participant
                stmt = select(Approval).where(
                    Approval.id == UUID(approval_id)
                ).options(selectinload(Approval.participants))
                
                result = await db.execute(stmt)
                approval = result.scalar_one_or_none()
                
                if not approval:
                    logger.error(f"Approval {approval_id} not found")
                    return False
                
                participant = None
                for p in approval.participants:
                    if str(p.id) == participant_id:
                        participant = p
                        break
                
                if not participant:
                    logger.error(f"Participant {participant_id} not found")
                    return False
                
                # Send notification
                success = await notification_service.send_approval_notification(
                    approval, participant
                )
                
                if success:
                    await db.commit()
                
                return success
        
        # Run the async function
        success = asyncio.run(_send_notification())
        
        if success:
            logger.info(f"Sent approval notification for {approval_id} to participant {participant_id}")
        else:
            logger.error(f"Failed to send approval notification for {approval_id} to participant {participant_id}")
        
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Failed to send approval notification: {e}")
        self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True)
def send_completion_notification_task(self, approval_id: str):
    """Task to send completion notification."""
    try:
        import asyncio
        from uuid import UUID
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from .models import Approval
        
        async def _send_completion_notification():
            async with AsyncSessionLocal() as db:
                # Load approval
                stmt = select(Approval).where(
                    Approval.id == UUID(approval_id)
                ).options(selectinload(Approval.participants))
                
                result = await db.execute(stmt)
                approval = result.scalar_one_or_none()
                
                if not approval:
                    logger.error(f"Approval {approval_id} not found")
                    return False
                
                # Send completion notification
                success = await notification_service.send_completion_notification(approval)
                return success
        
        # Run the async function
        success = asyncio.run(_send_completion_notification())
        
        if success:
            logger.info(f"Sent completion notification for approval {approval_id}")
        else:
            logger.error(f"Failed to send completion notification for approval {approval_id}")
        
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Failed to send completion notification: {e}")
        self.retry(countdown=60, max_retries=3)


# Utility functions for triggering tasks
def schedule_approval_notifications(approval_id: str, participant_ids: list[str]):
    """Schedule notification tasks for approval participants."""
    for participant_id in participant_ids:
        send_approval_notification_task.delay(approval_id, participant_id)


def schedule_completion_notification(approval_id: str):
    """Schedule completion notification task."""
    send_completion_notification_task.delay(approval_id)
