"""
Notification and Subscription Service
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiosmtplib
import structlog
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client as TwilioClient

from app.config import settings
from app.models import (
    Incident, IncidentSeverity, NotificationChannel, NotificationLog,
    NotificationSubscription
)

logger = structlog.get_logger(__name__)


class NotificationService:
    """Service for managing notifications and subscriptions."""

    def __init__(self):
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )

    async def create_subscription(
        self,
        db: AsyncSession,
        tenant_id: str,
        name: str,
        channels: List[Dict[str, Any]],
        min_severity: IncidentSeverity = IncidentSeverity.MEDIUM,
        service_filters: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        immediate_notification: bool = True,
        digest_frequency: Optional[str] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        created_by: str = "system"
    ) -> NotificationSubscription:
        """Create a new notification subscription."""

        # Validate channels
        validated_channels = []
        for channel in channels:
            if self._validate_channel(channel):
                validated_channels.append(channel)

        if not validated_channels:
            raise ValueError("At least one valid channel must be provided")

        # Check subscription limits
        existing_count = await self._count_tenant_subscriptions(db, tenant_id)
        if existing_count >= settings.MAX_SUBSCRIPTIONS_PER_TENANT:
            raise ValueError(
                f"Maximum {settings.MAX_SUBSCRIPTIONS_PER_TENANT} subscriptions per tenant"
            )

        subscription = NotificationSubscription(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            min_severity=min_severity,
            service_filters=service_filters,
            channels=validated_channels,
            immediate_notification=immediate_notification,
            digest_frequency=digest_frequency,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
            created_by=created_by
        )

        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

        logger.info(
            "Notification subscription created",
            subscription_id=str(subscription.id),
            tenant_id=tenant_id,
            channels=len(validated_channels)
        )

        return subscription

    async def get_subscription(
        self,
        db: AsyncSession,
        subscription_id: uuid.UUID
    ) -> Optional[NotificationSubscription]:
        """Get subscription by ID."""

        result = await db.execute(
            select(NotificationSubscription).where(
                NotificationSubscription.id == subscription_id
            )
        )
        return result.scalar_one_or_none()

    async def list_subscriptions(
        self,
        db: AsyncSession,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """List subscriptions with filtering."""

        query = select(NotificationSubscription)
        filters = []

        if tenant_id:
            filters.append(NotificationSubscription.tenant_id == tenant_id)

        if user_id:
            filters.append(NotificationSubscription.user_id == user_id)

        if active_only:
            filters.append(NotificationSubscription.is_active == True)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(desc(NotificationSubscription.created_at))

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        subscriptions = result.scalars().all()

        # Get total count
        count_query = select(NotificationSubscription.id)
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await db.execute(count_query)
        total_count = len(count_result.scalars().all())

        return {
            "subscriptions": subscriptions,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_count,
                "pages": (total_count + page_size - 1) // page_size
            }
        }

    async def update_subscription(
        self,
        db: AsyncSession,
        subscription_id: uuid.UUID,
        name: Optional[str] = None,
        channels: Optional[List[Dict[str, Any]]] = None,
        min_severity: Optional[IncidentSeverity] = None,
        service_filters: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
        immediate_notification: Optional[bool] = None,
        digest_frequency: Optional[str] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None
    ) -> Optional[NotificationSubscription]:
        """Update a subscription."""

        subscription = await self.get_subscription(db, subscription_id)
        if not subscription:
            return None

        # Update fields if provided
        if name is not None:
            subscription.name = name
        if channels is not None:
            validated_channels = [
                channel for channel in channels
                if self._validate_channel(channel)
            ]
            if not validated_channels:
                raise ValueError("At least one valid channel must be provided")
            subscription.channels = validated_channels
        if min_severity is not None:
            subscription.min_severity = min_severity
        if service_filters is not None:
            subscription.service_filters = service_filters
        if is_active is not None:
            subscription.is_active = is_active
        if immediate_notification is not None:
            subscription.immediate_notification = immediate_notification
        if digest_frequency is not None:
            subscription.digest_frequency = digest_frequency
        if quiet_hours_start is not None:
            subscription.quiet_hours_start = quiet_hours_start
        if quiet_hours_end is not None:
            subscription.quiet_hours_end = quiet_hours_end

        await db.commit()
        await db.refresh(subscription)

        logger.info("Subscription updated", subscription_id=str(subscription_id))

        return subscription

    async def delete_subscription(
        self,
        db: AsyncSession,
        subscription_id: uuid.UUID
    ) -> bool:
        """Delete a subscription."""

        subscription = await self.get_subscription(db, subscription_id)
        if not subscription:
            return False

        await db.delete(subscription)
        await db.commit()

        logger.info("Subscription deleted", subscription_id=str(subscription_id))

        return True

    async def notify_incident_created(
        self,
        db: AsyncSession,
        incident: Incident
    ) -> int:
        """Send notifications for a new incident."""

        # Get matching subscriptions
        subscriptions = await self._get_matching_subscriptions(db, incident)

        notifications_sent = 0

        for subscription in subscriptions:
            if not subscription.immediate_notification:
                continue  # Skip non-immediate subscriptions

            if self._is_in_quiet_hours(subscription):
                continue  # Skip if in quiet hours

            # Send to all channels in the subscription
            for channel_config in subscription.channels:
                try:
                    success = await self._send_incident_notification(
                        db=db,
                        incident=incident,
                        subscription=subscription,
                        channel_config=channel_config,
                        notification_type="incident_created"
                    )

                    if success:
                        notifications_sent += 1

                except Exception as e:
                    logger.error(
                        "Failed to send incident notification",
                        incident_id=str(incident.id),
                        subscription_id=str(subscription.id),
                        error=str(e)
                    )

        # Update incident notification tracking
        if notifications_sent > 0:
            incident.notifications_sent = True
            incident.last_notification_at = datetime.utcnow()
            await db.commit()

        logger.info(
            "Incident notifications sent",
            incident_id=str(incident.id),
            count=notifications_sent
        )

        return notifications_sent

    async def notify_incident_updated(
        self,
        db: AsyncSession,
        incident: Incident,
        update_message: str
    ) -> int:
        """Send notifications for an incident update."""

        subscriptions = await self._get_matching_subscriptions(db, incident)

        notifications_sent = 0

        for subscription in subscriptions:
            if not subscription.immediate_notification:
                continue

            if self._is_in_quiet_hours(subscription):
                continue

            for channel_config in subscription.channels:
                try:
                    success = await self._send_incident_notification(
                        db=db,
                        incident=incident,
                        subscription=subscription,
                        channel_config=channel_config,
                        notification_type="incident_updated",
                        update_message=update_message
                    )

                    if success:
                        notifications_sent += 1

                except Exception as e:
                    logger.error(
                        "Failed to send incident update notification",
                        incident_id=str(incident.id),
                        subscription_id=str(subscription.id),
                        error=str(e)
                    )

        if notifications_sent > 0:
            incident.last_notification_at = datetime.utcnow()
            await db.commit()

        return notifications_sent

    async def _get_matching_subscriptions(
        self,
        db: AsyncSession,
        incident: Incident
    ) -> List[NotificationSubscription]:
        """Get subscriptions that match an incident."""

        # Get all active subscriptions with severity >= incident severity
        severity_order = {
            IncidentSeverity.LOW: 1,
            IncidentSeverity.MEDIUM: 2,
            IncidentSeverity.HIGH: 3,
            IncidentSeverity.CRITICAL: 4
        }

        incident_severity_level = severity_order[incident.severity]

        result = await db.execute(
            select(NotificationSubscription).where(
                NotificationSubscription.is_active == True
            )
        )

        all_subscriptions = result.scalars().all()
        matching_subscriptions = []

        for subscription in all_subscriptions:
            subscription_severity_level = severity_order[subscription.min_severity]

            # Check severity threshold
            if incident_severity_level < subscription_severity_level:
                continue

            # Check service filters
            if subscription.service_filters and incident.affected_services:
                if not any(
                    service in subscription.service_filters
                    for service in incident.affected_services
                ):
                    continue

            matching_subscriptions.append(subscription)

        return matching_subscriptions

    async def _send_incident_notification(
        self,
        db: AsyncSession,
        incident: Incident,
        subscription: NotificationSubscription,
        channel_config: Dict[str, Any],
        notification_type: str,
        update_message: Optional[str] = None
    ) -> bool:
        """Send a notification through a specific channel."""

        channel_type = NotificationChannel(channel_config.get("type"))
        recipient = channel_config.get("address", "")

        # Generate notification content
        subject, message = self._generate_notification_content(
            incident, notification_type, update_message
        )

        # Create notification log entry
        log_entry = NotificationLog(
            incident_id=incident.id,
            subscription_id=subscription.id,
            channel=channel_type,
            recipient=recipient,
            subject=subject,
            message=message,
            status="pending"
        )

        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)

        # Send notification based on channel type
        success = False
        error_message = None

        try:
            if channel_type == NotificationChannel.EMAIL:
                success = await self._send_email(recipient, subject, message)
            elif channel_type == NotificationChannel.SMS:
                success = await self._send_sms(recipient, message)
            elif channel_type == NotificationChannel.WEBHOOK:
                success = await self._send_webhook(
                    channel_config.get("url", ""),
                    incident,
                    notification_type,
                    update_message
                )

            # Update log entry
            log_entry.status = "sent" if success else "failed"
            log_entry.sent_at = datetime.utcnow()

            if success:
                # Update subscription last notified
                subscription.last_notified_at = datetime.utcnow()

        except Exception as e:
            error_message = str(e)
            log_entry.status = "failed"
            log_entry.error_message = error_message
            success = False

        await db.commit()

        return success

    async def _send_email(self, recipient: str, subject: str, message: str) -> bool:
        """Send email notification."""

        if not settings.SMTP_HOST:
            logger.warning("SMTP not configured, skipping email notification")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = settings.FROM_EMAIL
            msg['To'] = recipient
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=settings.SMTP_USE_TLS,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD
            )

            logger.info("Email sent", recipient=recipient, subject=subject)
            return True

        except Exception as e:
            logger.error("Failed to send email", recipient=recipient, error=str(e))
            return False

    async def _send_sms(self, recipient: str, message: str) -> bool:
        """Send SMS notification."""

        if not self.twilio_client or not settings.TWILIO_FROM_PHONE:
            logger.warning("Twilio not configured, skipping SMS notification")
            return False

        try:
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_FROM_PHONE,
                to=recipient
            )

            logger.info("SMS sent", recipient=recipient, sid=message_obj.sid)
            return True

        except Exception as e:
            logger.error("Failed to send SMS", recipient=recipient, error=str(e))
            return False

    async def _send_webhook(
        self,
        webhook_url: str,
        incident: Incident,
        notification_type: str,
        update_message: Optional[str] = None
    ) -> bool:
        """Send webhook notification."""

        try:
            import httpx

            payload = {
                "type": notification_type,
                "incident": {
                    "id": str(incident.id),
                    "title": incident.title,
                    "description": incident.description,
                    "status": incident.status.value,
                    "severity": incident.severity.value,
                    "started_at": incident.started_at.isoformat(),
                    "affected_services": incident.affected_services
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            if update_message:
                payload["update_message"] = update_message

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()

            logger.info("Webhook sent", url=webhook_url, incident_id=str(incident.id))
            return True

        except Exception as e:
            logger.error("Failed to send webhook", url=webhook_url, error=str(e))
            return False

    def _generate_notification_content(
        self,
        incident: Incident,
        notification_type: str,
        update_message: Optional[str] = None
    ) -> tuple[str, str]:
        """Generate notification subject and message."""

        severity_emoji = {
            IncidentSeverity.LOW: "🔵",
            IncidentSeverity.MEDIUM: "🟡",
            IncidentSeverity.HIGH: "🟠",
            IncidentSeverity.CRITICAL: "🔴"
        }

        emoji = severity_emoji.get(incident.severity, "🔵")

        if notification_type == "incident_created":
            subject = f"{emoji} New Incident: {incident.title}"
            message = f"""
A new {incident.severity.value} severity incident has been created:

Title: {incident.title}
Status: {incident.status.value.title()}
Severity: {incident.severity.value.title()}
Started: {incident.started_at.strftime('%Y-%m-%d %H:%M:%S')} UTC

{incident.description or 'No additional details provided.'}

Affected Services: {', '.join(incident.affected_services) if incident.affected_services else 'None specified'}

This is an automated notification from the Incident Center.
            """.strip()

        elif notification_type == "incident_updated":
            subject = f"{emoji} Incident Update: {incident.title}"
            message = f"""
An incident has been updated:

Title: {incident.title}
Status: {incident.status.value.title()}
Severity: {incident.severity.value.title()}

Update: {update_message or 'No update message provided.'}

This is an automated notification from the Incident Center.
            """.strip()

        else:
            subject = f"{emoji} Incident Notification: {incident.title}"
            message = f"Incident: {incident.title}\nStatus: {incident.status.value}"

        return subject, message

    def _validate_channel(self, channel: Dict[str, Any]) -> bool:
        """Validate a notification channel configuration."""

        channel_type = channel.get("type")
        if channel_type not in [c.value for c in NotificationChannel]:
            return False

        address = channel.get("address", "")
        if not address:
            return False

        # Basic validation based on channel type
        if channel_type == NotificationChannel.EMAIL.value:
            return "@" in address and "." in address
        elif channel_type == NotificationChannel.SMS.value:
            return address.startswith("+") and len(address) >= 10
        elif channel_type == NotificationChannel.WEBHOOK.value:
            return address.startswith("http")

        return True

    async def _count_tenant_subscriptions(
        self,
        db: AsyncSession,
        tenant_id: str
    ) -> int:
        """Count existing subscriptions for a tenant."""

        result = await db.execute(
            select(NotificationSubscription.id).where(
                and_(
                    NotificationSubscription.tenant_id == tenant_id,
                    NotificationSubscription.is_active == True
                )
            )
        )

        return len(result.scalars().all())

    def _is_in_quiet_hours(self, subscription: NotificationSubscription) -> bool:
        """Check if current time is in subscription's quiet hours."""

        if not subscription.quiet_hours_start or not subscription.quiet_hours_end:
            return False

        now = datetime.utcnow()
        current_time = now.strftime("%H:%M")

        start_time = subscription.quiet_hours_start
        end_time = subscription.quiet_hours_end

        # Handle overnight quiet hours (e.g., 22:00 to 06:00)
        if start_time > end_time:
            return current_time >= start_time or current_time <= end_time
        else:
            return start_time <= current_time <= end_time
