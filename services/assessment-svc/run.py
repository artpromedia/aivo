#!/usr/bin/env python3
"""
Start the Assessment Service.

Example usage:
    python run.py
    python run.py --host 0.0.0.0 --port 8001
"""

import argparse

import uvicorn
from app.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Start Assessment Service")
    parser.add_argument("--host", default=settings.host, help="Host to bind to")
    parser.add_argument("--port", type=int, default=settings.port, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default=settings.log_level, help="Log level")

    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower(),
    )


if __name__ == "__main__":
    main()
