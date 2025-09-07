"""Real-time notification service with WebSocket, Push, and SMS."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import redis.asyncio as redis
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt

from .config import settings
from .message_queue import MessageQueue
from .models import (
    NotificationChannel,
    NotificationRequest,
    PushSubscription,
)
from .push_service import PushService
from .sms_service import SMSService
from .template_engine import TemplateEngine

logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """Manages WebSocket connections and message routing."""

    def __init__(self) -> None:
        self.active_connections: dict[str, set[WebSocket]] = {}
        self.connection_metadata: dict[WebSocket, dict[str, Any]] = {}
        self.redis: redis.Redis | None = None

    async def init_redis(self) -> None:
        """Initialize Redis connection for pub/sub."""
        self.redis = redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        user_role: str | None = None,
        token: str | None = None,
    ) -> None:
        """Accept and track WebSocket connection."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(UTC),
            "user_role": user_role,
            "token": token,
        }

        logger.info(f"User {user_id} connected via WebSocket")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection."""
        metadata = self.connection_metadata.get(websocket, {})
        user_id = metadata.get("user_id")

        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        logger.info(f"User {user_id} disconnected from WebSocket")

    async def send_personal_message(
        self,
        message: str,
        user_id: str,
        message_type: str = "notification",
    ) -> None:
        """Send message to specific user's connections."""
        if user_id in self.active_connections:
            disconnected = []

            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(
                        {
                            "id": str(uuid4()),
                            "type": message_type,
                            "timestamp": datetime.now(UTC).isoformat(),
                            "data": message,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send to {user_id}: {e}")
                    disconnected.append(connection)

            # Clean up disconnected connections
            for conn in disconnected:
                await self.disconnect(conn)

    async def broadcast(
        self, message: str, message_type: str = "broadcast"
    ) -> None:
        """Broadcast message to all connected users."""
        all_connections = []
        for connections in self.active_connections.values():
            all_connections.extend(connections)

        for connection in all_connections:
            try:
                await connection.send_json(
                    {
                        "id": str(uuid4()),
                        "type": message_type,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "data": message,
                    }
                )
            except Exception as e:
                logger.error(f"Broadcast failed: {e}")


manager = ConnectionManager()
push_service = PushService()
sms_service = SMSService()
template_engine = TemplateEngine()
message_queue = MessageQueue()


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    await manager.init_redis()
    await message_queue.init()
    await push_service.init()
    logger.info("Notification service started")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    if manager.redis:
        manager.redis.close()
        await manager.redis.wait_closed()
    await message_queue.close()
    logger.info("Notification service stopped")


async def verify_jwt_token(token: str) -> dict[str, Any]:
    """Verify JWT token and extract user info."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


@app.websocket("/ws/notify")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = None,
    replay_id: str | None = None,
) -> None:
    """WebSocket endpoint for real-time notifications."""
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return

    try:
        # Verify JWT token
        user_data = await verify_jwt_token(token)
        user_id = user_data.get("sub")

        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Connect WebSocket
        await manager.connect(
            websocket,
            user_id,
            {"replay_id": replay_id, "user_data": user_data},
        )

        # Send initial connection success
        await websocket.send_json(
            {
                "id": str(uuid4()),
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # Replay missed messages if replay_id provided
        if replay_id:
            missed_messages = await message_queue.get_missed_messages(
                user_id,
                replay_id,
            )
            for msg in missed_messages:
                await websocket.send_json(msg)

        # Heartbeat task
        async def heartbeat() -> None:
            while True:
                try:
                    await asyncio.sleep(30)
                    await websocket.send_json(
                        {
                            "id": str(uuid4()),
                            "type": "heartbeat",
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )
                except Exception:
                    break

        heartbeat_task = asyncio.create_task(heartbeat())

        try:
            # Listen for messages
            while True:
                data = await websocket.receive_json()

                # Handle client heartbeat response
                if data.get("type") == "pong":
                    continue

                # Handle other message types
                logger.info(f"Received from {user_id}: {data}")

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for {user_id}")
        finally:
            heartbeat_task.cancel()
            await manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))


@app.post("/push/subscribe")
async def subscribe_push(
    subscription: PushSubscription,
    current_user: dict = Depends(verify_jwt_token),
) -> dict:
    """Subscribe to push notifications."""
    user_id = current_user.get("sub")

    try:
        await push_service.subscribe(user_id, subscription)
        return {
            "status": "success",
            "message": "Push subscription registered",
        }
    except Exception as e:
        logger.error(f"Push subscription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/push/unsubscribe")
async def unsubscribe_push(
    endpoint: str,
    current_user: dict = Depends(verify_jwt_token),
) -> dict:
    """Unsubscribe from push notifications."""
    user_id = current_user.get("sub")

    try:
        await push_service.unsubscribe(user_id, endpoint)
        return {
            "status": "success",
            "message": "Push subscription removed",
        }
    except Exception as e:
        logger.error(f"Push unsubscribe failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/notify")
async def send_notification(
    request: NotificationRequest,
    current_user: dict | None = None,
) -> dict:
    """Send notification through available channels."""
    try:
        # Generate notification from template
        notification = await template_engine.render(
            request.template_id,
            request.data,
            request.locale,
        )

        results = {
            "notification_id": str(uuid4()),
            "channels": {},
        }

        # Try WebSocket first (if user is connected)
        if NotificationChannel.WEBSOCKET in request.channels:
            if request.user_id in manager.active_connections:
                await manager.send_personal_message(
                    notification,
                    request.user_id,
                    request.notification_type,
                )
                results["channels"]["websocket"] = "delivered"
            else:
                results["channels"]["websocket"] = "user_offline"

        # Try Web Push
        if NotificationChannel.PUSH in request.channels:
            push_result = await push_service.send(
                request.user_id,
                notification,
            )
            results["channels"]["push"] = push_result

        # SMS fallback for critical notifications
        if NotificationChannel.SMS in request.channels and request.priority == "critical":
            if request.phone_number:
                sms_result = await sms_service.send(
                    request.phone_number,
                    notification["sms_text"],
                )
                results["channels"]["sms"] = sms_result
            else:
                results["channels"]["sms"] = "no_phone_number"

        # Queue for later delivery if needed
        if request.queue_if_offline:
            await message_queue.queue_notification(
                request.user_id,
                notification,
                request.ttl,
            )
            results["queued"] = True

        return results

    except Exception as e:
        logger.error(f"Notification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "connections": sum(len(conns) for conns in manager.active_connections.values()),
    }
