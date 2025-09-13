"""Schedules API routes."""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
import uuid

from ..database import database, schedules_table, reports_table
from ..schemas import (
    Schedule, ScheduleCreate, ScheduleUpdate, ScheduleListResponse,
    ScheduleTestResponse
)
from ..services.auth_service import get_current_tenant
from ..services.scheduler import SchedulerService
from ..services.cron_service import CronService

router = APIRouter()
cron_service = CronService()

@router.get("/", response_model=ScheduleListResponse)
async def list_schedules(
    tenant_id: str = Depends(get_current_tenant),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    report_id: Optional[UUID] = Query(None),
    active_only: bool = Query(False)
):
    """List schedules for a tenant with pagination and filtering."""
    offset = (page - 1) * per_page

    # Build query conditions
    conditions = [schedules_table.c.tenant_id == tenant_id]

    if report_id:
        conditions.append(schedules_table.c.report_id == report_id)

    if active_only:
        conditions.append(schedules_table.c.is_active == True)

    # Count total
    count_query = f"""
        SELECT COUNT(*) FROM schedules
        WHERE {" AND ".join([str(c) for c in conditions])}
    """
    total = await database.fetch_val(count_query)

    # Fetch schedules
    query = schedules_table.select().where(*conditions).order_by(
        schedules_table.c.created_at.desc()
    ).offset(offset).limit(per_page)

    schedules = await database.fetch_all(query)

    return ScheduleListResponse(
        schedules=[Schedule(**dict(schedule)) for schedule in schedules],
        total=total,
        page=page,
        per_page=per_page
    )

@router.post("/", response_model=Schedule)
async def create_schedule(
    schedule: ScheduleCreate,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new report schedule."""
    # Verify report exists
    report = await database.fetch_one(
        reports_table.select().where(
            reports_table.c.id == schedule.report_id,
            reports_table.c.tenant_id == tenant_id
        )
    )

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Validate cron expression
    try:
        next_run = cron_service.get_next_run_time(schedule.cron_expression, schedule.timezone)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {str(e)}")

    # Validate delivery configuration
    if schedule.delivery_method in ["email", "both"] and not schedule.recipients:
        raise HTTPException(status_code=400, detail="Email recipients required for email delivery")

    if schedule.delivery_method in ["s3", "both"] and not schedule.s3_config:
        raise HTTPException(status_code=400, detail="S3 configuration required for S3 delivery")

    schedule_data = schedule.dict()
    schedule_data["id"] = uuid.uuid4()
    schedule_data["tenant_id"] = tenant_id
    schedule_data["next_run_at"] = next_run

    query = schedules_table.insert().values(**schedule_data)
    await database.execute(query)

    # Register schedule with scheduler service
    background_tasks.add_task(
        _register_schedule_with_scheduler,
        schedule_data["id"]
    )

    # Fetch and return created schedule
    created_schedule = await database.fetch_one(
        schedules_table.select().where(schedules_table.c.id == schedule_data["id"])
    )

    return Schedule(**dict(created_schedule))

@router.get("/{schedule_id}", response_model=Schedule)
async def get_schedule(
    schedule_id: UUID,
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a specific schedule."""
    query = schedules_table.select().where(
        schedules_table.c.id == schedule_id,
        schedules_table.c.tenant_id == tenant_id
    )

    schedule = await database.fetch_one(query)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return Schedule(**dict(schedule))

@router.put("/{schedule_id}", response_model=Schedule)
async def update_schedule(
    schedule_id: UUID,
    schedule_update: ScheduleUpdate,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant)
):
    """Update a schedule."""
    # Check if schedule exists
    existing_schedule = await database.fetch_one(
        schedules_table.select().where(
            schedules_table.c.id == schedule_id,
            schedules_table.c.tenant_id == tenant_id
        )
    )

    if not existing_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    update_data = schedule_update.dict(exclude_unset=True)

    # Validate cron expression if provided
    if "cron_expression" in update_data:
        timezone = update_data.get("timezone", existing_schedule["timezone"])
        try:
            next_run = cron_service.get_next_run_time(update_data["cron_expression"], timezone)
            update_data["next_run_at"] = next_run
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid cron expression: {str(e)}")

    # Update schedule
    query = schedules_table.update().where(
        schedules_table.c.id == schedule_id,
        schedules_table.c.tenant_id == tenant_id
    ).values(**update_data)

    await database.execute(query)

    # Re-register schedule with scheduler service
    background_tasks.add_task(
        _register_schedule_with_scheduler,
        schedule_id
    )

    # Fetch and return updated schedule
    updated_schedule = await database.fetch_one(
        schedules_table.select().where(schedules_table.c.id == schedule_id)
    )

    return Schedule(**dict(updated_schedule))

@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: UUID,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant)
):
    """Delete a schedule."""
    # Check if schedule exists
    existing_schedule = await database.fetch_one(
        schedules_table.select().where(
            schedules_table.c.id == schedule_id,
            schedules_table.c.tenant_id == tenant_id
        )
    )

    if not existing_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Unregister from scheduler service
    background_tasks.add_task(
        _unregister_schedule_from_scheduler,
        schedule_id
    )

    # Delete schedule
    query = schedules_table.delete().where(
        schedules_table.c.id == schedule_id,
        schedules_table.c.tenant_id == tenant_id
    )

    await database.execute(query)

    return {"message": "Schedule deleted successfully"}

@router.post("/{schedule_id}/toggle", response_model=Schedule)
async def toggle_schedule(
    schedule_id: UUID,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant)
):
    """Toggle schedule active status."""
    # Get current schedule
    schedule = await database.fetch_one(
        schedules_table.select().where(
            schedules_table.c.id == schedule_id,
            schedules_table.c.tenant_id == tenant_id
        )
    )

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Toggle active status
    new_status = not schedule["is_active"]

    query = schedules_table.update().where(
        schedules_table.c.id == schedule_id,
        schedules_table.c.tenant_id == tenant_id
    ).values(is_active=new_status)

    await database.execute(query)

    # Update scheduler registration
    if new_status:
        background_tasks.add_task(_register_schedule_with_scheduler, schedule_id)
    else:
        background_tasks.add_task(_unregister_schedule_from_scheduler, schedule_id)

    # Return updated schedule
    updated_schedule = await database.fetch_one(
        schedules_table.select().where(schedules_table.c.id == schedule_id)
    )

    return Schedule(**dict(updated_schedule))

@router.post("/{schedule_id}/run-now")
async def run_schedule_now(
    schedule_id: UUID,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant)
):
    """Manually trigger a schedule to run immediately."""
    # Check if schedule exists
    schedule = await database.fetch_one(
        schedules_table.select().where(
            schedules_table.c.id == schedule_id,
            schedules_table.c.tenant_id == tenant_id
        )
    )

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Trigger export
    background_tasks.add_task(
        _execute_scheduled_export,
        schedule_id,
        manual=True
    )

    return {"message": "Schedule execution triggered"}

@router.post("/test-cron", response_model=ScheduleTestResponse)
async def test_cron_expression(
    cron_expression: str,
    timezone: str = "UTC",
    count: int = Query(5, ge=1, le=10)
):
    """Test a cron expression and return next run times."""
    try:
        next_runs = cron_service.get_next_run_times(cron_expression, timezone, count)

        return ScheduleTestResponse(
            is_valid=True,
            next_runs=next_runs
        )
    except Exception as e:
        return ScheduleTestResponse(
            is_valid=False,
            next_runs=[],
            error_message=str(e)
        )

# Background task functions
async def _register_schedule_with_scheduler(schedule_id: UUID):
    """Register a schedule with the scheduler service."""
    # This would interact with the SchedulerService
    # For now, just log the action
    import structlog
    logger = structlog.get_logger()
    logger.info("Registering schedule with scheduler", schedule_id=str(schedule_id))

async def _unregister_schedule_from_scheduler(schedule_id: UUID):
    """Unregister a schedule from the scheduler service."""
    import structlog
    logger = structlog.get_logger()
    logger.info("Unregistering schedule from scheduler", schedule_id=str(schedule_id))

async def _execute_scheduled_export(schedule_id: UUID, manual: bool = False):
    """Execute a scheduled export."""
    import structlog
    logger = structlog.get_logger()
    logger.info("Executing scheduled export", schedule_id=str(schedule_id), manual=manual)
