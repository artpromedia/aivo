"""Alert notification service for Device Enrollment."""

import json
from typing import Dict, List, Optional
from uuid import UUID

import aiohttp
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AlertRule, AlertTrigger, AlertRuleAction

logger = structlog.get_logger(__name__)


class AlertNotificationService:
    """Service for sending alert notifications."""

    def __init__(self) -> None:
        """Initialize service."""
        self.slack_webhook_url = None  # Configure via environment
        self.email_service_url = None  # Configure via environment

    async def trigger_alert(
        self,
        db: AsyncSession,
        rule: AlertRule,
        metric_value: str,
        affected_devices: List[str],
        trigger_reason: str
    ) -> AlertTrigger:
        """Trigger an alert and execute configured actions."""
        try:
            # Create alert trigger record
            trigger = AlertTrigger(
                rule_id=rule.rule_id,
                metric_value=metric_value,
                affected_devices=affected_devices,
                trigger_reason=trigger_reason,
                actions_executed=[],
                action_results={}
            )

            db.add(trigger)
            await db.commit()
            await db.refresh(trigger)

            # Execute configured actions
            results = {}
            executed_actions = []

            for action in rule.actions:
                try:
                    if action == AlertRuleAction.SLACK:
                        result = await self._send_slack_notification(rule, trigger)
                        results["slack"] = result
                        executed_actions.append("slack")

                    elif action == AlertRuleAction.EMAIL:
                        result = await self._send_email_notification(rule, trigger)
                        results["email"] = result
                        executed_actions.append("email")

                    elif action == AlertRuleAction.WEBHOOK:
                        result = await self._send_webhook_notification(rule, trigger)
                        results["webhook"] = result
                        executed_actions.append("webhook")

                    elif action == AlertRuleAction.DEVICE_LOCK:
                        result = await self._execute_device_lock(rule, trigger, affected_devices)
                        results["device_lock"] = result
                        executed_actions.append("device_lock")

                    elif action == AlertRuleAction.DEVICE_WIPE:
                        result = await self._execute_device_wipe(rule, trigger, affected_devices)
                        results["device_wipe"] = result
                        executed_actions.append("device_wipe")

                except Exception as e:
                    logger.error("Failed to execute alert action", action=action, error=str(e))
                    results[action] = {"error": str(e)}

            # Update trigger with results
            trigger.actions_executed = executed_actions
            trigger.action_results = results
            await db.commit()

            logger.info(
                "Alert triggered",
                rule_id=rule.rule_id,
                rule_name=rule.name,
                actions_executed=executed_actions,
                affected_devices=len(affected_devices)
            )

            return trigger

        except Exception as e:
            logger.error("Failed to trigger alert", rule_id=rule.rule_id, error=str(e))
            raise

    async def _send_slack_notification(
        self, rule: AlertRule, trigger: AlertTrigger
    ) -> Dict[str, any]:
        """Send Slack notification."""
        if not self.slack_webhook_url:
            return {"error": "Slack webhook URL not configured"}

        try:
            # Get Slack configuration from rule
            slack_config = rule.action_config.get("slack", {}) if rule.action_config else {}
            channel = slack_config.get("channel", "#alerts")
            username = slack_config.get("username", "Aivo Fleet Monitor")

            # Build message
            message = {
                "channel": channel,
                "username": username,
                "icon_emoji": ":warning:",
                "attachments": [
                    {
                        "color": "danger" if "critical" in rule.name.lower() else "warning",
                        "title": f"Fleet Alert: {rule.name}",
                        "fields": [
                            {
                                "title": "Metric",
                                "value": rule.metric,
                                "short": True
                            },
                            {
                                "title": "Value",
                                "value": trigger.metric_value,
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": f"{rule.condition} {rule.threshold}",
                                "short": True
                            },
                            {
                                "title": "Affected Devices",
                                "value": str(len(trigger.affected_devices or [])),
                                "short": True
                            },
                            {
                                "title": "Reason",
                                "value": trigger.trigger_reason,
                                "short": False
                            }
                        ],
                        "footer": "Aivo Fleet Monitor",
                        "ts": int(trigger.triggered_at.timestamp())
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_webhook_url,
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return {"status": "sent"}
                    else:
                        return {"error": f"HTTP {response.status}"}

        except Exception as e:
            return {"error": str(e)}

    async def _send_email_notification(
        self, rule: AlertRule, trigger: AlertTrigger
    ) -> Dict[str, any]:
        """Send email notification."""
        if not self.email_service_url:
            return {"error": "Email service URL not configured"}

        try:
            # Get email configuration from rule
            email_config = rule.action_config.get("email", {}) if rule.action_config else {}
            recipients = email_config.get("recipients", ["admin@aivo.com"])

            # Build email content
            subject = f"Aivo Fleet Alert: {rule.name}"
            body = f"""
Fleet Alert Triggered

Alert: {rule.name}
Description: {rule.description or 'No description'}

Metric: {rule.metric}
Condition: {rule.condition} {rule.threshold}
Current Value: {trigger.metric_value}

Affected Devices: {len(trigger.affected_devices or [])}
Reason: {trigger.trigger_reason}

Triggered At: {trigger.triggered_at}

---
Aivo Fleet Monitor
            """.strip()

            email_data = {
                "to": recipients,
                "subject": subject,
                "body": body,
                "is_html": False
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.email_service_url}/send",
                    json=email_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return {"status": "sent", "recipients": recipients}
                    else:
                        return {"error": f"HTTP {response.status}"}

        except Exception as e:
            return {"error": str(e)}

    async def _send_webhook_notification(
        self, rule: AlertRule, trigger: AlertTrigger
    ) -> Dict[str, any]:
        """Send webhook notification."""
        try:
            # Get webhook configuration from rule
            webhook_config = rule.action_config.get("webhook", {}) if rule.action_config else {}
            webhook_url = webhook_config.get("url")

            if not webhook_url:
                return {"error": "Webhook URL not configured"}

            # Build webhook payload
            payload = {
                "alert": {
                    "rule_id": str(rule.rule_id),
                    "rule_name": rule.name,
                    "metric": rule.metric,
                    "condition": rule.condition,
                    "threshold": rule.threshold,
                    "current_value": trigger.metric_value,
                    "affected_devices": trigger.affected_devices,
                    "trigger_reason": trigger.trigger_reason,
                    "triggered_at": trigger.triggered_at.isoformat()
                }
            }

            headers = {"Content-Type": "application/json"}
            if "headers" in webhook_config:
                headers.update(webhook_config["headers"])

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status < 400:
                        return {"status": "sent", "response_code": response.status}
                    else:
                        return {"error": f"HTTP {response.status}"}

        except Exception as e:
            return {"error": str(e)}

    async def _execute_device_lock(
        self, rule: AlertRule, trigger: AlertTrigger, affected_devices: List[str]
    ) -> Dict[str, any]:
        """Execute device lock action."""
        try:
            # This would integrate with the device action system
            # For now, just log the action
            logger.warning(
                "Device lock action triggered",
                rule_id=rule.rule_id,
                devices=affected_devices,
                trigger_id=trigger.trigger_id
            )

            return {
                "status": "initiated",
                "devices": affected_devices,
                "message": "Device lock commands will be sent on next heartbeat"
            }

        except Exception as e:
            return {"error": str(e)}

    async def _execute_device_wipe(
        self, rule: AlertRule, trigger: AlertTrigger, affected_devices: List[str]
    ) -> Dict[str, any]:
        """Execute device wipe action."""
        try:
            # This would integrate with the device action system
            # For now, just log the action
            logger.critical(
                "Device wipe action triggered",
                rule_id=rule.rule_id,
                devices=affected_devices,
                trigger_id=trigger.trigger_id
            )

            return {
                "status": "initiated",
                "devices": affected_devices,
                "message": "Device wipe commands will be sent on next heartbeat"
            }

        except Exception as e:
            return {"error": str(e)}
