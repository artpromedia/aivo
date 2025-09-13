"""FastAPI application configuration."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import create_tables
from .routes import usage, limits, requests


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await create_tables()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="API Usage Service",
        description="API usage tracking, rate limits, and quota management",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(usage.router)
    app.include_router(limits.router)
    app.include_router(requests.router)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "api-usage-svc"}

    return app


# Create app instance
app = create_app()
