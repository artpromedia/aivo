"""
SSO Service main application entry point.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
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
from .routes import health, saml, providers, mappings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management."""
    # Startup
    logger.info("Starting SSO Service...")

    # Initialize database
    await init_db()

    # Setup OpenTelemetry
    if settings.environment != "test":
        resource = Resource(attributes={
            "service.name": "sso-svc",
            "service.version": "0.1.0"
        })

        trace.set_tracer_provider(TracerProvider(resource=resource))

        # Add OTLP exporter if configured
        if settings.otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

    logger.info("SSO Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down SSO Service...")
    await engine.dispose()
    logger.info("SSO Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="SSO Service",
    description="Enterprise Single Sign-On and SAML Identity Provider Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    root_path="/api/v1" if settings.environment == "production" else ""
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(saml.router, prefix="/saml", tags=["saml"])
app.include_router(providers.router, prefix="/providers", tags=["providers"])
app.include_router(mappings.router, prefix="/mappings", tags=["mappings"])

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
        "service": "sso-svc",
        "version": "0.1.0",
        "description": "Enterprise Single Sign-On and SAML Identity Provider Service",
        "status": "healthy",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "saml": {
                "metadata": "/saml/metadata",
                "acs": "/saml/acs",
                "sls": "/saml/sls",
                "login": "/saml/login/{provider_id}"
            },
            "providers": "/providers",
            "mappings": "/mappings"
        }
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
