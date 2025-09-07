#!/usr/bin/env python3
"""Development server for notification service."""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.WEBSOCKET_HOST,
        port=settings.WEBSOCKET_PORT,
        reload=settings.DEVELOPMENT_MODE,
        log_level=settings.LOG_LEVEL.lower(),
    )
