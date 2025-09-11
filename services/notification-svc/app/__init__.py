"""Realtime Notification Service for IEP reminders.

This service provides WebSocket, Web Push, and SMS notification delivery
with specialized support for IEP (Individualized Education Program) reminders
and educational notifications.

Features:
- Real-time WebSocket notifications with heartbeat and replay
- Web Push notifications for offline users
- SMS fallback for critical notifications
- IEP-specific templates and reminder types
- Multi-language template support
- Comprehensive analytics and monitoring
"""

__version__ = "1.0.0"
__author__ = "Realtime Engineering Team"
__email__ = "engineering@aivo.com"

from .main import app
from .models import (
    IEPReminderType,
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
    NotificationResponse,
    NotificationType,
    PushSubscription,
)

__all__ = [
    "app",
    "NotificationChannel",
    "NotificationPriority",
    "NotificationType",
    "IEPReminderType",
    "NotificationRequest",
    "NotificationResponse",
    "PushSubscription",
]
