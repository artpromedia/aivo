"""Kafka/Redpanda producer service with DLQ support."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any

import structlog
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError, KafkaTimeoutError

from app.config import settings
from app.models import LearnerEvent

logger = structlog.get_logger(__name__)


class KafkaProducerService:
    """Kafka producer with DLQ and retry logic."""

    def __init__(self) -> None:
        """Initialize Kafka producer service."""
        self.producer: AIOKafkaProducer | None = None
        self.dlq_producer: AIOKafkaProducer | None = None
        self._connected = False
        self._metrics = {
            "events_published_total": 0,
            "events_dlq_total": 0,
            "kafka_errors_total": 0,
            "retry_attempts_total": 0,
        }

    async def start(self) -> None:
        """Start the Kafka producer."""
        logger.info("Starting Kafka producer service")
        
        try:
            # Main producer for events
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                client_id=f"{settings.kafka_client_id}-main",
                compression_type=settings.kafka_compression_type,
                batch_size=settings.kafka_batch_size,
                linger_ms=settings.kafka_linger_ms,
                max_retries=settings.kafka_max_retries,
                retry_backoff_ms=settings.kafka_retry_backoff_ms,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
            )
            
            # DLQ producer
            self.dlq_producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                client_id=f"{settings.kafka_client_id}-dlq",
                compression_type=settings.kafka_compression_type,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
            )
            
            # Start producers
            await self.producer.start()
            await self.dlq_producer.start()
            
            self._connected = True
            logger.info("Kafka producer started successfully")
            
        except Exception as e:
            logger.error("Failed to start Kafka producer", error=str(e))
            self._connected = False
            raise

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        logger.info("Stopping Kafka producer service")
        
        try:
            if self.producer:
                await self.producer.stop()
            if self.dlq_producer:
                await self.dlq_producer.stop()
            
            self._connected = False
            logger.info("Kafka producer stopped")
            
        except Exception as e:
            logger.error("Error stopping Kafka producer", error=str(e))

    async def publish_events(
        self, 
        events: list[LearnerEvent], 
        batch_id: str | None = None
    ) -> tuple[int, int]:
        """
        Publish events to Kafka.
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not self.producer or not self._connected:
            raise RuntimeError("Kafka producer not connected")
        
        successful = 0
        failed = 0
        
        for event in events:
            try:
                # Use learner_id as partition key for ordering
                key = event.learner_id
                
                # Prepare event payload
                payload = {
                    "event": event.dict(),
                    "batch_id": batch_id or str(uuid.uuid4()),
                    "published_at": datetime.utcnow().isoformat(),
                    "producer_id": settings.kafka_client_id,
                }
                
                # Send to main topic
                await self._send_with_retry(
                    topic=settings.kafka_topic_events_raw,
                    key=key,
                    value=payload,
                    event_id=event.event_id,
                )
                
                successful += 1
                self._metrics["events_published_total"] += 1
                
            except Exception as e:
                logger.error(
                    "Failed to publish event",
                    event_id=event.event_id,
                    learner_id=event.learner_id,
                    error=str(e),
                )
                
                # Send to DLQ
                await self._send_to_dlq(event, str(e), batch_id)
                failed += 1
        
        logger.info(
            "Published events to Kafka",
            batch_id=batch_id,
            successful=successful,
            failed=failed,
        )
        
        return successful, failed

    async def _send_with_retry(
        self,
        topic: str,
        key: str,
        value: dict[str, Any],
        event_id: str,
        max_retries: int | None = None,
    ) -> None:
        """Send message with retry logic."""
        max_retries = max_retries or settings.kafka_max_retries
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Send message
                future = await self.producer.send(topic, value=value, key=key)
                record_metadata = await future
                
                logger.debug(
                    "Event published successfully",
                    event_id=event_id,
                    topic=topic,
                    partition=record_metadata.partition,
                    offset=record_metadata.offset,
                    attempt=attempt + 1,
                )
                
                return
                
            except (KafkaTimeoutError, KafkaError) as e:
                last_error = e
                self._metrics["kafka_errors_total"] += 1
                
                if attempt < max_retries:
                    self._metrics["retry_attempts_total"] += 1
                    retry_delay = settings.kafka_retry_backoff_ms * (2 ** attempt) / 1000
                    
                    logger.warning(
                        "Kafka send failed, retrying",
                        event_id=event_id,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        retry_delay=retry_delay,
                        error=str(e),
                    )
                    
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(
                        "All retry attempts exhausted",
                        event_id=event_id,
                        attempts=attempt + 1,
                        error=str(e),
                    )
                    raise e
            
            except Exception as e:
                logger.error(
                    "Unexpected error sending to Kafka",
                    event_id=event_id,
                    attempt=attempt + 1,
                    error=str(e),
                )
                raise e
        
        if last_error:
            raise last_error

    async def _send_to_dlq(
        self, 
        event: LearnerEvent, 
        error_reason: str, 
        batch_id: str | None = None
    ) -> None:
        """Send failed event to Dead Letter Queue."""
        try:
            dlq_payload = {
                "original_event": event.dict(),
                "error_reason": error_reason,
                "failed_at": datetime.utcnow().isoformat(),
                "batch_id": batch_id,
                "dlq_id": str(uuid.uuid4()),
                "retry_count": 0,
                "producer_id": settings.kafka_client_id,
            }
            
            # Send to DLQ topic
            future = await self.dlq_producer.send(
                settings.kafka_topic_dlq,
                value=dlq_payload,
                key=event.learner_id,
            )
            
            await future
            self._metrics["events_dlq_total"] += 1
            
            logger.warning(
                "Event sent to DLQ",
                event_id=event.event_id,
                learner_id=event.learner_id,
                error_reason=error_reason,
            )
            
        except Exception as e:
            logger.error(
                "Failed to send event to DLQ",
                event_id=event.event_id,
                learner_id=event.learner_id,
                dlq_error=str(e),
                original_error=error_reason,
            )
            # At this point, we've lost the event - log for manual recovery

    async def health_check(self) -> dict[str, Any]:
        """Check Kafka connection health."""
        try:
            if not self.producer or not self._connected:
                return {
                    "kafka": {
                        "status": "unhealthy",
                        "error": "Producer not connected",
                    }
                }
            
            # Try to get metadata (lightweight operation)
            metadata = await self.producer.client.fetch_metadata()
            
            # Check if our topics exist
            topics_status = {}
            for topic in [settings.kafka_topic_events_raw, settings.kafka_topic_dlq]:
                if topic in metadata.topics:
                    partition_count = len(metadata.topics[topic].partitions)
                    topics_status[topic] = {
                        "exists": True,
                        "partitions": partition_count,
                    }
                else:
                    topics_status[topic] = {
                        "exists": False,
                        "error": "Topic not found",
                    }
            
            return {
                "kafka": {
                    "status": "healthy",
                    "connected": self._connected,
                    "broker_count": len(metadata.brokers),
                    "topics": topics_status,
                    "metrics": self._metrics,
                }
            }
            
        except Exception as e:
            return {
                "kafka": {
                    "status": "unhealthy",
                    "error": str(e),
                    "connected": False,
                }
            }

    async def get_metrics(self) -> dict[str, Any]:
        """Get producer metrics."""
        return dict(self._metrics)

    def is_connected(self) -> bool:
        """Check if producer is connected."""
        return self._connected and self.producer is not None
