from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from typing import AsyncGenerator

from .database import init_database
from .routes import simple_reports, simple_schedules, simple_exports
from .services.simple_scheduler import SchedulerService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting reports service")

    # Initialize database
    await init_database()

    # Start scheduler service
    scheduler = SchedulerService()
    await scheduler.start()
    app.state.scheduler = scheduler

    logger.info("Reports service started successfully")

    yield

    # Cleanup
    logger.info("Shutting down reports service")
    await scheduler.stop()
    logger.info("Reports service stopped")

app = FastAPI(
    title="Reports Service",
    description="Self-serve report builder with scheduled exports to S3/email",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(simple_reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(simple_schedules.router, prefix="/api/v1/schedules", tags=["schedules"])
app.include_router(simple_exports.router, prefix="/api/v1/exports", tags=["exports"])

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "reports-svc"}

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "reports-svc",
        "description": "Self-serve report builder with scheduled exports",
        "version": "1.0.0",
        "endpoints": {
            "reports": "/api/v1/reports",
            "schedules": "/api/v1/schedules",
            "exports": "/api/v1/exports",
            "health": "/health"
        }
    }
