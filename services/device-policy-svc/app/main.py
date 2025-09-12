"""FastAPI main application for Device Policy Service."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.routes import router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting Device Policy Service")

    # Create database tables
    try:
        await create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Database initialization failed", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Device Policy Service")


# FastAPI app configuration
app = FastAPI(
    title="Device Policy & MDM Service",
    description=("Aivo Pad device policy management, kiosk mode, and " "network allowlist service"),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return {
        "error": "internal_server_error",
        "message": "An unexpected error occurred",
    }


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "Device Policy Service",
        "version": "1.0.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
