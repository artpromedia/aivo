"""
Main FastAPI application for auth service.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import Base
from .routes import router as auth_router
from .schemas import ErrorResponse

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://auth_user:auth_password@localhost:5432/auth_db"
)

# Create async engine with conditional pool arguments
engine_kwargs = {
    "echo": bool(os.getenv("DATABASE_ECHO", False)),
}

# Only add pool arguments for non-SQLite databases
if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update(
        {
            "pool_size": int(os.getenv("DATABASE_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
        }
    )

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Create session factory
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Close database connections
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Auth Service",
    description="Authentication and authorization service with JWT and RBAC",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT", "development") == "development" else None,
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


# Dependency to get database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_factory() as session:
        try:
            yield session
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()


# Include routers first
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

# Override the dependency in the app after including the router
from .routes import get_db_dependency

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
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="Internal server error",
        ).model_dump(),
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth-svc", "version": "1.0.0"}


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Auth Service API",
        "version": "1.0.0",
        "docs": "/docs" if os.getenv("ENVIRONMENT", "development") == "development" else "disabled",
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
