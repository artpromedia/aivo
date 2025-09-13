"""
Data Governance Service - Main Application

Provides data retention policies, legal holds, and data subject rights (DSR) management
for FERPA/COPPA compliance and eDiscovery workflows.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import structlog

from .config import settings
from .database import engine, Base
from .routes import retention_policies, dsr_requests, legal_holds
from .services.cleanup_service import CleanupService


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

logger = structlog.get_logger()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Background cleanup service
cleanup_service = CleanupService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Data Governance Service")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_service.start())

    yield

    # Cleanup
    logger.info("Shutting down Data Governance Service")
    await cleanup_service.stop()
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title="Data Governance Service",
    description="Privacy-focused data retention, DSR processing, and legal holds management",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "data-governance"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check database connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return {"status": "ready", "service": "data-governance"}
    except Exception as e:
        logger.error("Readiness check failed", exc_info=e)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "error": str(e)}
        )


# Include routers
app.include_router(
    retention_policies.router,
    prefix="/policies/retention",
    tags=["Retention Policies"]
)

app.include_router(
    dsr_requests.router,
    prefix="/dsr",
    tags=["Data Subject Rights"]
)

app.include_router(
    legal_holds.router,
    prefix="/holds",
    tags=["Legal Holds"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
