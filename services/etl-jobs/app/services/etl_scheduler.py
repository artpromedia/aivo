"""ETL transformation scheduler for running daily analytics jobs."""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any

import structlog

# pylint: disable=import-error,no-name-in-module
from app.services.snowflake_etl import SnowflakeETLService  # type: ignore

logger = structlog.get_logger(__name__)


class ETLScheduler:
    """Scheduler for ETL transformation jobs."""

    def __init__(self) -> None:
        """Initialize ETL scheduler."""
        self.snowflake_service = SnowflakeETLService()
        self._running = False
        self._scheduler_task: asyncio.Task | None = None

        # Metrics
        self._metrics = {
            "jobs_scheduled": 0,
            "jobs_completed": 0,
            "jobs_failed": 0,
            "last_run_time": None,
        }

    async def start(self) -> None:
        """Start the ETL scheduler."""
        logger.info("Starting ETL scheduler")

        try:
            # Connect to Snowflake
            await self.snowflake_service.connect()

            self._running = True

            # Start scheduler task
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())

            logger.info("ETL scheduler started successfully")

        except Exception as e:
            logger.error("Failed to start ETL scheduler", error=str(e))
            raise

    async def stop(self) -> None:
        """Stop the ETL scheduler."""
        logger.info("Stopping ETL scheduler")

        self._running = False

        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        # Disconnect from Snowflake
        await self.snowflake_service.disconnect()

        logger.info("ETL scheduler stopped")

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        logger.info("Starting ETL scheduler loop")

        while self._running:
            try:
                # Check if it's time to run daily jobs (4 AM UTC)
                now = datetime.utcnow()
                if (
                    now.hour == 4
                    and now.minute < 5
                    and (
                        self._metrics["last_run_time"] is None
                        or self._metrics["last_run_time"].date() < now.date()
                    )
                ):
                    await self._run_daily_jobs()

                # Sleep for 5 minutes before next check
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "Error in scheduler loop",
                    error=str(e),
                    error_type=type(e).__name__
                )
                # Brief pause before retrying
                await asyncio.sleep(60)

    async def _run_daily_jobs(self) -> None:
        """Run daily transformation jobs."""
        target_date = (datetime.utcnow() - timedelta(days=1)).date()

        logger.info("Running daily ETL jobs", target_date=target_date)

        try:
            self._metrics["jobs_scheduled"] += 1

            # Run transformations
            results = await self.snowflake_service.run_daily_transformations(
                target_date
            )

            # Run data quality validation
            validation_results = (
                await self.snowflake_service.validate_data_quality(target_date)
            )

            # Check if all validations passed
            all_passed = all(validation_results.values())

            if all_passed:
                self._metrics["jobs_completed"] += 1
                logger.info(
                    "Daily ETL jobs completed successfully",
                    target_date=target_date,
                    results=results,
                    validation=validation_results,
                )
            else:
                self._metrics["jobs_failed"] += 1
                logger.warning(
                    "Daily ETL jobs completed with validation failures",
                    target_date=target_date,
                    results=results,
                    validation=validation_results,
                )

            self._metrics["last_run_time"] = datetime.utcnow()

        except Exception as e:  # pylint: disable=broad-exception-caught
            self._metrics["jobs_failed"] += 1
            logger.error(
                "Daily ETL jobs failed", target_date=target_date, error=str(e)
            )

    async def run_manual_job(
        self, target_date: date | None = None
    ) -> dict[str, Any]:
        """Run ETL jobs manually for a specific date."""
        if target_date is None:
            target_date = (datetime.utcnow() - timedelta(days=1)).date()

        logger.info("Running manual ETL job", target_date=target_date)

        try:
            # Ensure Snowflake connection
            if not self.snowflake_service.is_connected():
                await self.snowflake_service.connect()

            # Run transformations
            results = await self.snowflake_service.run_daily_transformations(
                target_date
            )

            # Run validation
            validation_results = (
                await self.snowflake_service.validate_data_quality(target_date)
            )

            return {
                "status": "success",
                "target_date": target_date.isoformat(),
                "transformations": results,
                "validation": validation_results,
                "all_checks_passed": all(validation_results.values()),
            }

        except (ConnectionError, RuntimeError, ValueError) as e:
            logger.error(
                "Manual ETL job failed", target_date=target_date, error=str(e)
            )
            return {
                "status": "failed",
                "target_date": target_date.isoformat(),
                "error": str(e)
            }

    async def backfill_data(
        self, start_date: date, end_date: date
    ) -> dict[str, Any]:
        """Backfill data for a date range."""
        logger.info(
            "Starting data backfill", start_date=start_date, end_date=end_date
        )

        if not self.snowflake_service.is_connected():
            await self.snowflake_service.connect()

        results = []
        current_date = start_date

        while current_date <= end_date:
            try:
                logger.info("Processing backfill date", date=current_date)

                # Run transformations for this date
                day_results = (
                    await self.snowflake_service.run_daily_transformations(
                        current_date
                    )
                )

                results.append({
                    "date": current_date.isoformat(),
                    "status": "success",
                    "results": day_results
                })

                logger.info(
                    "Backfill date completed",
                    date=current_date,
                    results=day_results
                )

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "Backfill failed for date", date=current_date, error=str(e)
                )
                results.append({
                    "date": current_date.isoformat(),
                    "status": "failed",
                    "error": str(e)
                })

            current_date += timedelta(days=1)

        logger.info(
            "Data backfill completed",
            start_date=start_date,
            end_date=end_date,
            total_days=len(results),
            successful_days=len(
                [r for r in results if r["status"] == "success"]
            ),
        )

        return {
            "status": "completed",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "results": results,
        }

    async def health_check(self) -> dict[str, Any]:
        """Check scheduler and Snowflake service health."""
        health = {
            "status": "healthy" if self._running else "unhealthy",
            "running": self._running,
            "metrics": self._metrics.copy(),
        }

        # Check Snowflake service health
        try:
            sf_health = await self.snowflake_service.health_check()
            health["snowflake"] = sf_health

            # Check Snowpipe status
            pipe_status = await self.snowflake_service.check_snowpipe_status()
            health["snowpipe"] = pipe_status

            # Overall health depends on Snowflake connectivity
            if (not sf_health.get("connected") or
                    not pipe_status.get("healthy")):
                health["status"] = "unhealthy"

        except Exception as e:  # pylint: disable=broad-exception-caught
            health["snowflake"] = {"error": str(e)}
            health["status"] = "unhealthy"

        return health

    def get_metrics(self) -> dict[str, Any]:
        """Get scheduler metrics."""
        return self._metrics.copy()
