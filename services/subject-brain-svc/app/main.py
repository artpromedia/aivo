"""Subject-Brain Service FastAPI application."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import (
    PlannerRequest,
    PlannerResponse,
    RuntimeStatusResponse,
)
from .services.runtime_manager import runtime_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting Subject-Brain Service")

    # Initialize Kubernetes HPA
    try:
        await runtime_manager.create_hpa()
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to create HPA: %s", e)

    yield

    logger.info("Shutting down Subject-Brain Service")


# Create FastAPI application
app = FastAPI(
    title="Subject-Brain Service",
    description=("AI-powered planner and runtime for " "per-learner-subject GPU pods"),
    version=settings.service_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "subject-brain-svc",
        "version": settings.service_version,
    }


@app.get("/metrics")
async def get_metrics() -> dict[str, dict[str, int] | dict[str, int]]:
    """Get service metrics for monitoring."""
    try:
        scaling_metrics = await runtime_manager.get_scaling_metrics()
        return {
            "service_metrics": {
                "active_runtimes": len(runtime_manager.active_runtimes),
                "total_pods": scaling_metrics["active_runtimes"],
            },
            "scaling_metrics": scaling_metrics,
        }
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to get metrics: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get metrics") from e


@app.post("/plan", response_model=PlannerResponse)
async def create_activity_plan(request: PlannerRequest) -> PlannerResponse:
    """Create a personalized activity plan for a learner."""
    try:
        logger.info(
            "Creating plan for learner %s in %s",
            request.learner_id,
            request.subject,
        )

        # TODO: In a real implementation, we would:  # pylint: disable=fixme
        # 1. Fetch learner baseline from learner service
        # 2. Get available coursework topics from coursework service
        # 3. Retrieve teacher constraints from auth/profile service

        # For now, create a mock planner input
        # This would be replaced with actual service calls
        raise HTTPException(
            status_code=501,
            detail=("Plan creation requires integration with other services"),
        )

    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to create plan: %s", e)
        raise HTTPException(
            status_code=500, detail="Internal server error while creating plan"
        ) from e


@app.get("/runtime/{runtime_id}", response_model=RuntimeStatusResponse)
async def get_runtime_status(runtime_id: str) -> RuntimeStatusResponse:
    """Get the current status of a runtime."""
    try:
        runtime_pod = await runtime_manager.get_runtime_status(runtime_id)

        if not runtime_pod:
            raise HTTPException(status_code=404, detail=f"Runtime {runtime_id} not found")

        return RuntimeStatusResponse(
            runtime_id=runtime_pod.runtime_id,
            status=runtime_pod.status,
            metrics=runtime_pod.metrics,
            # pylint: disable-next=fixme
            estimated_completion_minutes=None,  # TODO: Calculate based on plan
            # pylint: disable-next=fixme
            current_activity=None,  # TODO: Get from runtime pod
        )

    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to get runtime status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get runtime status") from e


@app.delete("/runtime/{runtime_id}")
async def terminate_runtime(runtime_id: str) -> dict[str, str]:
    """Manually terminate a runtime."""
    try:
        runtime_pod = await runtime_manager.get_runtime_status(runtime_id)

        if not runtime_pod:
            raise HTTPException(status_code=404, detail=f"Runtime {runtime_id} not found")

        await runtime_manager.terminate_runtime(runtime_id)

        return {
            "message": f"Runtime {runtime_id} termination initiated",
            "status": "terminating",
        }

    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to terminate runtime: %s", e)
        raise HTTPException(status_code=500, detail="Failed to terminate runtime") from e


@app.post("/cleanup")
async def cleanup_idle_runtimes() -> dict[str, str | list[str] | int]:
    """Manually trigger cleanup of idle runtimes."""
    try:
        cleaned_up = await runtime_manager.cleanup_idle_runtimes()

        return {
            "message": "Cleanup completed",
            "cleaned_up_runtimes": cleaned_up,
            "count": len(cleaned_up),
        }

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to cleanup runtimes: %s", e)
        raise HTTPException(status_code=500, detail="Failed to cleanup runtimes") from e


@app.get("/")
async def root() -> dict[str, str | dict[str, str]]:
    """Root endpoint with service information."""
    return {
        "service": "subject-brain-svc",
        "description": ("AI-powered planner and runtime for per-learner-subject GPU pods"),
        "version": settings.service_version,
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "create_plan": "POST /plan",
            "get_runtime": "GET /runtime/{runtime_id}",
            "terminate_runtime": "DELETE /runtime/{runtime_id}",
            "cleanup": "POST /cleanup",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
