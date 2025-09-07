"""Game Generation Service - FastAPI Application."""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.config import settings
from app.models import (
    AccessibilitySettings,
    CacheStats,
    HealthResponse,
    ManifestRequest,
    ManifestResponse,
    PerformanceStats,
)
from app.services.cache import template_cache
from app.services.generator import game_generation_service


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan."""
    # Startup
    await template_cache.connect()
    print("Game Generation Service started")

    yield

    # Shutdown
    await template_cache.disconnect()
    print("Game Generation Service stopped")


# Create FastAPI application
app = FastAPI(
    title="Game Generation Service",
    description=(
        "Generate accessible educational games with declarative manifests"
    ),
    version=settings.service_version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="game-gen-svc",
        version=settings.service_version,
        timestamp=time.time()
    )


@app.post("/manifest", response_model=ManifestResponse)
async def generate_game_manifest(
    request: ManifestRequest,
    background_tasks: BackgroundTasks
) -> ManifestResponse:
    """Generate game manifest for learner with accessibility support.

    Creates a declarative game manifest based on learner requirements:
    - Subject-specific game types and content
    - Grade-appropriate difficulty and interaction complexity
    - Accessibility adaptations (A11y toggles)
    - Template caching for ≤1s latency

    Args:
        request: Manifest generation request with learner requirements
        background_tasks: Background task manager for cache warming

    Returns:
        Complete game manifest with scenes, assets, and scoring

    Raises:
        HTTPException: For validation errors or generation failures
    """
    start_time = time.time()

    try:
        # Use grade or default to grade 1
        grade = request.grade or 1

        # Use provided accessibility or defaults
        accessibility = request.accessibility or AccessibilitySettings()

        # Validate request parameters
        if request.duration_minutes < settings.min_game_duration_minutes:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Duration must be at least "
                    f"{settings.min_game_duration_minutes} minutes"
                )
            )

        if request.duration_minutes > settings.max_game_duration_minutes:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Duration cannot exceed "
                    f"{settings.max_game_duration_minutes} minutes"
                )
            )

        # Check cache first for sub-second response
        cached_manifest = await template_cache.get_manifest(
            subject=request.subject.value,
            grade=grade,
            game_type="auto",  # Let service determine optimal type
            duration_minutes=request.duration_minutes,
            accessibility=accessibility.model_dump()
        )

        if cached_manifest:
            generation_time_ms = int((time.time() - start_time) * 1000)
            return ManifestResponse(
                manifest=cached_manifest,
                generation_time_ms=generation_time_ms,
                cache_hit=True,
                learner_id=request.learner_id
            )

        # Generate new manifest
        manifest = await game_generation_service.generate_manifest(
            learner_id=request.learner_id,
            subject=request.subject,
            grade=grade,
            duration_minutes=request.duration_minutes,
            accessibility=accessibility
        )

        # Cache the generated manifest
        await template_cache.store_manifest(
            subject=request.subject.value,
            grade=grade,
            game_type=manifest.game_type.value,
            duration_minutes=request.duration_minutes,
            accessibility=accessibility.model_dump(),
            manifest=manifest
        )

        # Schedule cache warming for related variants
        background_tasks.add_task(
            template_cache.warm_cache,
            request.subject.value,
            grade
        )

        generation_time_ms = int((time.time() - start_time) * 1000)

        # Check if we met the performance target
        if generation_time_ms > settings.target_generation_time_ms:
            print("Generation exceeded target time: %.2fms > %dms",
                  generation_time_ms, settings.target_generation_time_ms)

        return ManifestResponse(
            manifest=manifest,
            generation_time_ms=generation_time_ms,
            cache_hit=False,
            learner_id=request.learner_id
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Validation error: {str(e)}"
        ) from e
    except Exception as e:
        print("Manifest generation error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error during manifest generation"
        ) from e


@app.get("/cache/stats", response_model=CacheStats)
async def get_cache_statistics() -> CacheStats:
    """Get template cache performance statistics."""
    return template_cache.get_cache_stats()


@app.post("/cache/warm")
async def warm_cache(
    subject: str,
    grade: int,
    background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Warm cache for specific subject and grade combinations.

    Pre-generates common game variants for faster response times.
    Useful for preparing cache before peak usage periods.
    """
    try:
        background_tasks.add_task(
            template_cache.warm_cache,
            subject,
            grade
        )
        message = f"Cache warming started for {subject} grade {grade}"
        return {"message": message}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cache warming failed: {str(e)}"
        ) from e


@app.delete("/cache/clear")
async def clear_cache() -> dict[str, str]:
    """Clear expired cache entries."""
    try:
        expired_count = await template_cache.clear_expired()
        return {"message": f"Cleared {expired_count} expired cache entries"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cache clearing failed: {str(e)}"
        ) from e


@app.get("/performance", response_model=PerformanceStats)
async def get_performance_stats() -> PerformanceStats:
    """Get service performance statistics."""
    generator_stats = game_generation_service.get_performance_stats()
    cache_stats = template_cache.get_cache_stats()

    return PerformanceStats(
        total_generations=generator_stats["total_generations"],
        average_generation_time_ms=(
            generator_stats["average_generation_time_ms"]
        ),
        target_time_ms=settings.target_generation_time_ms,
        cache_hit_rate=cache_stats.hit_rate,
        cache_size_bytes=cache_stats.size_bytes,
        service_uptime_seconds=time.time()
    )


@app.get("/subjects/{subject}/games")
async def get_available_games(subject: str, grade: int = 1) -> dict[str, Any]:
    """Get available game types for a specific subject and grade."""
    try:
        game_types = getattr(settings, f"{subject}_game_types", [])

        # Filter based on grade appropriateness
        if grade <= 2:
            appropriate_games = ["matching", "sorting", "memory"]
            game_types = [g for g in game_types if g in appropriate_games]

        return {
            "subject": subject,
            "grade": grade,
            "available_games": game_types,
            "accessibility_features": [
                "reduced_motion", "high_contrast", "large_text",
                "audio_cues", "simplified_ui", "color_blind_friendly"
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available games: {str(e)}"
        ) from e


# Error handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(
    _request: Request, exc: ValidationError
) -> HTTPException:
    """Handle Pydantic validation errors."""
    return HTTPException(
        status_code=422,
        detail=f"Validation error: {str(exc)}"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
