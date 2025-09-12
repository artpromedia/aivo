"""
Main FastAPI application for chat service.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .database import close_db, create_tables, get_db
from .routes import get_db_dependency
from .routes import router as chat_router
from .schemas import ErrorResponse, HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting chat service...")

    # Create database tables
    try:
        await create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down chat service...")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="Chat Service",
    description="Chat service with parental controls, moderation, and audit capabilities",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=("/docs" if os.getenv("ENVIRONMENT", "development") == "development" else None),
    redoc_url=("/redoc" if os.getenv("ENVIRONMENT", "development") == "development" else None),
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if os.getenv("ENVIRONMENT") == "production":
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "").split(",")
    if allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# Include routers
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

# Override the dependency in the router
app.dependency_overrides[get_db_dependency] = get_db


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_EXCEPTION",
            message=exc.detail,
        ).model_dump(),
        headers=exc.headers,
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy exceptions."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="DATABASE_ERROR",
            message="Database error occurred",
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="Internal server error",
        ).model_dump(),
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    # Check database connectivity
    database_status = "healthy"
    try:
        async for db in get_db():
            # Simple query to test connection
            await db.execute("SELECT 1")
            break
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status = "unhealthy"

    # Check other services (would implement actual checks in production)
    mongodb_status = "healthy" if os.getenv("MONGODB_CONNECTION_STRING") else "disabled"
    redis_status = "healthy" if os.getenv("REDIS_URL") else "disabled"
    s3_status = "healthy" if os.getenv("AWS_ACCESS_KEY_ID") else "disabled"

    overall_status = "healthy" if database_status == "healthy" else "unhealthy"

    return HealthResponse(
        status=overall_status,
        service="chat-svc",
        version="1.0.0",
        database_status=database_status,
        mongodb_status=mongodb_status,
        redis_status=redis_status,
        s3_status=s3_status,
    )


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Chat Service API",
        "version": "1.0.0",
        "service": "chat-svc",
        "docs": (
            "/docs" if os.getenv("ENVIRONMENT", "development") == "development" else "disabled"
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
