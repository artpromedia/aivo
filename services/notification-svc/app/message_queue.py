"""Message queue for reliable notification delivery."""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import redis.asyncio as redis

from .config import settings

logger = logging.getLogger(__name__)


class MessageQueue:
    """Manages queued notifications for offline users."""

    def __init__(self) -> None:
        self.redis: redis.Redis | None = None
        self.retry_delays = [1, 5, 15, 60, 300]  # Exponential backoff

    async def init(self) -> None:
        """Initialize Redis connection."""
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()

    async def queue_notification(
        self,
        user_id: str,
        notification: dict[str, Any],
        ttl: int = 86400,
    ) -> str:
        """Queue notification for later delivery."""
        notification_id = notification.get("id", str(uuid4()))

        # Add metadata
        notification["queued_at"] = datetime.now(UTC).isoformat()
        notification["ttl"] = ttl
        notification["retry_count"] = 0

        # Store in Redis with expiration
        key = f"notification_queue:{user_id}:{notification_id}"
        await self.redis.setex(
            key,
            ttl,
            json.dumps(notification),
        )

        # Add to user's queue sorted set
        queue_key = f"user_queue:{user_id}"
        score = datetime.now(UTC).timestamp()
        await self.redis.zadd(queue_key, score, notification_id)

        logger.info("Queued notification %s for %s", notification_id, user_id)

        return notification_id

    async def get_missed_messages(
        self,
        user_id: str,
        replay_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get missed messages for user since replay_id."""
        queue_key = f"user_queue:{user_id}"

        # Get notification IDs from sorted set
        if replay_id:
            # Get messages after replay_id timestamp
            replay_key = f"notification_queue:{user_id}:{replay_id}"
            replay_data = await self.redis.get(replay_key)

            if replay_data:
                replay_notification = json.loads(replay_data)
                replay_timestamp = datetime.fromisoformat(
                    replay_notification["queued_at"]
                ).timestamp()

                notification_ids = await self.redis.zrangebyscore(
                    queue_key,
                    replay_timestamp,
                    "+inf",
                )
            else:
                # Replay ID not found, get all
                notification_ids = await self.redis.zrange(queue_key, 0, -1)
        else:
            # Get all queued messages
            notification_ids = await self.redis.zrange(queue_key, 0, -1)

        # Fetch actual notifications
        messages = []
        for notification_id in notification_ids:
            key = f"notification_queue:{user_id}:{notification_id}"
            data = await self.redis.get(key)

            if data:
                notification = json.loads(data)
                messages.append(notification)

        logger.info("Retrieved %s missed messages for %s", len(messages), user_id)

        return messages

    async def mark_delivered(
        self,
        user_id: str,
        notification_id: str,
    ) -> None:
        """Mark notification as delivered."""
        # Remove from queue
        queue_key = f"user_queue:{user_id}"
        await self.redis.zrem(queue_key, notification_id)

        # Delete notification data
        key = f"notification_queue:{user_id}:{notification_id}"
        await self.redis.delete(key)

        logger.info("Marked %s as delivered for %s", notification_id, user_id)

    async def retry_failed(
        self,
        user_id: str,
        notification_id: str,
    ) -> bool:
        """Retry failed notification with exponential backoff."""
        key = f"notification_queue:{user_id}:{notification_id}"
        data = await self.redis.get(key)

        if not data:
            return False

        notification = json.loads(data)
        retry_count = notification.get("retry_count", 0)

        if retry_count >= len(self.retry_delays):
            # Max retries exceeded
            logger.warning("Max retries exceeded for %s (%s)", notification_id, user_id)
            await self.mark_delivered(user_id, notification_id)
            return False

        # Schedule retry
        retry_delay = self.retry_delays[retry_count]
        notification["retry_count"] = retry_count + 1
        notification["next_retry"] = (
            datetime.now(UTC) + timedelta(seconds=retry_delay)
        ).isoformat()

        # Update notification
        await self.redis.setex(
            key,
            notification["ttl"],
            json.dumps(notification),
        )

        logger.info(
            "Scheduled retry %s for %s in %ss",
            retry_count + 1,
            notification_id,
            retry_delay,
        )

        return True

    async def process_retry_queue(self) -> None:
        """Background task to process retry queue."""
        while True:
            try:
                # Get all user queues
                user_queues = await self.redis.keys("user_queue:*")

                for queue_key in user_queues:
                    user_id = queue_key.split(":")[1]

                    # Get notifications ready for retry
                    now = datetime.now(UTC).timestamp()
                    notification_ids = await self.redis.zrangebyscore(
                        queue_key,
                        "-inf",
                        now,
                    )

                    for notification_id in notification_ids:
                        key = f"notification_queue:{user_id}:{notification_id}"
                        data = await self.redis.get(key)

                        if data:
                            notification = json.loads(data)
                            next_retry = notification.get("next_retry")

                            if next_retry:
                                retry_time = datetime.fromisoformat(next_retry)
                                if retry_time <= datetime.now(UTC):
                                    # Trigger retry
                                    logger.info(
                                        "Retrying %s for %s",
                                        notification_id,
                                        user_id,
                                    )
                                    # FUTURE: Implement actual delivery attempt
                                    # Integrate with notification service

                await asyncio.sleep(30)  # Check every 30 seconds

            except (redis.RedisError, OSError, ValueError) as e:
                logger.error("Retry queue processing error: %s", e)
                await asyncio.sleep(60)
