"""FastAPI application setup for Device OTA & Heartbeat Service."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# pylint: disable=import-error
from app.config import get_settings
from app.database import create_tables
from app.routes import firmware, health, heartbeat


@asynccontextmanager
async def lifespan(_app: FastAPI):  # pylint: disable=unused-argument
    """Application lifespan events."""
    # Startup
    settings = get_settings()
    await create_tables()

    # Log startup
    print(f"Device OTA & Heartbeat Service starting on {settings.environment}")
    print(f"Database: {settings.database_url}")

    yield

    # Shutdown
    print("Device OTA & Heartbeat Service shutting down")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title="Device OTA & Heartbeat Service",
        description=(
            "S2A-10 — OTA & Heartbeat — Device firmware/app updates "
            "with rings and rollback + heartbeat collection"
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    # Security middleware
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts,
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )

    # Include routers
    application.include_router(
        health.router,
        prefix="/health",
        tags=["Health"],
    )

    application.include_router(
        firmware.router,
        prefix="/api/v1",
        tags=["Firmware Updates"],
    )

    application.include_router(
        heartbeat.router,
        prefix="/api/v1",
        tags=["Device Heartbeat"],
    )

    return application


# Create app instance
app = create_app()
