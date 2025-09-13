"""Fleet health and alert management routes for Device Enrollment Service."""

from typing import Annotated, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import (
    AlertMetricsResponse,
    AlertRuleListResponse,
    AlertRuleRequest,
    AlertRuleResponse,
    AlertTriggerResponse,
    DeviceActionRequest,
    DeviceActionResponse,
    ErrorResponse,
    FleetHealthResponse,
)
from ..services.alert_service import AlertRulesService
from ..services.fleet_service import FleetHealthService

logger = structlog.get_logger(__name__)

router = APIRouter()

# Service instances
fleet_service = FleetHealthService()
alert_service = AlertRulesService()


@router.get(
    "/fleet/health",
    response_model=FleetHealthResponse,
    summary="Get Fleet Health Metrics",
    description="Get aggregated fleet health metrics including uptime, heartbeat gaps, and firmware drift",
    responses={
        200: {"description": "Fleet health metrics retrieved"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_fleet_health(
    tenant_id: Optional[UUID] = None,
    range_days: int = 30,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> FleetHealthResponse:
    """Get fleet health metrics."""
    try:
        health_data = await fleet_service.get_fleet_health(
            db=db, tenant_id=tenant_id, range_days=range_days
        )
        return FleetHealthResponse(**health_data)

    except Exception as e:
        logger.error("Failed to get fleet health", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve fleet health metrics",
        ) from e


# Alert Rules Management

@router.get(
    "/alerts/rules",
    response_model=AlertRuleListResponse,
    summary="List Alert Rules",
    description="Get list of alert rules with optional filtering",
    responses={
        200: {"description": "Alert rules retrieved"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_alert_rules(
    tenant_id: Optional[UUID] = None,
    is_enabled: Optional[bool] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AlertRuleListResponse:
    """List alert rules."""
    try:
        rules = await alert_service.get_alert_rules(
            db=db, tenant_id=tenant_id, is_enabled=is_enabled
        )

        rule_responses = []
        for rule in rules:
            rule_responses.append(
                AlertRuleResponse(
                    rule_id=rule.rule_id,
                    name=rule.name,
                    description=rule.description,
                    metric=rule.metric,
                    condition=rule.condition.value,
                    threshold=rule.threshold,
                    window_minutes=rule.window_minutes,
                    tenant_id=rule.tenant_id,
                    device_filter=rule.device_filter,
                    actions=[action.value for action in rule.actions],
                    action_config=rule.action_config,
                    is_enabled=rule.is_enabled,
                    trigger_count=rule.trigger_count,
                    last_triggered_at=rule.last_triggered_at,
                    created_by=rule.created_by,
                    created_at=rule.created_at,
                    updated_at=rule.updated_at,
                )
            )

        return AlertRuleListResponse(rules=rule_responses, total=len(rule_responses))

    except Exception as e:
        logger.error("Failed to list alert rules", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alert rules",
        ) from e


@router.post(
    "/alerts/rules",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Alert Rule",
    description="Create a new alert rule",
    responses={
        201: {"description": "Alert rule created"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_alert_rule(
    request: AlertRuleRequest,
    created_by: UUID,  # This would come from authentication
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AlertRuleResponse:
    """Create a new alert rule."""
    try:
        # Convert string actions to enum values
        from ..models import AlertRuleAction, AlertRuleCondition

        actions = [AlertRuleAction(action) for action in request.actions]
        condition = AlertRuleCondition(request.condition)

        rule = await alert_service.create_alert_rule(
            db=db,
            name=request.name,
            description=request.description,
            metric=request.metric,
            condition=condition,
            threshold=request.threshold,
            window_minutes=request.window_minutes,
            tenant_id=request.tenant_id,
            device_filter=request.device_filter,
            actions=actions,
            action_config=request.action_config,
            created_by=created_by,
        )

        return AlertRuleResponse(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            metric=rule.metric,
            condition=rule.condition.value,
            threshold=rule.threshold,
            window_minutes=rule.window_minutes,
            tenant_id=rule.tenant_id,
            device_filter=rule.device_filter,
            actions=[action.value for action in rule.actions],
            action_config=rule.action_config,
            is_enabled=rule.is_enabled,
            trigger_count=rule.trigger_count,
            last_triggered_at=rule.last_triggered_at,
            created_by=rule.created_by,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    except ValueError as e:
        logger.warning("Invalid alert rule request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Failed to create alert rule", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert rule",
        ) from e


@router.get(
    "/alerts/rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Get Alert Rule",
    description="Get a specific alert rule by ID",
    responses={
        200: {"description": "Alert rule retrieved"},
        404: {"model": ErrorResponse, "description": "Alert rule not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_alert_rule(
    rule_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AlertRuleResponse:
    """Get a specific alert rule."""
    try:
        rule = await alert_service.get_alert_rule(db=db, rule_id=rule_id)

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert rule not found",
            )

        return AlertRuleResponse(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            metric=rule.metric,
            condition=rule.condition.value,
            threshold=rule.threshold,
            window_minutes=rule.window_minutes,
            tenant_id=rule.tenant_id,
            device_filter=rule.device_filter,
            actions=[action.value for action in rule.actions],
            action_config=rule.action_config,
            is_enabled=rule.is_enabled,
            trigger_count=rule.trigger_count,
            last_triggered_at=rule.last_triggered_at,
            created_by=rule.created_by,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get alert rule", rule_id=rule_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alert rule",
        ) from e


@router.put(
    "/alerts/rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Update Alert Rule",
    description="Update an existing alert rule",
    responses={
        200: {"description": "Alert rule updated"},
        404: {"model": ErrorResponse, "description": "Alert rule not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_alert_rule(
    rule_id: UUID,
    request: AlertRuleRequest,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AlertRuleResponse:
    """Update an alert rule."""
    try:
        # Check if rule exists
        existing_rule = await alert_service.get_alert_rule(db=db, rule_id=rule_id)
        if not existing_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert rule not found",
            )

        # Convert string actions to enum values
        from ..models import AlertRuleAction, AlertRuleCondition

        actions = [AlertRuleAction(action) for action in request.actions]
        condition = AlertRuleCondition(request.condition)

        updated_rule = await alert_service.update_alert_rule(
            db=db,
            rule_id=rule_id,
            name=request.name,
            description=request.description,
            metric=request.metric,
            condition=condition,
            threshold=request.threshold,
            window_minutes=request.window_minutes,
            tenant_id=request.tenant_id,
            device_filter=request.device_filter,
            actions=actions,
            action_config=request.action_config,
            is_enabled=request.is_enabled,
        )

        return AlertRuleResponse(
            rule_id=updated_rule.rule_id,
            name=updated_rule.name,
            description=updated_rule.description,
            metric=updated_rule.metric,
            condition=updated_rule.condition.value,
            threshold=updated_rule.threshold,
            window_minutes=updated_rule.window_minutes,
            tenant_id=updated_rule.tenant_id,
            device_filter=updated_rule.device_filter,
            actions=[action.value for action in updated_rule.actions],
            action_config=updated_rule.action_config,
            is_enabled=updated_rule.is_enabled,
            trigger_count=updated_rule.trigger_count,
            last_triggered_at=updated_rule.last_triggered_at,
            created_by=updated_rule.created_by,
            created_at=updated_rule.created_at,
            updated_at=updated_rule.updated_at,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid alert rule update request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Failed to update alert rule", rule_id=rule_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert rule",
        ) from e


@router.delete(
    "/alerts/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Alert Rule",
    description="Delete an alert rule",
    responses={
        204: {"description": "Alert rule deleted"},
        404: {"model": ErrorResponse, "description": "Alert rule not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_alert_rule(
    rule_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> None:
    """Delete an alert rule."""
    try:
        deleted = await alert_service.delete_alert_rule(db=db, rule_id=rule_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert rule not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete alert rule", rule_id=rule_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert rule",
        ) from e


@router.post(
    "/alerts/rules/{rule_id}/toggle",
    response_model=AlertRuleResponse,
    summary="Toggle Alert Rule",
    description="Enable or disable an alert rule",
    responses={
        200: {"description": "Alert rule toggled"},
        404: {"model": ErrorResponse, "description": "Alert rule not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def toggle_alert_rule(
    rule_id: UUID,
    enabled: bool,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AlertRuleResponse:
    """Toggle an alert rule enabled/disabled."""
    try:
        rule = await alert_service.toggle_alert_rule(db=db, rule_id=rule_id, enabled=enabled)

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert rule not found",
            )

        return AlertRuleResponse(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            metric=rule.metric,
            condition=rule.condition.value,
            threshold=rule.threshold,
            window_minutes=rule.window_minutes,
            tenant_id=rule.tenant_id,
            device_filter=rule.device_filter,
            actions=[action.value for action in rule.actions],
            action_config=rule.action_config,
            is_enabled=rule.is_enabled,
            trigger_count=rule.trigger_count,
            last_triggered_at=rule.last_triggered_at,
            created_by=rule.created_by,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to toggle alert rule", rule_id=rule_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle alert rule",
        ) from e


@router.get(
    "/alerts/metrics",
    response_model=AlertMetricsResponse,
    summary="Get Available Alert Metrics",
    description="Get list of available metrics, conditions, and actions for alert rules",
    responses={
        200: {"description": "Alert metrics retrieved"},
    },
)
async def get_alert_metrics() -> AlertMetricsResponse:
    """Get available alert metrics, conditions, and actions."""
    return AlertMetricsResponse(
        metrics=alert_service.get_available_metrics(),
        conditions=alert_service.get_available_conditions(),
        actions=alert_service.get_available_actions(),
    )


# Device Actions (basic stub - would be expanded with actual action handling)

@router.post(
    "/devices/{device_id}/actions/{action_type}",
    response_model=DeviceActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Device Action",
    description="Execute a remote device action (wipe, reboot, lock)",
    responses={
        201: {"description": "Device action initiated"},
        400: {"model": ErrorResponse, "description": "Invalid action"},
        404: {"model": ErrorResponse, "description": "Device not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def execute_device_action(
    device_id: UUID,
    action_type: str,
    request: DeviceActionRequest,
    initiated_by: UUID,  # This would come from authentication
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> DeviceActionResponse:
    """Execute a remote device action."""
    try:
        # Validate action type
        valid_actions = ["wipe", "reboot", "lock"]
        if action_type not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action type. Must be one of: {', '.join(valid_actions)}",
            )

        # For now, just create a device action record
        # In a full implementation, this would integrate with the device communication system
        from ..models import DeviceAction

        action = DeviceAction(
            device_id=device_id,
            action_type=action_type,
            reason=request.reason,
            parameters=request.parameters,
            initiated_by=initiated_by,
        )

        db.add(action)
        await db.commit()
        await db.refresh(action)

        logger.info(
            "Device action initiated",
            device_id=device_id,
            action_type=action_type,
            action_id=action.action_id,
            initiated_by=initiated_by,
        )

        return DeviceActionResponse(
            action_id=action.action_id,
            device_id=action.device_id,
            action_type=action.action_type,
            status=action.status,
            reason=action.reason,
            initiated_by=action.initiated_by,
            created_at=action.created_at,
            sent_at=action.sent_at,
            completed_at=action.completed_at,
            error_message=action.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute device action", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute device action",
        ) from e
