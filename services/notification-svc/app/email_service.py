"""
Email service for sending notifications in development and production.
"""

import json
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import aiofiles

from .config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(self) -> None:
        """Initialize email service."""
        self.settings = get_settings()
        self.dev_mode = self.settings.dev_mode
        self.dev_email_path = Path(self.settings.dev_email_dump_path)

        if self.dev_mode:
            # Ensure dev email directory exists
            self.dev_email_path.mkdir(exist_ok=True)
            logger.info(
                "Email service in development mode - emails saved to %s",
                self.dev_email_path
            )
        else:
            logger.info(
                "Email service in production mode - "
                "emails will be sent via SMTP"
            )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str | None = None,
        from_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send an email."""

        from_email = from_email or self.settings.from_email
        from_name = from_name or self.settings.from_name

        email_data = {
            "to": to_email,
            "from_email": from_email,
            "from_name": from_name,
            "subject": subject,
            "html_content": html_content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
            "sent_via": "dev_mode" if self.dev_mode else "smtp",
        }

        if self.dev_mode:
            return await self._save_dev_email(email_data)
        else:
            return await self._send_smtp_email(email_data)

    async def send_bulk_emails(
        self,
        to_emails: list[str],
        subject: str,
        html_content: str,
        from_email: str | None = None,
        from_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send bulk emails."""

        results = {"total_sent": 0, "successful": [], "failed": []}

        for email in to_emails:
            try:
                result = await self.send_email(
                    to_email=email,
                    subject=subject,
                    html_content=html_content,
                    from_email=from_email,
                    from_name=from_name,
                    metadata=metadata,
                )

                if result.get("success"):
                    results["successful"].append(email)
                    results["total_sent"] += 1
                else:
                    results["failed"].append({
                        "email": email,
                        "error": result.get("error", "Unknown error")
                    })

            except (smtplib.SMTPException, OSError, ValueError) as e:
                logger.error("Failed to send email to %s: %s", email, e)
                results["failed"].append({"email": email, "error": str(e)})

        return results

    async def _save_dev_email(
        self, email_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Save email to file system for development."""
        try:
            # Generate filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            safe_email = (
                email_data['to'].replace('@', '_at_').replace('.', '_')
            )
            filename = f"email_{timestamp}_{safe_email}.json"
            filepath = self.dev_email_path / filename

            # Save email data as JSON
            async with aiofiles.open(filepath, "w") as f:
                await f.write(json.dumps(email_data, indent=2))

            logger.info("Development email saved: %s", filepath)

            return {
                "success": True,
                "message_id": f"dev_{timestamp}",
                "filepath": str(filepath)
            }

        except (OSError, ValueError, json.JSONDecodeError) as e:
            logger.error("Failed to save development email: %s", e)
            return {
                "success": False,
                "error": "Failed to save development email: " + str(e)
            }

    async def _send_smtp_email(
        self, email_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Send email via SMTP."""
        try:
            if not self.settings.smtp_server:
                raise ValueError("SMTP server not configured")

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = email_data["subject"]
            msg["From"] = (
                f"{email_data['from_name']} <{email_data['from_email']}>"
            )
            msg["To"] = email_data["to"]

            # Attach HTML content
            html_part = MIMEText(email_data["html_content"], "html")
            msg.attach(html_part)

            # Send email
            smtp_server = self.settings.smtp_server
            smtp_port = self.settings.smtp_port
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if self.settings.smtp_use_tls:
                    server.starttls()

                smtp_user = self.settings.smtp_username
                smtp_pass = self.settings.smtp_password
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)

                server.send_message(msg)

            logger.info("Email sent successfully to %s", email_data['to'])

            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
            return {
                "success": True,
                "message_id": f"smtp_{timestamp}",
            }

        except (smtplib.SMTPException, OSError, ValueError) as e:
            logger.error("Failed to send SMTP email: %s", e)
            return {
                "success": False,
                "error": "Failed to send email: " + str(e)
            }

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        if self.dev_mode:
            return True

        return bool(self.settings.smtp_server and self.settings.from_email)

    async def get_dev_emails(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent development emails (for testing/debugging)."""
        if not self.dev_mode:
            return []

        emails = []
        try:
            email_files = sorted(
                self.dev_email_path.glob("email_*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )[:limit]

            for filepath in email_files:
                async with aiofiles.open(filepath) as f:
                    content = await f.read()
                    email_data = json.loads(content)
                    emails.append(email_data)

        except (OSError, json.JSONDecodeError) as e:
            logger.error("Failed to load development emails: %s", e)

        return emails


# Global email service instance
email_service = EmailService()
