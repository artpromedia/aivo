"""Remote device action routes for Device OTA & Heartbeat Service."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import RemoteActionStatus, RemoteActionType
from app.schemas import (
    RemoteActionRequest,
    RemoteActionResponse,
    RemoteActionListResponse,
    RemoteActionStatsResponse,
)
from app.services.remote_action_service import RemoteActionService

router = APIRouter()


@router.post(
    "/devices/{device_id}/actions/{action_type}",
    response_model=RemoteActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Device Action",
    description="Execute a remote device action (wipe, reboot, lock)",
)
async def execute_device_action(
    device_id: UUID,
    action_type: str,
    request: RemoteActionRequest,
    db: AsyncSession = Depends(get_db),
) -> RemoteActionResponse:
    """Execute a remote device action."""
    try:
        # Validate action type
        try:
            action_enum = RemoteActionType(action_type)
        except ValueError:
            valid_actions = [action.value for action in RemoteActionType]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action type. Must be one of: {', '.join(valid_actions)}",
            )

        # Create action service
        action_service = RemoteActionService(db)

        # Create the action
        action = await action_service.create_action(
            device_id=device_id,
            action_type=action_enum,
            initiated_by=request.initiated_by,
            reason=request.reason,
            parameters=request.parameters,
            priority=request.priority,
            correlation_id=request.correlation_id,
            client_ip=request.client_ip,
        )

        return RemoteActionResponse(
            action_id=action.action_id,
            device_id=action.device_id,
            action_type=action.action_type.value,
            status=action.status.value,
            reason=action.reason,
            parameters=action.parameters,
            priority=action.priority,
            initiated_by=action.initiated_by,
            created_at=action.created_at,
            sent_at=action.sent_at,
            acknowledged_at=action.acknowledged_at,
            completed_at=action.completed_at,
            expires_at=action.expires_at,
            error_message=action.error_message,
            attempts=action.attempts,
            max_attempts=action.max_attempts,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute device action: {str(e)}",
        )


@router.get(
    "/devices/{device_id}/actions",
    response_model=RemoteActionListResponse,
    summary="Get Device Actions",
    description="Get list of actions for a specific device",
)
async def get_device_actions(
    device_id: UUID,
    status_filter: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> RemoteActionListResponse:
    """Get actions for a specific device."""
    try:
        # Validate status filter if provided
        status_enum = None
        if status_filter:
            try:
                status_enum = RemoteActionStatus(status_filter)
            except ValueError:
                valid_statuses = [status.value for status in RemoteActionStatus]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}",
                )

        action_service = RemoteActionService(db)
        actions = await action_service.get_device_actions(
            device_id=device_id,
            status_filter=status_enum,
            limit=limit,
        )

        action_responses = [
            RemoteActionResponse(
                action_id=action.action_id,
                device_id=action.device_id,
                action_type=action.action_type.value,
                status=action.status.value,
                reason=action.reason,
                parameters=action.parameters,
                priority=action.priority,
                initiated_by=action.initiated_by,
                created_at=action.created_at,
                sent_at=action.sent_at,
                acknowledged_at=action.acknowledged_at,
                completed_at=action.completed_at,
                expires_at=action.expires_at,
                error_message=action.error_message,
                attempts=action.attempts,
                max_attempts=action.max_attempts,
            )
            for action in actions
        ]

        return RemoteActionListResponse(
            actions=action_responses,
            total=len(action_responses),
            device_id=device_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device actions: {str(e)}",
        )


@router.get(
    "/actions/{action_id}",
    response_model=RemoteActionResponse,
    summary="Get Action Details",
    description="Get details of a specific action",
)
async def get_action_details(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> RemoteActionResponse:
    """Get details of a specific action."""
    try:
        action_service = RemoteActionService(db)
        action = await action_service.get_action_by_id(action_id)

        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action not found",
            )

        return RemoteActionResponse(
            action_id=action.action_id,
            device_id=action.device_id,
            action_type=action.action_type.value,
            status=action.status.value,
            reason=action.reason,
            parameters=action.parameters,
            priority=action.priority,
            initiated_by=action.initiated_by,
            created_at=action.created_at,
            sent_at=action.sent_at,
            acknowledged_at=action.acknowledged_at,
            completed_at=action.completed_at,
            expires_at=action.expires_at,
            error_message=action.error_message,
            attempts=action.attempts,
            max_attempts=action.max_attempts,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get action details: {str(e)}",
        )


@router.post(
    "/actions/{action_id}/acknowledge",
    status_code=status.HTTP_200_OK,
    summary="Acknowledge Action",
    description="Mark an action as acknowledged by the device",
)
async def acknowledge_action(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Acknowledge an action."""
    try:
        action_service = RemoteActionService(db)
        success = await action_service.mark_action_acknowledged(action_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action not found",
            )

        return {"message": "Action acknowledged", "action_id": str(action_id)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge action: {str(e)}",
        )


@router.post(
    "/actions/{action_id}/complete",
    status_code=status.HTTP_200_OK,
    summary="Complete Action",
    description="Mark an action as completed",
)
async def complete_action(
    action_id: UUID,
    result_data: Optional[dict] = None,
    device_response: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Complete an action."""
    try:
        action_service = RemoteActionService(db)
        success = await action_service.mark_action_completed(
            action_id=action_id,
            result_data=result_data,
            device_response=device_response,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action not found",
            )

        return {"message": "Action completed", "action_id": str(action_id)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete action: {str(e)}",
        )


@router.post(
    "/actions/{action_id}/fail",
    status_code=status.HTTP_200_OK,
    summary="Fail Action",
    description="Mark an action as failed",
)
async def fail_action(
    action_id: UUID,
    error_message: str,
    device_response: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark an action as failed."""
    try:
        action_service = RemoteActionService(db)
        success = await action_service.mark_action_failed(
            action_id=action_id,
            error_message=error_message,
            device_response=device_response,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action not found",
            )

        return {"message": "Action marked as failed", "action_id": str(action_id)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark action as failed: {str(e)}",
        )


@router.get(
    "/actions/stats",
    response_model=RemoteActionStatsResponse,
    summary="Get Action Statistics",
    description="Get statistics about remote actions",
)
async def get_action_statistics(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
) -> RemoteActionStatsResponse:
    """Get action statistics."""
    try:
        action_service = RemoteActionService(db)
        stats = await action_service.get_action_statistics(days=days)

        return RemoteActionStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get action statistics: {str(e)}",
        )


@router.post(
    "/actions/cleanup",
    summary="Cleanup Expired Actions",
    description="Clean up expired actions",
)
async def cleanup_expired_actions(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Clean up expired actions."""
    try:
        action_service = RemoteActionService(db)
        expired_count = await action_service.cleanup_expired_actions()

        return {
            "message": "Expired actions cleaned up",
            "expired_count": expired_count,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup expired actions: {str(e)}",
        )
