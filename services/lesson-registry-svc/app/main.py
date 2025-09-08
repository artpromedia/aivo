"""Main FastAPI application for lesson registry service."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .cdn_service import cdn_service
from .config import settings
from .database import engine, init_db
from .routes import router
from .schemas import HealthCheck

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(  # pylint: disable=unused-argument
    fastapi_app: FastAPI,
) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting Lesson Registry Service")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise

    yield

    # Shutdown
    logger.info("Shutting down Lesson Registry Service")


# Create FastAPI app
app = FastAPI(
    title="Lesson Registry Service",
    description="API for managing versioned lessons with signed CDN assets",
    version=settings.version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "lesson-registry-svc", "version": settings.version, "status": "running"}


@app.get("/healthz", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """Health check endpoint."""
    # Check database connectivity
    database_healthy = True
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
    except (ConnectionError, OSError, RuntimeError) as e:
        logger.error("Database health check failed: %s", e)
        database_healthy = False

    # Check CDN/storage connectivity
    storage_healthy = await cdn_service.health_check()

    # Overall health status
    overall_healthy = database_healthy and storage_healthy

    if not overall_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unhealthy"
        )

    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.version,
        database=database_healthy,
        storage=storage_healthy,
    )


@app.get("/metrics")
async def metrics() -> dict[str, str]:
    """Basic metrics endpoint."""
    # pylint: disable=fixme
    # TODO: Implement proper metrics collection
    return {
        "service": "lesson-registry-svc",
        "uptime": "unknown",
        "requests_total": "unknown",
        "database_connections": "unknown",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
