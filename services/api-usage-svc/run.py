#!/usr/bin/env python3
"""Run script for API Usage Service."""

import asyncio
import logging

from app.main import create_app
from app.database import create_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def main():
    """Main application runner."""
    try:
        logger.info("Starting API Usage Service on 0.0.0.0:8500")

        # Create database tables
        await create_tables()
        logger.info("Database tables created/verified")

        # Import uvicorn here to avoid import issues
        import uvicorn

        # Create app instance
        app = create_app()

        # Run the server
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8500,
            log_level="info",
            reload=False
        )
        server = uvicorn.Server(config)

        logger.info("Service started successfully")
        await server.serve()

    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
