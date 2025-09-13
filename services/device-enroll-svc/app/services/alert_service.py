"""Alert rules service for Device Enrollment."""

from typing import Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AlertRule, AlertRuleAction, AlertRuleCondition
from .notification_service import AlertNotificationService

logger = structlog.get_logger(__name__)


class AlertRulesService:
    """Service for managing alert rules."""

    def __init__(self) -> None:
        """Initialize service."""
        self.notification_service = AlertNotificationService()

    async def create_alert_rule(
        self,
        db: AsyncSession,
        name: str,
        metric: str,
        condition: AlertRuleCondition,
        threshold: str,
        actions: List[AlertRuleAction],
        created_by: UUID,
        description: Optional[str] = None,
        window_minutes: int = 15,
        tenant_id: Optional[UUID] = None,
        device_filter: Optional[Dict] = None,
        action_config: Optional[Dict] = None
    ) -> AlertRule:
        """Create a new alert rule."""
        try:
            rule = AlertRule(
                name=name,
                description=description,
                metric=metric,
                condition=condition,
                threshold=threshold,
                window_minutes=window_minutes,
                tenant_id=tenant_id,
                device_filter=device_filter,
                actions=actions,
                action_config=action_config,
                created_by=created_by
            )

            db.add(rule)
            await db.commit()
            await db.refresh(rule)

            logger.info(
                "Alert rule created",
                rule_id=rule.rule_id,
                name=name,
                metric=metric,
                created_by=created_by
            )

            return rule

        except Exception as e:
            logger.error("Failed to create alert rule", name=name, error=str(e))
            raise

    async def get_alert_rules(
        self,
        db: AsyncSession,
        tenant_id: Optional[UUID] = None,
        is_enabled: Optional[bool] = None
    ) -> List[AlertRule]:
        """Get alert rules with optional filtering."""
        try:
            query = select(AlertRule)

            conditions = []
            if tenant_id:
                conditions.append(AlertRule.tenant_id == tenant_id)
            if is_enabled is not None:
                conditions.append(AlertRule.is_enabled == is_enabled)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(AlertRule.created_at.desc())

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error("Failed to get alert rules", error=str(e))
            raise

    async def get_alert_rule(
        self, db: AsyncSession, rule_id: UUID
    ) -> Optional[AlertRule]:
        """Get a specific alert rule by ID."""
        try:
            result = await db.execute(
                select(AlertRule).where(AlertRule.rule_id == rule_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error("Failed to get alert rule", rule_id=rule_id, error=str(e))
            raise

    async def update_alert_rule(
        self,
        db: AsyncSession,
        rule_id: UUID,
        **kwargs
    ) -> Optional[AlertRule]:
        """Update an alert rule."""
        try:
            # Remove None values
            update_data = {k: v for k, v in kwargs.items() if v is not None}

            if not update_data:
                return await self.get_alert_rule(db, rule_id)

            await db.execute(
                update(AlertRule)
                .where(AlertRule.rule_id == rule_id)
                .values(**update_data)
            )
            await db.commit()

            logger.info(
                "Alert rule updated",
                rule_id=rule_id,
                updated_fields=list(update_data.keys())
            )

            return await self.get_alert_rule(db, rule_id)

        except Exception as e:
            logger.error("Failed to update alert rule", rule_id=rule_id, error=str(e))
            raise

    async def delete_alert_rule(
        self, db: AsyncSession, rule_id: UUID
    ) -> bool:
        """Delete an alert rule."""
        try:
            rule = await self.get_alert_rule(db, rule_id)
            if not rule:
                return False

            await db.delete(rule)
            await db.commit()

            logger.info("Alert rule deleted", rule_id=rule_id, name=rule.name)
            return True

        except Exception as e:
            logger.error("Failed to delete alert rule", rule_id=rule_id, error=str(e))
            raise

    async def toggle_alert_rule(
        self, db: AsyncSession, rule_id: UUID, enabled: bool
    ) -> Optional[AlertRule]:
        """Enable or disable an alert rule."""
        try:
            return await self.update_alert_rule(db, rule_id, is_enabled=enabled)

        except Exception as e:
            logger.error("Failed to toggle alert rule", rule_id=rule_id, error=str(e))
            raise

    async def evaluate_alert_rules(
        self, db: AsyncSession, metric: str, value: str, context: Dict
    ) -> None:
        """Evaluate all alert rules for a given metric."""
        try:
            # Get all enabled rules for this metric
            result = await db.execute(
                select(AlertRule).where(
                    and_(
                        AlertRule.metric == metric,
                        AlertRule.is_enabled == True
                    )
                )
            )
            rules = result.scalars().all()

            for rule in rules:
                try:
                    if await self._evaluate_rule_condition(rule, value, context):
                        # Rule condition met, trigger alert
                        affected_devices = context.get("affected_devices", [])
                        trigger_reason = f"{metric} {rule.condition} {rule.threshold} (current: {value})"

                        await self.notification_service.trigger_alert(
                            db=db,
                            rule=rule,
                            metric_value=value,
                            affected_devices=affected_devices,
                            trigger_reason=trigger_reason
                        )

                        # Update rule trigger count and timestamp
                        await self.update_alert_rule(
                            db,
                            rule.rule_id,
                            trigger_count=rule.trigger_count + 1,
                            last_triggered_at=context.get("timestamp")
                        )

                except Exception as e:
                    logger.error(
                        "Failed to evaluate alert rule",
                        rule_id=rule.rule_id,
                        error=str(e)
                    )

        except Exception as e:
            logger.error("Failed to evaluate alert rules", metric=metric, error=str(e))

    async def _evaluate_rule_condition(
        self, rule: AlertRule, value: str, context: Dict
    ) -> bool:
        """Evaluate if a rule condition is met."""
        try:
            if rule.condition == AlertRuleCondition.GREATER_THAN:
                return float(value) > float(rule.threshold)
            elif rule.condition == AlertRuleCondition.LESS_THAN:
                return float(value) < float(rule.threshold)
            elif rule.condition == AlertRuleCondition.EQUALS:
                return value == rule.threshold
            elif rule.condition == AlertRuleCondition.NOT_EQUALS:
                return value != rule.threshold
            elif rule.condition == AlertRuleCondition.CONTAINS:
                return rule.threshold in value
            else:
                logger.warning("Unknown alert rule condition", condition=rule.condition)
                return False

        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to evaluate rule condition",
                rule_id=rule.rule_id,
                value=value,
                threshold=rule.threshold,
                error=str(e)
            )
            return False

    def get_available_metrics(self) -> List[Dict[str, str]]:
        """Get list of available metrics for alert rules."""
        return [
            {
                "key": "online_percentage",
                "name": "Online Percentage",
                "description": "Percentage of devices online",
                "unit": "%"
            },
            {
                "key": "offline_device_count",
                "name": "Offline Device Count",
                "description": "Number of offline devices",
                "unit": "devices"
            },
            {
                "key": "firmware_drift_percentage",
                "name": "Firmware Drift Percentage",
                "description": "Percentage of devices on non-latest firmware",
                "unit": "%"
            },
            {
                "key": "mean_heartbeat_minutes",
                "name": "Mean Heartbeat Interval",
                "description": "Average heartbeat interval",
                "unit": "minutes"
            },
            {
                "key": "enrollment_failure_rate",
                "name": "Enrollment Failure Rate",
                "description": "Rate of enrollment failures",
                "unit": "%"
            },
            {
                "key": "certificate_expiry_count",
                "name": "Expiring Certificates",
                "description": "Number of certificates expiring soon",
                "unit": "certificates"
            }
        ]

    def get_available_conditions(self) -> List[Dict[str, str]]:
        """Get list of available conditions for alert rules."""
        return [
            {
                "key": AlertRuleCondition.GREATER_THAN,
                "name": "Greater Than",
                "description": "Trigger when metric value is greater than threshold"
            },
            {
                "key": AlertRuleCondition.LESS_THAN,
                "name": "Less Than",
                "description": "Trigger when metric value is less than threshold"
            },
            {
                "key": AlertRuleCondition.EQUALS,
                "name": "Equals",
                "description": "Trigger when metric value equals threshold"
            },
            {
                "key": AlertRuleCondition.NOT_EQUALS,
                "name": "Not Equals",
                "description": "Trigger when metric value does not equal threshold"
            },
            {
                "key": AlertRuleCondition.CONTAINS,
                "name": "Contains",
                "description": "Trigger when metric value contains threshold string"
            }
        ]

    def get_available_actions(self) -> List[Dict[str, str]]:
        """Get list of available actions for alert rules."""
        return [
            {
                "key": AlertRuleAction.EMAIL,
                "name": "Email",
                "description": "Send email notification"
            },
            {
                "key": AlertRuleAction.SLACK,
                "name": "Slack",
                "description": "Send Slack message"
            },
            {
                "key": AlertRuleAction.WEBHOOK,
                "name": "Webhook",
                "description": "Send HTTP webhook"
            },
            {
                "key": AlertRuleAction.DEVICE_LOCK,
                "name": "Device Lock",
                "description": "Lock affected devices"
            },
            {
                "key": AlertRuleAction.DEVICE_WIPE,
                "name": "Device Wipe",
                "description": "Wipe affected devices (CRITICAL)"
            }
        ]
