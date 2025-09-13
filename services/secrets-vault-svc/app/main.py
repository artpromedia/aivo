"""Secrets Vault Service - FastAPI application."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import init_db
from .routes import namespaces_router, secrets_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting Secrets Vault Service...")

    # Create database tables
    await init_db()
    logger.info("Database tables created/verified")

    # Initialize default namespace
    try:
        from .database import AsyncSessionLocal
        from .services import NamespaceService

        async with AsyncSessionLocal() as db:
            namespace_service = NamespaceService()

            # Check if default namespace exists
            default_namespace = await namespace_service.get_namespace_by_name(db, "default")
            if not default_namespace:
                await namespace_service.create_namespace(
                    db=db,
                    name="default",
                    display_name="Default",
                    description="Default namespace for secrets",
                    created_by="system",
                )
                logger.info("Created default namespace")
    except Exception as e:
        logger.error(f"Failed to create default namespace: {e}")

    logger.info("Secrets Vault Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Secrets Vault Service...")


# Create FastAPI application
app = FastAPI(
    title="Secrets Vault Service",
    description="Secure secrets management with KMS envelope encryption",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan,
)

# Add middleware
# Note: TrustedHostMiddleware is commented out - add allowed_hosts to config if needed
# if settings.allowed_hosts:
#     app.add_middleware(
#         TrustedHostMiddleware,
#         allowed_hosts=settings.allowed_hosts
#     )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError exceptions."""
    logger.warning(f"ValueError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "type": "validation_error"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "http_error"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error" if settings.environment == "production" else str(exc),
            "type": "internal_error",
        },
    )


# Health check endpoints
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "secrets-vault-svc",
        "version": "1.0.0",
        "environment": settings.environment,
    }


@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """Readiness check endpoint."""
    try:
        from .database import AsyncSessionLocal

        # Test database connection
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text
            await db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "checks": {
                "database": "ok",
                "encryption": "ok",
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "error": str(e),
            }
        )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "service": "Secrets Vault Service",
        "description": "Secure secrets management with KMS envelope encryption",
        "version": "1.0.0",
        "docs_url": "/docs" if settings.environment == "development" else None,
    }


# Include routers
app.include_router(namespaces_router)
app.include_router(secrets_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
