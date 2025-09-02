#!/usr/bin/env python3
"""
Start the IEP Service.

Example usage:
    python run.py
    python run.py --host 0.0.0.0 --port 8001
    python run.py --reload --debug
"""

import argparse
import uvicorn
from app.config import settings

def main():
    parser = argparse.ArgumentParser(description="Start IEP Service")
    parser.add_argument("--host", default=settings.host, help="Host to bind to")
    parser.add_argument("--port", type=int, default=settings.port, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--log-level", default=settings.log_level, help="Log level")
    
    args = parser.parse_args()
    
    # Override settings if debug is enabled
    if args.debug:
        args.reload = True
        args.log_level = "DEBUG"
    
    print(f"Starting IEP Service...")
    print(f"GraphQL endpoint: http://{args.host}:{args.port}{settings.graphql_path}")
    if settings.graphiql_enabled:
        print(f"GraphiQL interface: http://{args.host}:{args.port}{settings.graphql_path}")
    print(f"Health check: http://{args.host}:{args.port}/health")
    print(f"API docs: http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower()
    )

if __name__ == "__main__":
    main()
