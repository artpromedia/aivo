#!/usr/bin/env python3
"""
Science Solver Service startup script.

This script can be used to start the service in development or production mode.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Start the Science Solver Service."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get the directory where this script is located
    script_dir = Path(__file__).parent

    # Add the script directory to Python path
    sys.path.insert(0, str(script_dir))

    # Set environment variables
    os.environ.setdefault("PYTHONPATH", str(script_dir))

    # Default configuration
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8003"))
    debug = os.environ.get("DEBUG", "false").lower() == "true"

    logger.info("Starting Science Solver Service on %s:%s", host, port)
    logger.info("Working directory: %s", script_dir)
    logger.info("Debug mode: %s", debug)

    # Start uvicorn with controlled input
    python_executable = sys.executable
    cmd = [
        python_executable, "-m", "uvicorn",
        "app.main:app",
        "--host", host,
        "--port", str(port),
    ]

    if debug:
        cmd.append("--reload")

    try:
        subprocess.run(cmd, cwd=script_dir, check=True)  # noqa: S603
    except KeyboardInterrupt:
        logger.info("Shutting down Science Solver Service")
    except subprocess.CalledProcessError:
        logger.exception("Error starting service")
        sys.exit(1)


if __name__ == "__main__":
    main()
