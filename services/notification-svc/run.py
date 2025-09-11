#!/usr/bin/env python3
"""
Run script for the Notification Service.
"""

import argparse

import uvicorn

from app.config import settings


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Notification Service")
    parser.add_argument("--host", default=settings.host, help="Host to bind to")
    parser.add_argument("--port", type=int, default=settings.port, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")

    args = parser.parse_args()

    # Update settings if debug mode is requested
    if args.debug:
        settings.debug = True

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="debug" if args.debug else "info",
    )


if __name__ == "__main__":
    main()
