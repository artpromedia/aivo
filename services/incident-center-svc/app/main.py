"""
Main FastAPI Application
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

import structlog
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.database import create_tables
from app.routes import banners, incidents, subscriptions

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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Set up rate limiter
limiter = Limiter(key_func=get_remote_address)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""

    logger.info("Starting Incident Center Service")

    # Create database tables
    await create_tables()
    logger.info("Database tables created/verified")

    # TODO: Start background tasks (Celery workers, etc.)
    # TODO: Initialize Redis connections

    yield

    logger.info("Shutting down Incident Center Service")

    # TODO: Cleanup background tasks
    # TODO: Close Redis connections


# Create FastAPI application
app = FastAPI(
    title="Incident Center Service",
    description="S2C-06 Incident Center & Notifications API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "incident-center"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # TODO: Check database connectivity
    # TODO: Check Redis connectivity
    # TODO: Check external service dependencies

    return {
        "status": "ready",
        "service": "incident-center",
        "version": "1.0.0"
    }


@app.get("/metrics")
@limiter.limit("10/minute")
async def metrics(request: Request):
    """Basic metrics endpoint."""
    # TODO: Implement proper metrics collection
    # TODO: Add Prometheus-compatible metrics

    return {
        "incidents_total": 0,
        "active_incidents": 0,
        "banners_total": 0,
        "active_banners": 0,
        "subscriptions_total": 0,
        "notifications_sent_24h": 0
    }


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log HTTP requests."""

    start_time = asyncio.get_event_loop().time()

    # Log request
    logger.info(
        "HTTP request started",
        method=request.method,
        url=str(request.url),
        user_agent=request.headers.get("user-agent"),
        x_forwarded_for=request.headers.get("x-forwarded-for"),
        remote_addr=request.client.host if request.client else None
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = asyncio.get_event_loop().time() - start_time

    # Log response
    logger.info(
        "HTTP request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2)
    )

    # Add custom headers
    response.headers["X-Service"] = "incident-center"
    response.headers["X-Response-Time"] = f"{duration:.3f}s"

    return response


# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""

    logger.error(
        "Unhandled exception",
        method=request.method,
        url=str(request.url),
        error_type=type(exc).__name__,
        error_message=str(exc),
        exc_info=True
    )

    return Response(
        content="Internal Server Error",
        status_code=500,
        media_type="text/plain"
    )


# Include routers
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(banners.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        access_log=True
    )
