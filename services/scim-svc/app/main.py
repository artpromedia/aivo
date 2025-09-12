"""
SCIM Service main application entry point.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import make_asgi_app

from .config import get_settings
from .database import engine, init_db
from .routes import health, service_provider, users, groups, bulk, schemas as schema_routes
from .middleware.rate_limiter import RateLimiterMiddleware
from .middleware.authentication import AuthenticationMiddleware
from .middleware.tenant_isolation import TenantIsolationMiddleware
from .exceptions import SCIMException, scim_exception_handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management."""
    # Startup
    logger.info("Starting SCIM Service...")

    # Initialize database
    await init_db()

    # Setup OpenTelemetry
    if settings.environment != "test":
        resource = Resource(attributes={
            "service.name": "scim-svc",
            "service.version": "0.1.0"
        })

        trace.set_tracer_provider(TracerProvider(resource=resource))

        # Add OTLP exporter if configured
        if settings.otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

    logger.info("SCIM Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down SCIM Service...")
    await engine.dispose()
    logger.info("SCIM Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="SCIM 2.0 Provisioning Service",
    description="Enterprise Identity Management and User Provisioning Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    root_path="/scim/v2" if settings.environment == "production" else ""
)

# Add middleware in correct order
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

# Add custom middleware
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(TenantIsolationMiddleware)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Add exception handlers
app.add_exception_handler(SCIMException, scim_exception_handler)


# Include routers with SCIM v2 prefix
app.include_router(health.router, tags=["health"])
app.include_router(service_provider.router, prefix="/ServiceProviderConfig", tags=["service-provider"])
app.include_router(schema_routes.router, prefix="/Schemas", tags=["schemas"])
app.include_router(users.router, prefix="/Users", tags=["users"])
app.include_router(groups.router, prefix="/Groups", tags=["groups"])
app.include_router(bulk.router, prefix="/Bulk", tags=["bulk"])

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Instrument with OpenTelemetry
if settings.environment != "test":
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "scim-svc",
        "version": "0.1.0",
        "description": "SCIM 2.0 Provisioning Service for Enterprise Identity Management",
        "status": "healthy",
        "scim_version": "2.0",
        "supported_operations": [
            "Users", "Groups", "Bulk", "ServiceProviderConfig", "Schemas"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "service_provider_config": "/ServiceProviderConfig",
            "schemas": "/Schemas",
            "users": "/Users",
            "groups": "/Groups",
            "bulk": "/Bulk"
        }
    }


@app.get("/v2")
async def scim_root():
    """SCIM v2 root endpoint."""
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "Resources": [
            {
                "name": "User",
                "endpoint": f"{settings.base_url}/Users",
                "description": "User Account",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
            },
            {
                "name": "Group",
                "endpoint": f"{settings.base_url}/Groups",
                "description": "Group",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:Group"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
