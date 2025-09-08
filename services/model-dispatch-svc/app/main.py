"""Model Dispatch Policy Service - FastAPI Application."""

import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    HealthResponse,
    OverrideResponse,
    PolicyRequest,
    PolicyResponse,
    PolicyStats,
    TeacherOverride,
)
from app.services.cache_service import cache_service
from app.services.policy_engine import policy_engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage application lifespan."""
    # Startup
    await cache_service.connect()
    await policy_engine.initialize()
    print("Model Dispatch Policy Service started")

    yield

    # Shutdown
    await cache_service.disconnect()
    print("Model Dispatch Policy Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Model Dispatch Policy Service",
    description=(
        "LLM provider routing by subject/grade/region "
        "with data residency enforcement"
    ),
    version=settings.service_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    stats = await policy_engine.get_stats()
    return HealthResponse(
        status="healthy",
        service="model-dispatch-svc",
        version=settings.service_version,
        timestamp=time.time(),
        rules_loaded=stats.get("rules_count", 0),
    )


@app.post("/policy", response_model=PolicyResponse)
async def get_policy(request: PolicyRequest) -> PolicyResponse:
    """Get LLM provider routing policy for the given parameters."""
    try:
        # Check cache first
        cached_response = await cache_service.get_policy(request)
        if cached_response:
            return cached_response

        # Get policy from engine
        response = await policy_engine.get_policy(request)

        # Cache the response
        await cache_service.set_policy(request, response)

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get policy: {str(e)}"
        ) from e


@app.post("/override", response_model=OverrideResponse)
async def create_teacher_override(
    override: TeacherOverride,
) -> OverrideResponse:
    """Create a teacher override for LLM provider selection."""
    try:
        override_id = await policy_engine.add_teacher_override(override)

        # Calculate expiration time
        expires_at = datetime.now() + timedelta(hours=override.duration_hours)

        return OverrideResponse(
            override_id=override_id,
            expires_at=expires_at,
            applied=True,
            message=(
                f"Override created successfully for "
                f"{override.duration_hours} hours"
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create override: {str(e)}"
        ) from e


@app.get("/stats", response_model=PolicyStats)
async def get_stats() -> PolicyStats:
    """Get policy dispatch statistics."""
    try:
        engine_stats = await policy_engine.get_stats()
        cache_stats = await cache_service.get_stats()

        return PolicyStats(
            total_requests=engine_stats["total_requests"],
            cache_hits=cache_stats["hits"],
            cache_misses=cache_stats["misses"],
            provider_distribution=engine_stats["provider_distribution"],
            region_distribution=engine_stats["region_distribution"],
            average_response_time_ms=engine_stats["average_response_time_ms"],
            rules_count=engine_stats["rules_count"],
            last_updated=engine_stats["last_updated"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        ) from e


@app.post("/cache/clear")
async def clear_cache(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Clear policy cache."""
    try:
        background_tasks.add_task(cache_service.clear_all)
        return {"message": "Cache clear initiated"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clear cache: {str(e)}"
        ) from e


@app.post("/cache/invalidate/subject/{subject}")
async def invalidate_subject_cache(
    subject: str, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Invalidate cache for a specific subject."""
    try:
        background_tasks.add_task(cache_service.invalidate_subject, subject)
        return {
            "message": f"Cache invalidation initiated for subject: {subject}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate cache: {str(e)}"
        ) from e


@app.post("/cache/invalidate/region/{region}")
async def invalidate_region_cache(
    region: str, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Invalidate cache for a specific region."""
    try:
        background_tasks.add_task(cache_service.invalidate_region, region)
        return {
            "message": f"Cache invalidation initiated for region: {region}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate cache: {str(e)}"
        ) from e


@app.post("/config/reload")
async def reload_config() -> dict[str, Any]:
    """Reload policy configuration."""
    try:
        success = await policy_engine.reload_config()
        return {
            "success": success,
            "message": (
                "Configuration reloaded successfully"
                if success
                else "Reload failed"
            ),
            "timestamp": time.time(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reload config: {str(e)}"
        ) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=str(settings.log_level).lower(),
    )
