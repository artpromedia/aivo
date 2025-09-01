"""
Main FastAPI application for tenant service.
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .database import create_tables
from .routes import router as tenant_router
from .schemas import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI application.
    """
    # Startup
    try:
        await create_tables()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Failed to create database tables: {e}")
        raise
    
    yield
    
    # Shutdown
    print("Tenant service shutting down")


# Create FastAPI application
app = FastAPI(
    title="Tenant Service",
    description="Multi-tenant service for managing districts, schools, and seat allocation",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with actual domains in production
    )

# Include routers
app.include_router(tenant_router, prefix="/api/v1", tags=["tenant"])


# Global exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database errors."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="Database error occurred",
            error_code="DATABASE_ERROR"
        ).model_dump()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            detail=str(exc),
            error_code="VALIDATION_ERROR"
        ).model_dump()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_code="HTTP_ERROR"
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="Internal server error",
            error_code="INTERNAL_ERROR"
        ).model_dump()
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "tenant-svc",
        "status": "running",
        "version": "1.0.0"
    }


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        reload=True
    )
