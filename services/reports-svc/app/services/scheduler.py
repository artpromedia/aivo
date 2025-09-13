"""Scheduler service for managing scheduled report exports."""

import asyncio
from datetime import datetime, timedelta
import structlog
from typing import Dict, List, Optional
import uuid
from uuid import UUID

from ..database import database, schedules_table, exports_table
from .cron_service import CronService

logger = structlog.get_logger()

class SchedulerService:
    """Service for managing scheduled report exports."""

    def __init__(self):
        self.cron_service = CronService()
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.schedules: Dict[UUID, dict] = {}

    async def start(self):
        """Start the scheduler service."""
        if self.running:
            return

        self.running = True
        logger.info("Starting scheduler service")

        # Load existing schedules
        await self._load_schedules()

        # Start the scheduler loop
        self.task = asyncio.create_task(self._scheduler_loop())

        logger.info("Scheduler service started")

    async def stop(self):
        """Stop the scheduler service."""
        if not self.running:
            return

        logger.info("Stopping scheduler service")
        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Scheduler service stopped")

    async def register_schedule(self, schedule_id: UUID):
        """Register a new schedule or update existing one."""
        try:
            # Fetch schedule from database
            schedule = await database.fetch_one(
                schedules_table.select().where(
                    schedules_table.c.id == schedule_id,
                    schedules_table.c.is_active == True
                )
            )

            if schedule:
                self.schedules[schedule_id] = dict(schedule)
                logger.info("Registered schedule", schedule_id=str(schedule_id))
            else:
                # Remove from schedules if it exists but is not active
                if schedule_id in self.schedules:
                    del self.schedules[schedule_id]
                    logger.info("Unregistered inactive schedule", schedule_id=str(schedule_id))

        except Exception as e:
            logger.error("Failed to register schedule", schedule_id=str(schedule_id), error=str(e))

    async def unregister_schedule(self, schedule_id: UUID):
        """Unregister a schedule."""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            logger.info("Unregistered schedule", schedule_id=str(schedule_id))

    async def _load_schedules(self):
        """Load all active schedules from database."""
        try:
            schedules = await database.fetch_all(
                schedules_table.select().where(schedules_table.c.is_active == True)
            )

            for schedule in schedules:
                self.schedules[schedule["id"]] = dict(schedule)

            logger.info("Loaded schedules", count=len(self.schedules))

        except Exception as e:
            logger.error("Failed to load schedules", error=str(e))

    async def _scheduler_loop(self):
        """Main scheduler loop that checks for due schedules."""
        while self.running:
            try:
                await self._check_due_schedules()

                # Sleep for 1 minute before next check
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in scheduler loop", error=str(e))
                await asyncio.sleep(60)  # Wait before retrying

    async def _check_due_schedules(self):
        """Check for schedules that are due to run."""
        now = datetime.utcnow()

        for schedule_id, schedule in list(self.schedules.items()):
            try:
                # Check if schedule is due
                if schedule["next_run_at"] and schedule["next_run_at"] <= now:
                    logger.info("Schedule is due", schedule_id=str(schedule_id))

                    # Execute the schedule
                    await self._execute_schedule(schedule_id, schedule)

                    # Calculate next run time
                    await self._update_next_run_time(schedule_id, schedule)

            except Exception as e:
                logger.error("Error processing schedule", schedule_id=str(schedule_id), error=str(e))

    async def _execute_schedule(self, schedule_id: UUID, schedule: dict):
        """Execute a scheduled report export."""
        try:
            # Create export record
            export_data = {
                "id": uuid.uuid4(),
                "report_id": schedule["report_id"],
                "schedule_id": schedule_id,
                "tenant_id": schedule["tenant_id"],
                "initiated_by": f"scheduler:{schedule['created_by']}",
                "format": schedule["format"],
                "status": "pending"
            }

            # Insert export record
            await database.execute(
                exports_table.insert().values(**export_data)
            )

            # Update schedule run statistics
            await database.execute(
                schedules_table.update().where(
                    schedules_table.c.id == schedule_id
                ).values(
                    last_run_at=datetime.utcnow(),
                    run_count=schedules_table.c.run_count + 1
                )
            )

            # Process export in background (this would trigger the export processing)
            asyncio.create_task(self._process_scheduled_export(export_data["id"]))

            logger.info("Scheduled export created",
                       schedule_id=str(schedule_id),
                       export_id=str(export_data["id"]))

        except Exception as e:
            logger.error("Failed to execute schedule", schedule_id=str(schedule_id), error=str(e))

    async def _update_next_run_time(self, schedule_id: UUID, schedule: dict):
        """Update the next run time for a schedule."""
        try:
            next_run = self.cron_service.get_next_run_time(
                schedule["cron_expression"],
                schedule["timezone"]
            )

            # Update database
            await database.execute(
                schedules_table.update().where(
                    schedules_table.c.id == schedule_id
                ).values(next_run_at=next_run)
            )

            # Update in-memory schedule
            self.schedules[schedule_id]["next_run_at"] = next_run

        except Exception as e:
            logger.error("Failed to update next run time", schedule_id=str(schedule_id), error=str(e))

    async def _process_scheduled_export(self, export_id: UUID):
        """Process a scheduled export (placeholder for now)."""
        # This would be similar to the _process_export function in exports.py
        # For now, just log that we would process it
        logger.info("Processing scheduled export", export_id=str(export_id))

        # Update status to processing
        await database.execute(
            exports_table.update().where(
                exports_table.c.id == export_id
            ).values(status="processing")
        )

        # Simulate processing time
        await asyncio.sleep(5)

        # For demo, mark as completed
        await database.execute(
            exports_table.update().where(
                exports_table.c.id == export_id
            ).values(
                status="completed",
                completed_at=datetime.utcnow(),
                execution_time_ms=5000
            )
        )

        logger.info("Scheduled export completed", export_id=str(export_id))

    def get_schedule_status(self) -> dict:
        """Get status information about the scheduler."""
        return {
            "running": self.running,
            "active_schedules": len(self.schedules),
            "schedules": [
                {
                    "id": str(schedule_id),
                    "name": schedule.get("name"),
                    "next_run_at": schedule.get("next_run_at").isoformat() if schedule.get("next_run_at") else None,
                    "last_run_at": schedule.get("last_run_at").isoformat() if schedule.get("last_run_at") else None,
                    "run_count": schedule.get("run_count", 0)
                }
                for schedule_id, schedule in self.schedules.items()
            ]
        }
