"""
FastAPI application setup with consent ledger API routes.

Main application with CORS, middleware, and route registration.
"""
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.api import consent_router, parental_router, export_router, deletion_router, health_router
from config import get_settings, init_database, cleanup_database, is_database_healthy


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_database()
    yield
    # Shutdown
    await cleanup_database()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Centralized consent and preferences management with GDPR/COPPA compliance",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    # Trusted host middleware for production
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.district.edu"]
        )
    
    # Register API routers
    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(consent_router, prefix="/api/v1/consent", tags=["Consent"])
    app.include_router(parental_router, prefix="/api/v1/parental", tags=["Parental Rights"])
    app.include_router(export_router, prefix="/api/v1/export", tags=["Data Export"])
    app.include_router(deletion_router, prefix="/api/v1/deletion", tags=["Data Deletion"])
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
                "detail": "Please contact support if this issue persists"
            }
        )
    
    # Health check middleware
    @app.middleware("http")
    async def health_check_middleware(request: Request, call_next):
        """Add health status headers to responses."""
        response = await call_next(request)
        
        # Add health status header
        db_healthy = await is_database_healthy()
        response.headers["X-Health-Database"] = "healthy" if db_healthy else "unhealthy"
        response.headers["X-Service-Version"] = settings.APP_VERSION
        
        return response
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
