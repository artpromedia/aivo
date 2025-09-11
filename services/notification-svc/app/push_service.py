"""Web Push notification service."""

import json
import logging

from py_vapid import Vapid
from pywebpush import WebPushException, webpush

from .config import settings
from .models import PushSubscription

logger = logging.getLogger(__name__)


class PushService:
    """Manages Web Push notifications."""

    def __init__(self) -> None:
        self.vapid_claims = {
            "sub": f"mailto:{settings.VAPID_EMAIL}",
        }
        self.subscriptions: dict[str, list[PushSubscription]] = {}

    async def init(self) -> None:
        """Initialize push service."""
        # Load or generate VAPID keys
        if not settings.VAPID_PRIVATE_KEY:
            vapid = Vapid()
            vapid.generate_keys()
            logger.warning("Generated VAPID keys. Public key: %s", vapid.public_key)
        else:
            logger.info("Using configured VAPID keys")

    async def subscribe(
        self,
        user_id: str,
        subscription: PushSubscription,
    ) -> bool:
        """Register a push subscription for a user."""
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = []

        # Check if subscription already exists
        for sub in self.subscriptions[user_id]:
            if sub.endpoint == subscription.endpoint:
                # Update existing subscription
                sub.keys = subscription.keys
                sub.expiration_time = subscription.expiration_time
                logger.info("Updated push subscription for %s", user_id)
                return True

        # Add new subscription
        self.subscriptions[user_id].append(subscription)
        logger.info("Added push subscription for %s", user_id)

        # FUTURE: Persist to database
        await self._persist_subscription(user_id, subscription)

        return True

    async def unsubscribe(
        self,
        user_id: str,
        endpoint: str,
    ) -> bool:
        """Remove a push subscription."""
        if user_id not in self.subscriptions:
            return False

        subscriptions = self.subscriptions[user_id]
        self.subscriptions[user_id] = [sub for sub in subscriptions if sub.endpoint != endpoint]

        logger.info("Removed push subscription for %s", user_id)

        # FUTURE: Remove from database
        await self._remove_subscription(user_id, endpoint)

        return True

    async def send(
        self,
        user_id: str,
        notification: dict,
    ) -> dict[str, any]:
        """Send push notification to user's subscriptions."""
        if user_id not in self.subscriptions:
            return {"status": "no_subscriptions"}

        results = {
            "status": "sent",
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        invalid_subscriptions = []

        for subscription in self.subscriptions[user_id]:
            try:
                response = webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": subscription.keys,
                    },
                    data=json.dumps(notification),
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims=self.vapid_claims,
                    ttl=86400,  # 24 hours
                )

                if response.status_code in [200, 201, 204]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        {
                            "endpoint": subscription.endpoint,
                            "status": response.status_code,
                        }
                    )

                    # Mark invalid subscriptions for removal
                    if response.status_code == 410:  # Gone
                        invalid_subscriptions.append(subscription.endpoint)

            except WebPushException as e:
                logger.error("Push failed for %s: %s", user_id, e)
                results["failed"] += 1
                results["errors"].append(
                    {
                        "endpoint": subscription.endpoint,
                        "error": str(e),
                    }
                )

                # Handle invalid subscription
                if e.response and e.response.status_code == 410:
                    invalid_subscriptions.append(subscription.endpoint)

        # Clean up invalid subscriptions
        for endpoint in invalid_subscriptions:
            await self.unsubscribe(user_id, endpoint)

        return results

    async def broadcast(
        self,
        notification: dict,
        user_ids: list[str] | None = None,
    ) -> dict[str, any]:
        """Broadcast notification to multiple users."""
        if user_ids is None:
            user_ids = list(self.subscriptions.keys())

        results = {
            "total_users": len(user_ids),
            "successful_users": 0,
            "failed_users": 0,
        }

        for user_id in user_ids:
            user_result = await self.send(user_id, notification)
            if user_result.get("successful", 0) > 0:
                results["successful_users"] += 1
            else:
                results["failed_users"] += 1

        return results

    async def _persist_subscription(
        self,
        user_id: str,
        subscription: PushSubscription,
    ) -> None:
        """Persist subscription to database."""
        # FUTURE: Implement database persistence

    async def _remove_subscription(
        self,
        user_id: str,
        endpoint: str,
    ) -> None:
        """Remove subscription from database."""
        # FUTURE: Implement database removal
