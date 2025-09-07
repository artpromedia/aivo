"""SMS notification service with multiple provider support."""

import logging

from twilio.rest import Client as TwilioClient

from .config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """Manages SMS notifications with fallback support."""

    def __init__(self) -> None:
        self.provider = settings.SMS_PROVIDER
        self.twilio_client = None

        if self.provider == "twilio":
            self.twilio_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
            )

    async def send(
        self,
        phone_number: str,
        message: str,
        sender_id: str | None = None,
    ) -> dict[str, any]:
        """Send SMS message."""
        if not self._validate_phone_number(phone_number):
            return {
                "status": "error",
                "error": "Invalid phone number",
            }

        # Truncate message if too long
        if len(message) > 160:
            message = message[:157] + "..."

        try:
            if self.provider == "twilio":
                return await self._send_twilio(
                    phone_number,
                    message,
                    sender_id,
                )
            elif self.provider == "aws_sns":
                return await self._send_aws_sns(
                    phone_number,
                    message,
                    sender_id,
                )
            else:
                return {
                    "status": "error",
                    "error": f"Unknown provider: {self.provider}",
                }

        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def _send_twilio(
        self,
        phone_number: str,
        message: str,
        sender_id: str | None = None,
    ) -> dict[str, any]:
        """Send SMS via Twilio."""
        try:
            message = self.twilio_client.messages.create(
                body=message,
                from_=sender_id or settings.TWILIO_PHONE_NUMBER,
                to=phone_number,
            )

            return {
                "status": "sent",
                "message_id": message.sid,
                "provider": "twilio",
            }

        except Exception as e:
            logger.error(f"Twilio SMS failed: {e}")
            raise

    async def _send_aws_sns(
        self,
        phone_number: str,
        message: str,
        sender_id: str | None = None,
    ) -> dict[str, any]:
        """Send SMS via AWS SNS."""
        # TODO: Implement AWS SNS integration
        return {
            "status": "not_implemented",
            "provider": "aws_sns",
        }

    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format."""
        # Basic validation - should be enhanced
        import re

        pattern = r"^\+?[1-9]\d{1,14}$"
        return bool(re.match(pattern, phone_number))

    async def send_batch(
        self,
        phone_numbers: list[str],
        message: str,
    ) -> dict[str, any]:
        """Send SMS to multiple recipients."""
        results = {
            "total": len(phone_numbers),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        for phone in phone_numbers:
            result = await self.send(phone, message)
            if result["status"] == "sent":
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(
                    {
                        "phone": phone,
                        "error": result.get("error"),
                    }
                )

        return results
