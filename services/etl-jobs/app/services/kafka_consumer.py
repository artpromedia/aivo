"""Kafka consumer service for ingesting events from Redpanda."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from app.config import settings
from app.models import RawEvent

logger = structlog.get_logger(__name__)


class KafkaEventConsumer:
    """Kafka consumer for processing events from Redpanda."""

    def __init__(self, event_handler) -> None:
        """Initialize the Kafka consumer.
        
        Args:
            event_handler: Callable that processes batches of events
        """
        self.consumer: AIOKafkaConsumer | None = None
        self.event_handler = event_handler
        self._running = False
        self._consume_task: asyncio.Task | None = None
        
        # Metrics
        self._metrics = {
            "messages_consumed": 0,
            "events_processed": 0,
            "processing_errors": 0,
            "last_processed_time": None,
        }

    async def start(self) -> None:
        """Start the Kafka consumer."""
        logger.info("Starting Kafka consumer", topic=settings.kafka_topic_events_raw)
        
        try:
            self.consumer = AIOKafkaConsumer(
                settings.kafka_topic_events_raw,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=settings.kafka_consumer_group,
                auto_offset_reset=settings.kafka_auto_offset_reset,
                enable_auto_commit=False,  # Manual commit for reliability
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None,
                max_poll_records=settings.batch_size,
                max_poll_interval_ms=30000,  # 30 seconds
            )
            
            await self.consumer.start()
            self._running = True
            
            # Start consuming in background
            self._consume_task = asyncio.create_task(self._consume_loop())
            
            logger.info("Kafka consumer started successfully")
            
        except Exception as e:
            logger.error("Failed to start Kafka consumer", error=str(e))
            raise

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        logger.info("Stopping Kafka consumer")
        
        self._running = False
        
        if self._consume_task:
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass
        
        if self.consumer:
            await self.consumer.stop()
        
        logger.info("Kafka consumer stopped")

    async def _consume_loop(self) -> None:
        """Main consumption loop."""
        logger.info("Starting consumption loop")
        
        while self._running:
            try:
                # Poll for messages
                msg_pack = await self.consumer.getmany(
                    timeout_ms=1000,
                    max_records=settings.batch_size
                )
                
                if not msg_pack:
                    continue
                
                # Process messages by topic partition
                for topic_partition, messages in msg_pack.items():
                    if messages:
                        await self._process_messages(topic_partition, messages)
                        
            except Exception as e:
                logger.error(
                    "Error in consume loop",
                    error=str(e),
                    error_type=type(e).__name__
                )
                self._metrics["processing_errors"] += 1
                
                # Brief pause before retrying
                await asyncio.sleep(1)

    async def _process_messages(self, topic_partition, messages) -> None:
        """Process a batch of messages from a topic partition."""
        logger.debug(
            "Processing message batch",
            partition=topic_partition.partition,
            message_count=len(messages)
        )
        
        try:
            # Convert messages to RawEvent objects
            events = []
            valid_messages = []
            
            for message in messages:
                try:
                    # Create RawEvent from message
                    event_data = message.value
                    
                    # Add ETL metadata
                    event_data["processed_at"] = datetime.now(timezone.utc)
                    event_data["partition_date"] = datetime.fromisoformat(
                        event_data["timestamp"]
                    ).strftime("%Y-%m-%d")
                    
                    event = RawEvent(**event_data)
                    events.append(event)
                    valid_messages.append(message)
                    
                except Exception as e:
                    logger.warning(
                        "Failed to parse event",
                        error=str(e),
                        message_offset=message.offset,
                        partition=topic_partition.partition
                    )
                    continue
            
            if events:
                # Process events through handler
                success = await self.event_handler(events)
                
                if success:
                    # Commit offsets for successfully processed messages
                    if valid_messages:
                        last_message = valid_messages[-1]
                        await self.consumer.commit({
                            topic_partition: last_message.offset + 1
                        })
                    
                    # Update metrics
                    self._metrics["messages_consumed"] += len(valid_messages)
                    self._metrics["events_processed"] += len(events)
                    self._metrics["last_processed_time"] = datetime.now(timezone.utc)
                    
                    logger.info(
                        "Processed message batch successfully",
                        events_count=len(events),
                        partition=topic_partition.partition,
                        last_offset=valid_messages[-1].offset if valid_messages else None
                    )
                else:
                    logger.error(
                        "Failed to process event batch",
                        events_count=len(events),
                        partition=topic_partition.partition
                    )
                    self._metrics["processing_errors"] += 1
                    
        except Exception as e:
            logger.error(
                "Error processing message batch",
                error=str(e),
                partition=topic_partition.partition,
                message_count=len(messages)
            )
            self._metrics["processing_errors"] += 1

    def get_metrics(self) -> dict[str, Any]:
        """Get consumer metrics."""
        return self._metrics.copy()

    async def health_check(self) -> dict[str, Any]:
        """Check consumer health."""
        health = {
            "status": "healthy" if self._running else "unhealthy",
            "consumer_running": self._running,
            "metrics": self.get_metrics(),
        }
        
        if self.consumer:
            try:
                # Check if we can get metadata (indicates connection)
                metadata = await self.consumer.client.fetch_metadata()
                health["kafka_connected"] = True
                health["available_topics"] = len(metadata.topics)
            except Exception as e:
                health["kafka_connected"] = False
                health["kafka_error"] = str(e)
        else:
            health["kafka_connected"] = False
            
        return health
