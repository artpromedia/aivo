#!/usr/bin/env python3
"""Run the Secrets Vault Service."""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from app.config import settings


async def main():
    """Main entry point."""
    config = uvicorn.Config(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
        access_log=True,
    )

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    print(f"Starting Secrets Vault Service on {settings.host}:{settings.port}")
    print(f"Environment: {settings.environment}")
    print(f"Database: {settings.database_url}")
    print(f"KMS Provider: {settings.kms_provider}")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nService stopped by user")
    except Exception as e:
        print(f"Service failed to start: {e}")
        sys.exit(1)
