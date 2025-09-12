"""Main ETL processor orchestrating the pipeline."""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Any

import structlog

from app.config import settings
from app.models import RawEvent
from app.services.etl_scheduler import ETLScheduler
from app.services.kafka_consumer import KafkaEventConsumer
from app.services.s3_writer import S3ParquetWriter

logger = structlog.get_logger(__name__)


class ETLProcessor:
    """Main ETL processor coordinating Kafka → S3 → Snowflake pipeline."""

    def __init__(self) -> None:
        """Initialize the ETL processor."""
        self.s3_writer = S3ParquetWriter()
        self.kafka_consumer = KafkaEventConsumer(self._process_event_batch)
        self.etl_scheduler = ETLScheduler()
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Setup signal handlers
        self._setup_signal_handlers()

        # Metrics
        self._metrics = {
            "batches_processed": 0,
            "events_processed": 0,
            "s3_files_written": 0,
            "processing_errors": 0,
            "start_time": None,
        }

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            for sig in [signal.SIGTERM, signal.SIGINT]:
                signal.signal(sig, self._signal_handler)

    def _signal_handler(
        self,
        signum: int,
        _frame: object,  # pylint: disable=unused-argument
    ) -> None:
        """Handle shutdown signals."""
        logger.info("Received shutdown signal", signal=signum)
        self._shutdown_event.set()

    async def start(self) -> None:
        """Start the ETL processor."""
        logger.info("Starting ETL processor")

        try:
            self._running = True
            self._metrics["start_time"] = datetime.now()

            # Start services
            await self.kafka_consumer.start()
            await self.etl_scheduler.start()

            logger.info("ETL processor started successfully")

            # Wait for shutdown signal
            await self._shutdown_event.wait()

        except Exception as e:
            logger.error("Failed to start ETL processor", error=str(e))
            raise
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the ETL processor."""
        logger.info("Stopping ETL processor")

        self._running = False

        # Stop services
        if self.kafka_consumer:
            await self.kafka_consumer.stop()

        if self.etl_scheduler:
            await self.etl_scheduler.stop()

        logger.info("ETL processor stopped")

    async def _process_event_batch(self, events: list[RawEvent]) -> bool:
        """Process a batch of events from Kafka.

        Args:
            events: List of events to process

        Returns:
            True if processing succeeded, False otherwise
        """
        if not events:
            return True

        try:
            logger.info(
                "Processing event batch",
                event_count=len(events),
                first_event_time=events[0].timestamp.isoformat(),
                last_event_time=events[-1].timestamp.isoformat(),
            )

            # Write events to S3 as Parquet
            s3_key = await self.s3_writer.write_events_to_s3(events)

            if s3_key:
                # Update metrics
                self._metrics["batches_processed"] += 1
                self._metrics["events_processed"] += len(events)
                self._metrics["s3_files_written"] += 1

                logger.info(
                    "Successfully processed event batch",
                    event_count=len(events),
                    s3_key=s3_key,
                )
                return True

            logger.error("Failed to write events to S3", event_count=len(events))
            self._metrics["processing_errors"] += 1
            return False

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Error processing event batch",
                error=str(e),
                event_count=len(events),
            )
            self._metrics["processing_errors"] += 1
            return False

    async def health_check(self) -> dict[str, Any]:
        """Get health status of the ETL processor."""
        health = {
            "status": "healthy" if self._running else "unhealthy",
            "running": self._running,
            "metrics": self._metrics.copy(),
            "uptime_seconds": (
                (datetime.now() - self._metrics["start_time"]).total_seconds()
                if self._metrics["start_time"]
                else 0
            ),
        }

        # Check component health
        kafka_health = await self.kafka_consumer.health_check()
        s3_health = await self.s3_writer.health_check()
        scheduler_health = await self.etl_scheduler.health_check()

        health["components"] = {
            "kafka_consumer": kafka_health,
            "s3_writer": s3_health,
            "etl_scheduler": scheduler_health,
        }

        # Overall health depends on all components
        if (
            not kafka_health.get("kafka_connected")
            or not s3_health.get("s3_connected")
            or not scheduler_health.get("running")
        ):
            health["status"] = "unhealthy"

        return health

    def get_metrics(self) -> dict[str, Any]:
        """Get processor metrics."""
        return self._metrics.copy()


async def main() -> None:
    """Main entry point."""
    # Configure logging
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logger.info(
        "Starting Aivo ETL Jobs Service",
        version=settings.version,
        config={
            "kafka_topic": settings.kafka_topic_events_raw,
            "s3_bucket": settings.s3_bucket_raw_events,
            "snowflake_database": settings.snowflake_database,
            "batch_size": settings.batch_size,
            "flush_interval": settings.flush_interval_seconds,
        },
    )

    processor = ETLProcessor()

    try:
        await processor.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("ETL processor failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
