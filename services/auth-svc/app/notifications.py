"""
Notification service client for auth-svc.
Handles email notifications through notification-svc (stubbed for now).
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EmailType(str, Enum):
    """Types of emails sent by the auth service."""

    INVITE = "invite"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    WELCOME = "welcome"


class EmailRequest(BaseModel):
    """Email request model for notification service."""

    to_email: str
    email_type: EmailType
    template_data: Dict[str, Any]
    subject: str
    priority: str = "normal"  # normal, high, urgent


class NotificationClient:
    """
    Client for sending notifications via notification-svc.
    Currently stubbed - in production would communicate with actual notification service.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or "http://notification-svc:8080"
        self.client = httpx.AsyncClient()

    async def send_email(self, email_request: EmailRequest) -> bool:
        """
        Send an email via notification service.
        Currently stubbed - logs the email request instead of sending.

        Args:
            email_request: Email details to send

        Returns:
            bool: True if email was queued successfully
        """
        try:
            # TODO: Replace with actual HTTP call to notification-svc
            # response = await self.client.post(
            #     f"{self.base_url}/v1/emails",
            #     json=email_request.model_dump()
            # )
            # return response.status_code == 202

            # For now, just log the email request
            logger.info(
                f"📧 EMAIL STUB: {email_request.email_type.value} email to {email_request.to_email} "
                f"with subject '{email_request.subject}'"
            )
            logger.debug(f"Template data: {email_request.template_data}")

            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def send_invite_email(
        self,
        email: str,
        invite_token: str,
        role: str,
        invited_by: str,
        organization_name: str = "SchoolApp",
    ) -> bool:
        """Send an invitation email to a new user."""
        email_request = EmailRequest(
            to_email=email,
            email_type=EmailType.INVITE,
            subject=f"You're invited to join {organization_name} as a {role}",
            template_data={
                "invite_token": invite_token,
                "role": role,
                "invited_by": invited_by,
                "organization_name": organization_name,
                "signup_url": f"https://app.example.com/signup?token={invite_token}",
                "expires_in_hours": 24,
            },
            priority="normal",
        )

        return await self.send_email(email_request)

    async def send_password_reset_email(self, email: str, reset_token: str, user_name: str) -> bool:
        """Send a password reset email."""
        email_request = EmailRequest(
            to_email=email,
            email_type=EmailType.PASSWORD_RESET,
            subject="Reset your password",
            template_data={
                "reset_token": reset_token,
                "user_name": user_name,
                "reset_url": f"https://app.example.com/reset-password?token={reset_token}",
                "expires_in_hours": 1,
            },
            priority="high",
        )

        return await self.send_email(email_request)

    async def send_email_verification(
        self, email: str, verification_token: str, user_name: str
    ) -> bool:
        """Send an email verification email."""
        email_request = EmailRequest(
            to_email=email,
            email_type=EmailType.EMAIL_VERIFICATION,
            subject="Verify your email address",
            template_data={
                "verification_token": verification_token,
                "user_name": user_name,
                "verification_url": f"https://app.example.com/verify-email?token={verification_token}",
                "expires_in_hours": 24,
            },
            priority="normal",
        )

        return await self.send_email(email_request)

    async def send_welcome_email(self, email: str, user_name: str, role: str) -> bool:
        """Send a welcome email to a new user."""
        email_request = EmailRequest(
            to_email=email,
            email_type=EmailType.WELCOME,
            subject="Welcome to SchoolApp!",
            template_data={
                "user_name": user_name,
                "role": role,
                "login_url": "https://app.example.com/login",
                "support_email": "support@example.com",
            },
            priority="normal",
        )

        return await self.send_email(email_request)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global notification client instance
_notification_client: Optional[NotificationClient] = None


def get_notification_client() -> NotificationClient:
    """Get the global notification client instance."""
    global _notification_client
    if _notification_client is None:
        _notification_client = NotificationClient()
    return _notification_client


async def close_notification_client():
    """Close the global notification client."""
    global _notification_client
    if _notification_client is not None:
        await _notification_client.close()
        _notification_client = None
