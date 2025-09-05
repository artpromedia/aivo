"""Event processing service that coordinates buffer and Kafka publishing."""

import asyncio
import uuid
from datetime import datetime
from typing import Any

import structlog

from app.config import settings
from app.models import LearnerEvent
from app.services.buffer_service import EventBuffer
from app.services.kafka_service import KafkaProducerService

logger = structlog.get_logger(__name__)


class EventProcessor:
    """Coordinates event buffering and Kafka publishing."""

    def __init__(self) -> None:
        """Initialize event processor."""
        self.buffer = EventBuffer()
        self.kafka = KafkaProducerService()
        self._running = False
        self._processing_task: asyncio.Task | None = None
        self._metrics = {
            "batches_processed_total": 0,
            "events_processed_total": 0,
            "processing_errors_total": 0,
            "last_processing_time": None,
            "average_processing_duration": 0.0,
        }

    async def start(self) -> None:
        """Start the event processor."""
        logger.info("Starting event processor")
        
        try:
            # Start dependencies
            await self.buffer.start()
            await self.kafka.start()
            
            # Start background processing
            self._running = True
            self._processing_task = asyncio
                .create_task(self._process_events_loop())
            
            logger.info("Event processor started successfully")
            
        except Exception as e:
            logger.error("Failed to start event processor", error=str(e))
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the event processor."""
        logger.info("Stopping event processor")
        
        self._running = False
        
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        try:
            await self.kafka.stop()
        except Exception as e:
            logger.error("Error stopping Kafka service", error=str(e))
        
        logger.info("Event processor stopped")

    async def collect_events(
        self,
        events: list[LearnerEvent]
    ) -> dict[str, Any]:
        """Collect and buffer events."""
        start_time = datetime.utcnow()
        
        try:
            # Validate events
            validated_events = []
            validation_errors = []
            
            for event in events:
                try:
                    # Additional validation if needed
                    if not event.learner_id or not event.event_id:
                        validation_errors.append(
                            f"Event {event.event_id}: missing required fields"
                        )
                        continue
                    
                    validated_events.append(event)
                    
                except Exception as e:
                    validation_errors.append(
                        f"Event validation error: {str(e)}"
                    )
            
            if not validated_events:
                return {
                    "accepted": 0,
                    "rejected": len(events),
                    "batch_id": None,
                    "message": "No valid events in batch",
                    "errors": validation_errors,
                }
            
            # Add to buffer
            batch_id = str(uuid.uuid4())
            success = await self.buffer.add_events(validated_events)
            
            if not success:
                return {
                    "accepted": 0,
                    "rejected": len(events),
                    "batch_id": batch_id,
                    "message": "Failed to buffer events",
                    "errors": ["Buffer write failed"],
                }
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                "Events collected successfully",
                batch_id=batch_id,
                accepted=len(validated_events),
                rejected=len(events) - len(validated_events),
                processing_time=processing_time,
            )
            
            return {
                "accepted": len(validated_events),
                "rejected": len(events) - len(validated_events),
                "batch_id": batch_id,
                "message": "Events buffered successfully",
                "errors": validation_errors,
            }
            
        except Exception as e:
            logger.error("Error collecting events", error=str(e))
            return {
                "accepted": 0,
                "rejected": len(events),
                "batch_id": None,
                "message": f"Collection failed: {str(e)}",
                "errors": [str(e)],
            }

    async def _process_events_loop(self) -> None:
        """Background loop to process buffered events."""
        logger.info("Starting event processing loop")
        
        while self._running:
            try:
                await self._process_buffer_batches()
                await asyncio.sleep(settings.buffer_flush_interval_seconds)
                
            except asyncio.CancelledError:
                logger.info("Event processing loop cancelled")
                break
                
            except Exception as e:
                logger.error("Error in event processing loop", error=str(e))
                self._metrics["processing_errors_total"] += 1
                await asyncio.sleep(5)  # Brief pause before retry

    async def _process_buffer_batches(self) -> None:
        """Process batches from buffer to Kafka."""
        if not self.kafka.is_connected():
            logger.warning("Kafka not connected, skipping batch processing")
            return
        
        try:
            # Get batches from buffer
            batches = await self.buffer.get_batches(
                max_batches=settings.buffer_batch_size
            )
            
            if not batches:
                return
            
            logger.debug(f"Processing {len(batches)} batches from buffer")
            
            for batch in batches:
                start_time = datetime.utcnow()
                
                try:
                    # Parse events from batch
                    events = [
                        LearnerEvent(**event_data)
                        for event_data in batch.get("events", [])
                    ]
                    
                    if not events:
                        # Remove empty batch
                        await self.buffer.remove_batch(
                            batch["file_path"], 
                            batch["batch_id"]
                        )
                        continue
                    
                    # Publish to Kafka
                    successful, failed = await self.kafka.publish_events(
                        events, 
                        batch["batch_id"]
                    )
                    
                    if successful > 0 and failed == 0:
                        # Remove successfully processed batch
                        await self.buffer.remove_batch(
                            batch["file_path"], 
                            batch["batch_id"]
                        )
                        
                        # Update metrics
                        self._metrics["batches_processed_total"] += 1
                        self._metrics["events_processed_total"] += successful
                        
                        processing_time = (
                            datetime.utcnow() - start_time
                        ).total_seconds()
                        
                        # Update average processing time
                        if self._metrics["average_processing_duration"] == 0:
                            self._metrics["average_processing_duration"] = processing_time
                        else:
                            self._metrics["average_processing_duration"] = (
                                self._metrics["average_processing_duration"] * 0.9 +
                                processing_time * 0.1
                            )
                        
                        self._metrics["last_processing_time"] = datetime
                            .utcnow()
                            .isoformat()
                        
                        logger.debug(
                            "Batch processed successfully",
                            batch_id=batch["batch_id"],
                            events=successful,
                            processing_time=processing_time,
                        )
                    
                    elif failed > 0:
                        logger.warning(
                            "Batch partially failed",
                            batch_id=batch["batch_id"],
                            successful=successful,
                            failed=failed,
                        )
                        
                        # Keep batch for retry or manual intervention
                        self._metrics["processing_errors_total"] += 1
                    
                except Exception as e:
                    logger.error(
                        "Error processing batch",
                        batch_id=batch.get("batch_id"),
                        error=str(e),
                    )
                    self._metrics["processing_errors_total"] += 1
                    
        except Exception as e:
            logger.error("Error in batch processing", error=str(e))
            self._metrics["processing_errors_total"] += 1

    async def health_check(self) -> dict[str, Any]:
        """Get health status of event processor."""
        try:
            # Get component health
            kafka_health = await self.kafka.health_check()
            buffer_stats = await self.buffer.get_stats()
            
            # Determine overall health
            kafka_healthy = kafka_health
                .get("kafka", {})
                .get("status") == "healthy"
            processor_healthy = self._running and
                self._processing_task and
                and not self
                ._processing_task
                .done()
            
            overall_status = (
                "healthy" if kafka_healthy and
                    processor_healthy else "unhealthy"
            )
            
            return {
                "status": overall_status,
                "processor": {
                    "running": self._running,
                    "task_healthy": processor_healthy,
                    "metrics": self._metrics,
                },
                "buffer": {
                    "total_events": buffer_stats.total_events,
                    "size_bytes": buffer_stats.size_bytes,
                    "files_count": buffer_stats.files_count,
                    "oldest_event": buffer_stats
                        .oldest_event
                        .isoformat() if buffer_stats.oldest_event else None,
                    "newest_event": buffer_stats
                        .newest_event
                        .isoformat() if buffer_stats.newest_event else None,
                },
                **kafka_health,
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    async def get_metrics(self) -> dict[str, Any]:
        """Get comprehensive metrics."""
        try:
            kafka_metrics = await self.kafka.get_metrics()
            buffer_stats = await self.buffer.get_stats()
            
            return {
                "processor": self._metrics,
                "kafka": kafka_metrics,
                "buffer": {
                    "total_events": buffer_stats.total_events,
                    "size_bytes": buffer_stats.size_bytes,
                    "files_count": buffer_stats.files_count,
                },
            }
            
        except Exception as e:
            logger.error("Error getting metrics", error=str(e))
            return {"error": str(e)}

    def is_ready(self) -> bool:
        """Check if processor is ready to accept events."""
        return (
            self._running and
            self.kafka.is_connected() and
            self._processing_task and 
            not self._processing_task.done()
        )
