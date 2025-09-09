"""Firmware update endpoints for Device OTA & Heartbeat Service."""
# flake8: noqa: E501

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# pylint: disable=import-error
from app.database import get_db
from app.models import (
    DeploymentRing,
    FirmwareUpdate,
    UpdateStatus,
)
from app.schemas import (
    FirmwareUpdateRequest,
    FirmwareUpdateResponse,
    RollbackRequest,
    UpdateCheckRequest,
    UpdateCheckResponse,
    UpdateListResponse,
    UpdateMetrics,
    UpdateProgressReport,
    UpdateRolloutStatus,
)
from app.services.firmware_service import FirmwareService
from app.services.update_service import UpdateService

router = APIRouter()


@router.post(
    "/firmware",
    response_model=FirmwareUpdateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_firmware_update(
    request: FirmwareUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> FirmwareUpdateResponse:
    """Create a new firmware update."""
    firmware_service = FirmwareService(db)

    # Create the firmware update
    firmware_update = await firmware_service.create_update(request)

    return FirmwareUpdateResponse.from_orm(firmware_update)


@router.get("/update", response_model=UpdateCheckResponse)
async def check_for_updates(
    device_id: UUID = Query(..., description="Device identifier"),
    device_type: str = Query(..., description="Device type"),
    current_firmware_version: str = Query(..., description="Current firmware version"),
    current_app_version: str | None = Query(None, description="Current app version"),
    hardware_model: str | None = Query(None, description="Hardware model"),
    battery_level: int | None = Query(None, ge=0, le=100, description="Battery level"),
    storage_available_mb: int | None = Query(None, ge=0, description="Available storage MB"),
    network_type: str | None = Query(None, description="Network connection type"),
    db: AsyncSession = Depends(get_db),
) -> UpdateCheckResponse:
    """Check for available updates for a device."""
    update_service = UpdateService(db)

    # Create request object
    request = UpdateCheckRequest(
        device_id=device_id,
        device_type=device_type,
        current_firmware_version=current_firmware_version,
        current_app_version=current_app_version,
        hardware_model=hardware_model,
        battery_level=battery_level,
        storage_available_mb=storage_available_mb,
        network_type=network_type,
    )

    # Check for updates
    response = await update_service.check_for_updates(request)

    return response


@router.post("/update/{update_id}/progress")
async def report_update_progress(
    update_id: UUID,
    progress: UpdateProgressReport,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Report update progress from device."""
    update_service = UpdateService(db)

    # Update progress
    await update_service.update_progress(update_id, progress)

    return {"status": "success", "message": "Progress updated"}


@router.get("/updates", response_model=UpdateListResponse)
async def list_firmware_updates(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    status_filter: UpdateStatus | None = Query(None, description="Filter by status"),
    ring_filter: DeploymentRing | None = Query(None, description="Filter by deployment ring"),
    db: AsyncSession = Depends(get_db),
) -> UpdateListResponse:
    """List firmware updates."""
    firmware_service = FirmwareService(db)

    # Get updates
    updates, total = await firmware_service.list_updates(
        page=page,
        size=size,
        status_filter=status_filter,
        ring_filter=ring_filter,
    )

    return UpdateListResponse(
        updates=[FirmwareUpdateResponse.from_orm(update) for update in updates],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/updates/{update_id}", response_model=FirmwareUpdateResponse)
async def get_firmware_update(
    update_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FirmwareUpdateResponse:
    """Get firmware update by ID."""
    stmt = (
        select(FirmwareUpdate)
        # pylint: disable=no-member
        .options(selectinload(FirmwareUpdate.device_updates))
        .where(FirmwareUpdate.update_id == update_id)
    )
    result = await db.execute(stmt)
    firmware_update = result.scalar_one_or_none()

    if not firmware_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Firmware update not found",
        )

    return FirmwareUpdateResponse.from_orm(firmware_update)


@router.get("/updates/{update_id}/status", response_model=UpdateRolloutStatus)
async def get_update_rollout_status(
    update_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> UpdateRolloutStatus:
    """Get update rollout status."""
    update_service = UpdateService(db)

    # Get rollout status
    status_data = await update_service.get_rollout_status(update_id)

    return status_data


@router.get("/updates/{update_id}/metrics", response_model=UpdateMetrics)
async def get_update_metrics(
    update_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> UpdateMetrics:
    """Get update deployment metrics."""
    update_service = UpdateService(db)

    # Get metrics
    metrics = await update_service.get_update_metrics(update_id)

    return metrics


@router.post("/updates/{update_id}/rollback")
async def rollback_update(
    update_id: UUID,
    request: RollbackRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Initiate update rollback."""
    update_service = UpdateService(db)

    # Initiate rollback
    await update_service.initiate_rollback(update_id, request)

    return {"status": "success", "message": "Rollback initiated"}


@router.post("/updates/{update_id}/deploy")
async def deploy_update(
    update_id: UUID,
    target_ring: DeploymentRing = Query(..., description="Target deployment ring"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Deploy update to next ring."""
    firmware_service = FirmwareService(db)

    # Deploy to ring
    await firmware_service.deploy_to_ring(update_id, target_ring)

    return {"status": "success", "message": f"Deployed to {target_ring.value} ring"}


@router.delete("/updates/{update_id}")
async def delete_firmware_update(
    update_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete firmware update (soft delete)."""
    stmt = select(FirmwareUpdate).where(FirmwareUpdate.update_id == update_id)
    result = await db.execute(stmt)
    firmware_update = result.scalar_one_or_none()

    if not firmware_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Firmware update not found",
        )

    # Mark as deleted
    firmware_update.is_deleted = True
    firmware_update.updated_at = datetime.utcnow()

    await db.commit()

    return {"status": "success", "message": "Firmware update deleted"}
