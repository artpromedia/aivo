"""
Admin Portal Aggregator Service - Main FastAPI application.
"""
# pylint: disable=import-error

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace  # type: ignore[import-untyped]
from opentelemetry.instrumentation.fastapi import (  # type: ignore[import-untyped]  # noqa: E501
    FastAPIInstrumentor,
)

from .cache_service import cache_service
from .config import get_settings
from .http_client import http_client
from .schemas import (
    BillingHistoryResponse,
    ErrorResponse,
    HealthCheckResponse,
    NamespacesResponse,
    SubscriptionDetails,
    SummaryResponse,
    TeamResponse,
    UsageResponse,
)
from .service_aggregator import service_aggregator
from .routes_rbac import router as rbac_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
tracer = trace.get_tracer(__name__)


@asynccontextmanager
# pylint: disable=unused-argument,redefined-outer-name
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Admin Portal Aggregator Service...")

    # Initialize services
    await cache_service.initialize()
    await http_client.initialize()

    logger.info("Admin Portal Aggregator Service started successfully")
    yield

    # Cleanup
    await cache_service.close()
    await http_client.close()
    logger.info("Admin Portal Aggregator Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Admin Portal Aggregator Service",
    description="Dashboard data aggregation service for admin portal",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenTelemetry instrumentation
FastAPIInstrumentor.instrument_app(app)

# Include RBAC router
app.include_router(rbac_router)


# Dependency for tenant ID validation
async def get_tenant_id(
    tenant_id: str = Query(..., description="Tenant identifier"),
) -> str:
    """Validate and return tenant ID."""
    if not tenant_id or len(tenant_id) < 3:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")
    return tenant_id


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    with tracer.start_as_current_span("health_check") as span:
        # Check dependencies
        dependencies = {"cache": "unknown", "http_client": "unknown"}

        # Check cache status
        try:
            cache_stats = await cache_service.get_stats()
            dependencies["cache"] = cache_stats.get("status", "unknown")
        except Exception as e:  # pylint: disable=broad-exception-caught
            dependencies["cache"] = f"error: {str(e)}"

        # Check HTTP client circuit breakers
        try:
            cb_status = http_client.get_circuit_breaker_status()
            all_closed = all(cb["state"] == "closed" for cb in cb_status.values())
            dependencies["http_client"] = "ok" if all_closed else "degraded"
        except Exception as e:  # pylint: disable=broad-exception-caught
            dependencies["http_client"] = f"error: {str(e)}"

        span.set_attributes(
            {
                "health.cache_status": dependencies["cache"],
                "health.http_client_status": dependencies["http_client"],
            }
        )

        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            dependencies=dependencies,
            cache_status=dependencies["cache"],
        )


@app.get("/summary", response_model=SummaryResponse)
async def get_summary(tenant_id: str = Depends(get_tenant_id)):
    """Get dashboard summary data."""
    with tracer.start_as_current_span("get_summary") as span:
        span.set_attribute("tenant.id", tenant_id)

        try:
            summary = await service_aggregator.get_summary(tenant_id)
            span.set_attribute("summary.health_score", summary.health_score)
            return summary
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to get summary for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve summary data: {str(e)}",
            ) from e


@app.get("/subscription", response_model=SubscriptionDetails)
async def get_subscription(tenant_id: str = Depends(get_tenant_id)):
    """Get subscription details."""
    with tracer.start_as_current_span("get_subscription") as span:
        span.set_attribute("tenant.id", tenant_id)

        try:
            subscription = await service_aggregator.get_subscription(tenant_id)
            span.set_attribute("subscription.tier", subscription.current_tier)
            return subscription
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to get subscription for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve subscription data: {str(e)}",
            ) from e


@app.get("/billing-history", response_model=BillingHistoryResponse)
async def get_billing_history(tenant_id: str = Depends(get_tenant_id)):
    """Get billing history."""
    with tracer.start_as_current_span("get_billing_history") as span:
        span.set_attribute("tenant.id", tenant_id)

        try:
            billing = await service_aggregator.get_billing_history(tenant_id)
            span.set_attribute("billing.invoice_count", len(billing.invoices))
            return billing
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to get billing history for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve billing history: {str(e)}",
            ) from e


@app.get("/team", response_model=TeamResponse)
async def get_team(tenant_id: str = Depends(get_tenant_id)):
    """Get team information."""
    with tracer.start_as_current_span("get_team") as span:
        span.set_attribute("tenant.id", tenant_id)

        try:
            team = await service_aggregator.get_team(tenant_id)
            span.set_attribute("team.total_members", team.total_members)
            return team
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to get team for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve team data: {str(e)}",
            ) from e


@app.get("/usage", response_model=UsageResponse)
async def get_usage(tenant_id: str = Depends(get_tenant_id)):
    """Get usage metrics."""
    with tracer.start_as_current_span("get_usage") as span:
        span.set_attribute("tenant.id", tenant_id)

        try:
            usage = await service_aggregator.get_usage(tenant_id)
            span.set_attribute("usage.api_calls", usage.total_api_calls)
            span.set_attribute("usage.storage_gb", usage.total_storage_gb)
            return usage
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to get usage for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve usage data: {str(e)}",
            ) from e


@app.get("/namespaces", response_model=NamespacesResponse)
async def get_namespaces(tenant_id: str = Depends(get_tenant_id)):
    """Get namespaces information."""
    with tracer.start_as_current_span("get_namespaces") as span:
        span.set_attribute("tenant.id", tenant_id)

        try:
            namespaces = await service_aggregator.get_namespaces(tenant_id)
            span.set_attribute("namespaces.total", namespaces.total_namespaces)
            span.set_attribute("namespaces.storage_gb", namespaces.total_storage_gb)
            return namespaces
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to get namespaces for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve namespaces data: {str(e)}",
            ) from e


@app.delete("/cache/{tenant_id}")
async def clear_tenant_cache(tenant_id: str):
    """Clear cache for a specific tenant."""
    with tracer.start_as_current_span("clear_tenant_cache") as span:
        span.set_attribute("tenant.id", tenant_id)

        try:
            cleared_count = await cache_service.clear_tenant(tenant_id)
            span.set_attribute("cache.cleared_count", cleared_count)

            message = f"Cleared {cleared_count} cache entries for tenant {tenant_id}"
            return {
                "message": message,
                "tenant_id": tenant_id,
                "cleared_count": cleared_count,
            }
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to clear cache for tenant %s: %s", tenant_id, e)
            raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}") from e


@app.get("/circuit-breakers")
async def get_circuit_breaker_status():
    """Get circuit breaker status for all services."""
    with tracer.start_as_current_span("get_circuit_breaker_status"):
        try:
            status = http_client.get_circuit_breaker_status()
            return {"circuit_breakers": status, "timestamp": datetime.utcnow()}
        except Exception as e:
            logger.error("Failed to get circuit breaker status: %s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve circuit breaker status: {str(e)}",
            ) from e


@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    with tracer.start_as_current_span("get_cache_stats"):
        try:
            stats = await cache_service.get_stats()
            return {"cache_stats": stats, "timestamp": datetime.utcnow()}
        except Exception as e:
            logger.error("Failed to get cache stats: %s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve cache stats: {str(e)}",
            ) from e


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,  # pylint: disable=unused-argument
    exc: Exception,
) -> JSONResponse:
    """Global exception handler."""
    logger.error("Unhandled exception: %s", exc)
    return ErrorResponse(
        error="internal_server_error",
        message="An internal server error occurred",
        details={"exception": str(exc)},
        timestamp=datetime.utcnow(),
    ).dict()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


# Team Management Endpoints


@app.post("/team/role-assign")
async def assign_team_role(
    request: dict,
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    """Assign role to team member via auth service."""
    with tracer.start_as_current_span("assign_team_role") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("user.id", request.get("user_id"))
        span.set_attribute("role", request.get("role"))

        try:
            # Validate request
            if not all(k in request for k in ["user_id", "tenant_id", "role"]):
                raise HTTPException(
                    status_code=400, detail="Missing required fields: user_id, tenant_id, role"
                )

            # Proxy to auth service
            response = await http_client.post(
                f"auth-svc/users/{request['user_id']}/roles",
                json={"tenant_id": request["tenant_id"], "role": request["role"]},
            )

            if response.status_code == 200:
                span.set_attribute("operation.success", True)
                return response.json()
            else:
                error_detail = response.json().get("detail", "Role assignment failed")
                raise HTTPException(status_code=response.status_code, detail=error_detail)

        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to assign role for tenant %s: %s", tenant_id, e)
            raise HTTPException(status_code=500, detail=f"Failed to assign role: {str(e)}") from e


@app.post("/team/role-revoke")
async def revoke_team_role(
    request: dict,
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    """Revoke role from team member via auth service."""
    with tracer.start_as_current_span("revoke_team_role") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("user.id", request.get("user_id"))
        span.set_attribute("role", request.get("role"))

        try:
            # Validate request
            if not all(k in request for k in ["user_id", "tenant_id", "role"]):
                raise HTTPException(
                    status_code=400, detail="Missing required fields: user_id, tenant_id, role"
                )

            # Proxy to auth service
            response = await http_client.delete(
                f"auth-svc/users/{request['user_id']}/roles",
                json={"tenant_id": request["tenant_id"], "role": request["role"]},
            )

            if response.status_code == 200:
                span.set_attribute("operation.success", True)
                return response.json()
            else:
                error_detail = response.json().get("detail", "Role revocation failed")
                raise HTTPException(status_code=response.status_code, detail=error_detail)

        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to revoke role for tenant %s: %s", tenant_id, e)
            raise HTTPException(status_code=500, detail=f"Failed to revoke role: {str(e)}") from e


@app.post("/team/invite-resend")
async def resend_team_invite(
    request: dict,
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    """Resend invitation via auth service."""
    with tracer.start_as_current_span("resend_team_invite") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("invite.id", request.get("invite_id"))

        try:
            # Validate request
            if "invite_id" not in request:
                raise HTTPException(status_code=400, detail="Missing required field: invite_id")

            # Proxy to auth service
            response = await http_client.post(f"auth-svc/invites/{request['invite_id']}/resend")

            if response.status_code == 200:
                span.set_attribute("operation.success", True)
                return response.json()
            else:
                error_detail = response.json().get("detail", "Invite resend failed")
                raise HTTPException(status_code=response.status_code, detail=error_detail)

        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to resend invite for tenant %s: %s", tenant_id, e)
            raise HTTPException(status_code=500, detail=f"Failed to resend invite: {str(e)}") from e
