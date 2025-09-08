#!/usr/bin/env python3
"""
Start the Approval Service.

Example usage:
    python run.py
    python run.py --host 0.0.0.0 --port 8081
    python run.py --reload --debug
"""

import argparse

import uvicorn
from app.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Start Approval Service")
    parser.add_argument("--host", default=settings.host, help="Host to bind to")
    parser.add_argument("--port", type=int, default=settings.port, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")

    args = parser.parse_args()

    log_level = "debug" if args.debug else settings.log_level.lower()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload or args.debug,
        log_level=log_level,
        workers=args.workers if not (args.reload or args.debug) else 1,
    )


if __name__ == "__main__":
    main()
