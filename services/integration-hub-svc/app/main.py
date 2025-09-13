"""FastAPI application for Integration Hub Service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import make_asgi_app
import structlog

from app.config import settings
from app.database import init_db
from app.routes import api_keys, health, webhooks


# Configure structured logging
logging.basicConfig(
    format="%(message)s",
    stream=None,
    level=getattr(logging, settings.log_level.upper()),
)
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
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting Integration Hub Service", version=settings.version)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    yield

    logger.info("Shutting down Integration Hub Service")


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    description=settings.description,
    version=settings.version,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    docs_url=f"{settings.api_v1_str}/docs",
    redoc_url=f"{settings.api_v1_str}/redoc",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Configure appropriately for production
)

# Add routes
app.include_router(health.router, prefix=settings.api_v1_str, tags=["Health"])
app.include_router(api_keys.router, prefix=settings.api_v1_str, tags=["API Keys"])
app.include_router(webhooks.router, prefix=settings.api_v1_str, tags=["Webhooks"])

# Add metrics endpoint
if settings.enable_metrics:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Enable OpenTelemetry instrumentation
if settings.enable_tracing:
    FastAPIInstrumentor.instrument_app(app)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": settings.project_name,
        "version": settings.version,
        "status": "healthy",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )
