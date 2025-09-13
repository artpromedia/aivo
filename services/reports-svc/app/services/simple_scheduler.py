"""Simplified scheduler service for testing."""

import asyncio
import structlog

logger = structlog.get_logger()

class SchedulerService:
    """Simplified scheduler service for testing."""

    def __init__(self):
        self.running = False

    async def start(self):
        """Start the scheduler service."""
        logger.info("Starting simplified scheduler service")
        self.running = True

    async def stop(self):
        """Stop the scheduler service."""
        logger.info("Stopping simplified scheduler service")
        self.running = False
