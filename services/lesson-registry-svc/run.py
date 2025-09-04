"""Run script for lesson registry service."""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8003,  # Different port from other services
        reload=settings.debug,
        log_level="info",
    )
