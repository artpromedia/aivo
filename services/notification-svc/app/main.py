"""Real-time notification service with WebSocket, Push, and SMS for IEP reminders."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import redis.asyncio as redis
import structlog
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

from .config import settings
from .message_queue import MessageQueue
from .models import (
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
    PushSubscription,
)
from .push_service import PushService
from .sms_service import SMSService
from .template_engine import TemplateEngine

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)

app = FastAPI(
    title="Realtime Notification Service",
    description="WebSocket, Web Push, and SMS notifications for IEP reminders",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenTelemetry instrumentation
FastAPIInstrumentor.instrument_app(app)
RedisInstrumentor().instrument()


class ConnectionManager:
    """Enhanced WebSocket connection manager with heartbeat and replay support."""

    def __init__(self) -> None:
        self.active_connections: dict[str, set[WebSocket]] = {}
        self.connection_metadata: dict[WebSocket, dict[str, Any]] = {}
        self.message_history: dict[str, list[dict[str, Any]]] = {}
        self.replay_sequence: int = 0
        self.heartbeat_interval: int = 30  # seconds
        self.heartbeat_tasks: dict[WebSocket, asyncio.Task] = {}

    async def connect(
        self, websocket: WebSocket, user_id: str, replay_from: str | None = None
    ) -> None:
        """Accept WebSocket connection and set up heartbeat."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(UTC),
            "last_heartbeat": datetime.now(UTC),
            "replay_from": replay_from,
        }

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(websocket))
        self.heartbeat_tasks[websocket] = heartbeat_task

        # Send missed messages if replay requested
        if replay_from:
            await self._replay_messages(websocket, user_id, replay_from)

        logger.info(
            "WebSocket connected",
            user_id=user_id,
            total_connections=len(self.active_connections.get(user_id, set())),
            replay_from=replay_from,
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Clean up WebSocket connection."""
        metadata = self.connection_metadata.get(websocket, {})
        user_id = metadata.get("user_id")

        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # Cancel heartbeat task
        if websocket in self.heartbeat_tasks:
            self.heartbeat_tasks[websocket].cancel()
            del self.heartbeat_tasks[websocket]

        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        logger.info(
            "WebSocket disconnected",
            user_id=user_id,
            connection_duration=(
                datetime.now(UTC) - metadata.get("connected_at", datetime.now(UTC))
            ).total_seconds(),
        )

    async def send_personal_message(
        self, message: dict[str, Any], user_id: str, notification_type: str = "general"
    ) -> dict[str, Any]:
        """Send message to specific user with replay support."""
        self.replay_sequence += 1

        enhanced_message = {
            "id": str(uuid4()),
            "type": notification_type,
            "data": message,
            "timestamp": datetime.now(UTC).isoformat(),
            "replay_id": str(self.replay_sequence),
            "user_id": user_id,
        }

        # Store message for replay
        if user_id not in self.message_history:
            self.message_history[user_id] = []
        self.message_history[user_id].append(enhanced_message)

        # Keep only last 100 messages per user
        if len(self.message_history[user_id]) > 100:
            self.message_history[user_id] = self.message_history[user_id][-100:]

        # Send to active connections
        delivered_count = 0
        if user_id in self.active_connections:
            dead_connections = set()
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(enhanced_message))
                    delivered_count += 1
                except Exception as e:
                    logger.warning("Failed to send message", error=str(e), user_id=user_id)
                    dead_connections.add(websocket)

            # Clean up dead connections
            for websocket in dead_connections:
                await self.disconnect(websocket)

        logger.info(
            "Message sent",
            user_id=user_id,
            message_id=enhanced_message["id"],
            replay_id=enhanced_message["replay_id"],
            delivered_count=delivered_count,
            notification_type=notification_type,
        )

        return {
            "delivered": delivered_count > 0,
            "connections": delivered_count,
            "replay_id": enhanced_message["replay_id"],
        }

    async def _heartbeat_loop(self, websocket: WebSocket) -> None:
        """Send periodic heartbeat pings."""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                heartbeat_msg = {
                    "type": "heartbeat",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "data": {"ping": "ping"},
                }
                await websocket.send_text(json.dumps(heartbeat_msg))

                # Update last heartbeat time
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_heartbeat"] = datetime.now(UTC)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("Heartbeat failed", error=str(e))
            await self.disconnect(websocket)

    async def _replay_messages(self, websocket: WebSocket, user_id: str, replay_from: str) -> None:
        """Replay missed messages from specific replay_id."""
        if user_id not in self.message_history:
            return

        try:
            replay_from_int = int(replay_from)
            messages_to_replay = [
                msg
                for msg in self.message_history[user_id]
                if int(msg["replay_id"]) > replay_from_int
            ]

            for message in messages_to_replay:
                await websocket.send_text(json.dumps(message))
                await asyncio.sleep(0.1)  # Small delay to prevent overwhelming

            logger.info(
                "Messages replayed",
                user_id=user_id,
                replay_from=replay_from,
                messages_count=len(messages_to_replay),
            )

        except (ValueError, TypeError) as e:
            logger.warning("Invalid replay_from value", error=str(e), replay_from=replay_from)

    def get_connection_stats(self) -> dict[str, Any]:
        """Get connection statistics."""
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        active_users = len(self.active_connections)

        # Calculate average connection duration
        now = datetime.now(UTC)
        durations = [
            (now - metadata["connected_at"]).total_seconds()
            for metadata in self.connection_metadata.values()
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_connections": total_connections,
            "active_users": active_users,
            "average_duration_seconds": avg_duration,
            "replay_sequence": self.replay_sequence,
        }


# Global instances
manager = ConnectionManager()
redis_client = redis.from_url(settings.REDIS_URL)
message_queue = MessageQueue(redis_client)
push_service = PushService()
sms_service = SMSService()
template_engine = TemplateEngine()


async def verify_jwt_token(token: str = Query(...)) -> dict[str, Any]:
    """Verify JWT token and extract user information."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )
        return payload
    except JWTError as e:
        logger.warning("JWT verification failed", error=str(e), token=token[:20] + "...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e


@app.websocket("/ws/notify")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    replay_from: str | None = Query(None),
) -> None:
    """WebSocket endpoint for real-time notifications with heartbeat and replay."""
    try:
        # Verify JWT token
        payload = await verify_jwt_token(token)
        user_id = payload["sub"]

        with tracer.start_as_current_span("websocket_connection"):
            await manager.connect(websocket, user_id, replay_from)

            try:
                while True:
                    # Wait for client messages (heartbeat responses, acks, etc.)
                    data = await websocket.receive_text()
                    try:
                        message = json.loads(data)
                        if message.get("type") == "pong":
                            # Handle heartbeat response
                            if websocket in manager.connection_metadata:
                                manager.connection_metadata[websocket]["last_heartbeat"] = (
                                    datetime.now(UTC)
                                )
                        elif message.get("type") == "ack":
                            # Handle message acknowledgment
                            logger.debug(
                                "Message acknowledged", message_id=message.get("message_id")
                            )
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON received from client", data=data)

            except WebSocketDisconnect:
                pass
            finally:
                await manager.disconnect(websocket)

    except HTTPException:
        await websocket.close(code=1008, reason="Unauthorized")
    except Exception as e:
        logger.error(
            "WebSocket error", error=str(e), user_id=user_id if "user_id" in locals() else None
        )
        await websocket.close(code=1011, reason="Internal server error")


@app.post("/push/subscribe")
async def subscribe_push(
    subscription: PushSubscription,
    current_user: dict[str, Any] = Depends(verify_jwt_token),
) -> dict[str, Any]:
    """Subscribe to web push notifications."""
    user_id = current_user.get("sub")

    try:
        with tracer.start_as_current_span("push_subscribe"):
            subscription_id = await push_service.subscribe(user_id, subscription)

            logger.info(
                "Push subscription created",
                user_id=user_id,
                subscription_id=subscription_id,
                endpoint=subscription.endpoint,
            )

            return {
                "status": "success",
                "message": "Push subscription registered",
                "subscription_id": subscription_id,
            }
    except Exception as e:
        logger.error("Push subscribe failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@app.delete("/push/unsubscribe")
async def unsubscribe_push(
    endpoint: str = Query(...),
    current_user: dict[str, Any] = Depends(verify_jwt_token),
) -> dict[str, Any]:
    """Unsubscribe from push notifications."""
    user_id = current_user.get("sub")

    try:
        with tracer.start_as_current_span("push_unsubscribe"):
            await push_service.unsubscribe(user_id, endpoint)

            logger.info(
                "Push subscription removed",
                user_id=user_id,
                endpoint=endpoint,
            )

            return {
                "status": "success",
                "message": "Push subscription removed",
            }
    except Exception as e:
        logger.error("Push unsubscribe failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@app.post("/notify")
async def send_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send notification through multiple channels with IEP reminder support."""
    notification_id = str(uuid4())

    try:
        with tracer.start_as_current_span("send_notification") as span:
            span.set_attributes(
                {
                    "notification.id": notification_id,
                    "notification.type": request.notification_type,
                    "notification.template_id": request.template_id,
                    "notification.user_id": request.user_id,
                    "notification.priority": request.priority,
                    "notification.channels": ",".join(request.channels),
                }
            )

            # Generate notification from template
            notification = await template_engine.render(
                request.template_id,
                request.data,
                request.locale,
            )

            results = {
                "notification_id": notification_id,
                "channels": {},
                "timestamp": datetime.now(UTC).isoformat(),
            }

            logger.info(
                "Notification processing started",
                notification_id=notification_id,
                template_id=request.template_id,
                user_id=request.user_id,
                notification_type=request.notification_type,
                priority=request.priority,
            )

            # Channel 1: WebSocket (real-time)
            if NotificationChannel.WEBSOCKET in request.channels:
                websocket_result = await manager.send_personal_message(
                    notification,
                    request.user_id,
                    request.notification_type,
                )
                results["channels"]["websocket"] = (
                    "delivered" if websocket_result["delivered"] else "user_offline"
                )
                results["websocket_connections"] = websocket_result["connections"]
                results["replay_id"] = websocket_result["replay_id"]

            # Channel 2: Web Push (for offline users)
            if NotificationChannel.PUSH in request.channels:
                try:
                    push_result = await push_service.send(
                        request.user_id,
                        notification,
                        request.notification_type,
                    )
                    results["channels"]["push"] = push_result.get("status", "unknown")
                except Exception as e:
                    logger.warning("Push notification failed", error=str(e))
                    results["channels"]["push"] = "failed"

            # Channel 3: SMS (critical notifications only)
            if (
                NotificationChannel.SMS in request.channels
                and request.priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL]
                and request.phone_number
            ):
                try:
                    sms_result = await sms_service.send(
                        request.phone_number,
                        notification.get("sms_text", notification.get("title", "")),
                        request.notification_type,
                    )
                    results["channels"]["sms"] = sms_result.get("status", "unknown")
                except Exception as e:
                    logger.warning("SMS notification failed", error=str(e))
                    results["channels"]["sms"] = "failed"
            elif NotificationChannel.SMS in request.channels:
                results["channels"]["sms"] = (
                    "no_phone_number" if not request.phone_number else "priority_too_low"
                )

            # Queue for offline delivery if requested
            if request.queue_if_offline:
                background_tasks.add_task(
                    message_queue.queue_notification,
                    request.user_id,
                    notification,
                    request.ttl,
                    notification_id,
                )
                results["queued"] = True

            # Calculate estimated delivery time
            if any(status == "delivered" for status in results["channels"].values()):
                results["estimated_delivery"] = datetime.now(UTC).isoformat()
            elif results.get("queued"):
                results["estimated_delivery"] = (
                    datetime.now(UTC) + timedelta(minutes=5)
                ).isoformat()

            logger.info(
                "Notification processing completed",
                notification_id=notification_id,
                channels_attempted=len(request.channels),
                channels_delivered=sum(
                    1 for status in results["channels"].values() if status == "delivered"
                ),
                queued=results.get("queued", False),
            )

            return results

    except Exception as e:
        logger.error(
            "Notification failed",
            error=str(e),
            notification_id=notification_id,
            template_id=request.template_id,
            user_id=request.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notification delivery failed: {str(e)}",
        ) from e


@app.get("/templates")
async def list_templates(
    category: str | None = Query(None),
    locale: str | None = Query("en-US"),
    current_user: dict[str, Any] = Depends(verify_jwt_token),
) -> dict[str, Any]:
    """List available notification templates."""
    try:
        templates = await template_engine.list_templates(category, locale)
        return {"templates": templates}
    except Exception as e:
        logger.error("Failed to list templates", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@app.get("/analytics")
async def get_analytics(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    notification_type: str | None = Query(None),
    current_user: dict[str, Any] = Depends(verify_jwt_token),
) -> dict[str, Any]:
    """Get notification delivery analytics."""
    try:
        # Get analytics from message queue and Redis
        analytics = await message_queue.get_analytics(
            start_date or datetime.now(UTC) - timedelta(days=30),
            end_date or datetime.now(UTC),
            notification_type,
        )

        # Add connection stats
        analytics["connection_stats"] = manager.get_connection_stats()

        return analytics
    except Exception as e:
        logger.error("Failed to get analytics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Comprehensive health check with connection and service status."""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.0.0",
        "service": "notification-svc",
    }

    try:
        # Connection stats
        connection_stats = manager.get_connection_stats()
        health_data.update(connection_stats)

        # Redis health
        await redis_client.ping()
        health_data["redis"] = "healthy"

        # Service health checks
        health_data["services"] = {
            "websocket": "healthy",
            "push": await push_service.health_check(),
            "sms": await sms_service.health_check(),
            "templates": await template_engine.health_check(),
        }

    except Exception as e:
        logger.warning("Health check partial failure", error=str(e))
        health_data["status"] = "degraded"
        health_data["error"] = str(e)

    return health_data


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    logger.info("Starting notification service")

    try:
        # Initialize services
        await template_engine.initialize()
        await push_service.initialize()
        await sms_service.initialize()

        logger.info("Notification service started successfully")
    except Exception as e:
        logger.error("Failed to start notification service", error=str(e))
        raise


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up resources on shutdown."""
    logger.info("Shutting down notification service")

    # Cancel all heartbeat tasks
    for task in manager.heartbeat_tasks.values():
        task.cancel()

    # Close Redis connections
    await redis_client.close()

    logger.info("Notification service shut down")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        },
    )
