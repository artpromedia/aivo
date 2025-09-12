"""Device heartbeat endpoints for Device OTA & Heartbeat Service."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import HeartbeatRequest, HeartbeatResponse

# pylint: disable=import-error,no-name-in-module
from app.services.heartbeat_service import (
    HeartbeatService,
)

router = APIRouter()


@router.post(
    "/heartbeat",
    response_model=HeartbeatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def receive_heartbeat(
    heartbeat: HeartbeatRequest,
    db: AsyncSession = Depends(get_db),
) -> HeartbeatResponse:
    """Receive device heartbeat."""
    heartbeat_service = HeartbeatService(db)

    # Process heartbeat
    response = await heartbeat_service.process_heartbeat(heartbeat)

    return response


@router.get("/devices/{device_id}/heartbeats")
async def get_device_heartbeats(
    device_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get recent heartbeats for a device."""
    heartbeat_service = HeartbeatService(db)

    # Get heartbeats
    heartbeats = await heartbeat_service.get_device_heartbeats(device_id, limit)

    return {
        "device_id": device_id,
        "heartbeats": heartbeats,
        "count": len(heartbeats),
    }


@router.get("/devices/{device_id}/status")
async def get_device_status(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current device status."""
    heartbeat_service = HeartbeatService(db)

    # Get device status
    status_data = await heartbeat_service.get_device_status(device_id)

    return status_data
