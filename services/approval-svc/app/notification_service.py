"""
Notification service for sending approval notifications.
"""

import logging
from datetime import UTC, datetime

import httpx

from .config import settings
from .enums import NotificationChannel
from .models import Approval, ApprovalParticipant

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications to participants."""

    def __init__(self) -> None:
        self.notification_service_url = settings.notification_service_url
        self.timeout = 30.0

    async def send_approval_notification(
        self, approval: Approval, participant: ApprovalParticipant
    ) -> bool:
        """Send notification to participant about new approval request."""
        try:
            # Prepare notification content
            subject = f"Approval Required: {approval.title}"
            message = self._generate_approval_message(approval, participant)

            # Send via external notification service if available
            if self.notification_service_url:
                success = await self._send_via_external_service(
                    participant.email, subject, message, approval, participant
                )
            else:
                # Log notification (fallback)
                logger.info(f"Notification for {participant.email}: {subject}")
                success = True

            # Update participant notification timestamp
            participant.notified_at = datetime.now(UTC)

            return success

        except Exception as e:
            logger.error(f"Failed to send notification to {participant.email}: {e}")
            return False

    async def send_reminder_notification(
        self, approval: Approval, participant: ApprovalParticipant
    ) -> bool:
        """Send reminder notification to participant."""
        try:
            hours_remaining = (approval.expires_at - datetime.now(UTC)).total_seconds() / 3600

            subject = f"Reminder: Approval Required - {approval.title}"
            message = self._generate_reminder_message(approval, participant, hours_remaining)

            if self.notification_service_url:
                success = await self._send_via_external_service(
                    participant.email, subject, message, approval, participant
                )
            else:
                logger.info(f"Reminder for {participant.email}: {subject}")
                success = True

            return success

        except Exception as e:
            logger.error(f"Failed to send reminder to {participant.email}: {e}")
            return False

    async def send_completion_notification(
        self, approval: Approval, to_participants: bool = True, to_creator: bool = True
    ) -> bool:
        """Send completion notification for approved/rejected approval."""
        try:
            subject = f"Approval {approval.status.value.title()}: {approval.title}"
            message = self._generate_completion_message(approval)

            success = True

            # Notify participants
            if to_participants:
                for participant in approval.participants:
                    if self.notification_service_url:
                        participant_success = await self._send_via_external_service(
                            participant.email, subject, message, approval, participant
                        )
                        success = success and participant_success
                    else:
                        logger.info(f"Completion notification for {participant.email}: {subject}")

            # Notify creator (if different from participants)
            if to_creator:
                creator_emails = [p.email for p in approval.participants]
                if approval.created_by not in creator_emails:
                    # Would need to lookup creator email from user service
                    logger.info(
                        f"Completion notification for creator {approval.created_by}: {subject}"
                    )

            return success

        except Exception as e:
            logger.error(f"Failed to send completion notification for approval {approval.id}: {e}")
            return False

    async def _send_via_external_service(
        self,
        email: str,
        subject: str,
        message: str,
        approval: Approval,
        participant: ApprovalParticipant | None = None,
    ) -> bool:
        """Send notification via external notification service."""
        try:
            payload = {
                "recipient": email,
                "subject": subject,
                "message": message,
                "channel": NotificationChannel.EMAIL.value,
                "metadata": {
                    "approval_id": str(approval.id),
                    "tenant_id": approval.tenant_id,
                    "participant_id": str(participant.id) if participant else None,
                },
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.notification_service_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.is_success:
                    logger.info(f"Notification sent successfully to {email}")
                    return True
                else:
                    logger.warning(
                        f"Notification failed with status {response.status_code}: {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to send notification via external service: {e}")
            return False

    def _generate_approval_message(
        self, approval: Approval, participant: ApprovalParticipant
    ) -> str:
        """Generate approval request message."""
        expires_str = approval.expires_at.strftime("%B %d, %Y at %I:%M %p UTC")

        return f"""
Hello {participant.display_name},

You have been requested to provide approval for the following:

Title: {approval.title}
Type: {approval.approval_type.value.replace("_", " ").title()}
Resource: {approval.resource_type} (ID: {approval.resource_id})
Priority: {approval.priority.value.title()}

Description:
{approval.description or "No description provided."}

This approval request expires on {expires_str}.

Please review and provide your decision as soon as possible.

Thank you,
The Approval System
        """.strip()

    def _generate_reminder_message(
        self, approval: Approval, participant: ApprovalParticipant, hours_remaining: float
    ) -> str:
        """Generate reminder message."""
        if hours_remaining <= 1:
            time_str = f"{int(hours_remaining * 60)} minutes"
        else:
            time_str = f"{int(hours_remaining)} hours"

        return f"""
Hello {participant.display_name},

This is a reminder that you have a pending approval request that expires in approximately {time_str}.

Title: {approval.title}
Type: {approval.approval_type.value.replace("_", " ").title()}
Priority: {approval.priority.value.title()}

Please provide your decision before the deadline to avoid expiration.

Thank you,
The Approval System
        """.strip()

    def _generate_completion_message(self, approval: Approval) -> str:
        """Generate completion message."""
        status_text = approval.status.value.title()

        return f"""
The approval request "{approval.title}" has been {status_text.lower()}.

Type: {approval.approval_type.value.replace("_", " ").title()}
Resource: {approval.resource_type} (ID: {approval.resource_id})
Completed: {approval.completed_at.strftime("%B %d, %Y at %I:%M %p UTC") if approval.completed_at else "N/A"}

Approval Progress:
{approval.approval_progress}

Thank you,
The Approval System
        """.strip()


# Global service instance
notification_service = NotificationService()
