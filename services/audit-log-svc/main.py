"""FastAPI application entry point for audit log service."""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn

from app.config import get_settings
from app.database import create_tables, close_db
from app.routes import audit, export, health
from app.services.audit_service import AuditService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    logger.info("Starting audit log service")

    try:
        # Create database tables
        await create_tables()
        logger.info("Database tables created successfully")

        # Initialize services
        audit_service = AuditService()
        logger.info("Services initialized")

        yield

    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise
    finally:
        logger.info("Shutting down audit log service")
        await close_db()


# Create FastAPI app
app = FastAPI(
    title="Audit Log Service",
    description="Immutable audit logging service with WORM compliance and hash chain verification",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log HTTP requests and responses."""
    start_time = asyncio.get_event_loop().time()

    # Extract request info
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=client_ip,
        user_agent=user_agent,
    )

    try:
        response = await call_next(request)
        process_time = asyncio.get_event_loop().time() - start_time

        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
        )

        return response

    except Exception as e:
        process_time = asyncio.get_event_loop().time() - start_time

        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=process_time,
        )

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(
    health.router,
    prefix="/health",
    tags=["health"],
)

app.include_router(
    audit.router,
    prefix="/api/v1",
    tags=["audit"],
)

app.include_router(
    export.router,
    prefix="/api/v1",
    tags=["export"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "audit-log-service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else "disabled",
    }


@app.get("/info")
async def info():
    """Service information endpoint."""
    return {
        "service": "audit-log-service",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "features": {
            "worm_compliance": True,
            "hash_chain_verification": True,
            "export_formats": ["csv", "json", "xlsx"],
            "s3_exports": True,
        },
        "database": {
            "type": "postgresql",
            "worm_enabled": True,
        },
    }


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None,  # Use structlog instead
    )
