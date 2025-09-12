"""
FastAPI application for model dispatch service.

Provides REST API for LLM provider selection and policy management.
"""

from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from structlog import configure, get_logger

from app.models import Base, GradeBand, Region, Subject
from app.services.dispatch_service import (
    DispatchRequest,
    ModelDispatchService,
)

# Configure structured logging
configure(
    processors=[],
    wrapper_class=None,
    logger_factory=None,
    cache_logger_on_first_use=True,
)

logger = get_logger(__name__)

# Database setup
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/model_dispatch_db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    yield
    # Cleanup on shutdown
    await engine.dispose()
    logger.info("Application shutdown complete")


# FastAPI app setup
app = FastAPI(
    title="Model Dispatch Service",
    description="LLM provider selection based on subject, grade, and region",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_db_session() -> AsyncSession:
    """Get database session dependency."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_dispatch_service(
    db: AsyncSession = Depends(get_db_session),
) -> ModelDispatchService:
    """Get dispatch service dependency."""
    return ModelDispatchService(db)


# Pydantic models for API
class DispatchRequestAPI(BaseModel):
    """API model for dispatch requests."""

    subject: Subject = Field(..., description="Academic subject")
    grade_band: GradeBand = Field(..., description="Grade band")
    region: Region = Field(..., description="Geographic region")
    teacher_override: bool = Field(False, description="Teacher override flag")
    override_provider_id: UUID | None = Field(None, description="Provider ID for teacher override")
    override_reason: str | None = Field(None, max_length=500, description="Reason for override")


class DispatchResponseAPI(BaseModel):
    """API model for dispatch responses."""

    provider_id: UUID
    provider_name: str
    endpoint_url: str
    template_ids: list[UUID]
    moderation_threshold: float
    policy_id: UUID
    allow_teacher_override: bool
    rate_limits: dict[str, int]
    estimated_cost: dict[str, float]
    request_id: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str


class ProviderInfo(BaseModel):
    """Provider information response."""

    id: str
    name: str
    type: str
    supported_regions: list[str]
    max_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    reliability_score: float


class AnalyticsResponse(BaseModel):
    """Analytics response."""

    total_requests: int
    success_rate: float
    teacher_override_rate: float
    most_used_subjects: dict[str, int]
    most_used_grades: dict[str, int]
    average_response_time_ms: float


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", service="model-dispatch-svc", version="1.0.0")


@app.post("/dispatch", response_model=DispatchResponseAPI)
async def dispatch_model(
    request: DispatchRequestAPI,
    request_id: str = Query(..., description="Unique request identifier"),
    service: ModelDispatchService = Depends(get_dispatch_service),
) -> DispatchResponseAPI:
    """
    Dispatch request to appropriate LLM provider.

    Selects provider based on subject, grade band, and region policies.
    """
    try:
        # Convert API request to service request
        dispatch_request = DispatchRequest(
            subject=request.subject,
            grade_band=request.grade_band,
            region=request.region,
            teacher_override=request.teacher_override,
            override_provider_id=request.override_provider_id,
            override_reason=request.override_reason,
            request_id=request_id,
        )

        # Get dispatch response
        response = await service.dispatch_request(dispatch_request)

        # Convert service response to API response
        return DispatchResponseAPI(
            provider_id=response.provider_id,
            provider_name=response.provider_name,
            endpoint_url=response.endpoint_url,
            template_ids=response.template_ids,
            moderation_threshold=response.moderation_threshold,
            policy_id=response.policy_id,
            allow_teacher_override=response.allow_teacher_override,
            rate_limits=response.rate_limits,
            estimated_cost=response.estimated_cost,
            request_id=request_id,
        )

    except ValueError as e:
        logger.error("Dispatch failed", error=str(e), request_id=request_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error in dispatch", error=str(e), request_id=request_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/providers", response_model=list[ProviderInfo])
async def get_providers(
    region: Region = Query(..., description="Region to filter providers"),
    service: ModelDispatchService = Depends(get_dispatch_service),
) -> list[ProviderInfo]:
    """Get available providers for a region."""
    try:
        providers_data = await service.get_available_providers(region)
        return [ProviderInfo(**provider) for provider in providers_data]
    except Exception as e:
        logger.error("Failed to get providers", error=str(e), region=region)
        raise HTTPException(status_code=500, detail="Failed to retrieve providers")


@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    region: Region | None = Query(None, description="Filter by region"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    service: ModelDispatchService = Depends(get_dispatch_service),
) -> AnalyticsResponse:
    """Get dispatch analytics and metrics."""
    try:
        analytics_data = await service.get_dispatch_analytics(region=region, days=days)
        return AnalyticsResponse(**analytics_data)
    except Exception as e:
        logger.error("Failed to get analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@app.get("/subjects", response_model=list[str])
async def get_subjects() -> list[str]:
    """Get list of available subjects."""
    return [subject.value for subject in Subject]


@app.get("/grade-bands", response_model=list[str])
async def get_grade_bands() -> list[str]:
    """Get list of available grade bands."""
    return [grade.value for grade in GradeBand]


@app.get("/regions", response_model=list[str])
async def get_regions() -> list[str]:
    """Get list of available regions."""
    return [region.value for region in Region]


@app.get("/policies/validate")
async def validate_policy(
    subject: Subject = Query(..., description="Subject to validate"),
    grade_band: GradeBand = Query(..., description="Grade band to validate"),
    region: Region = Query(..., description="Region to validate"),
    service: ModelDispatchService = Depends(get_dispatch_service),
) -> dict[str, any]:
    """Validate that a policy exists for the given parameters."""
    try:
        # Create a test dispatch request
        test_request = DispatchRequest(
            subject=subject,
            grade_band=grade_band,
            region=region,
            request_id="validation_test",
        )

        # Try to get a dispatch response
        response = await service.dispatch_request(test_request)

        return {
            "valid": True,
            "policy_id": str(response.policy_id),
            "provider_name": response.provider_name,
            "moderation_threshold": response.moderation_threshold,
            "allow_teacher_override": response.allow_teacher_override,
        }

    except ValueError as e:
        return {
            "valid": False,
            "error": str(e),
            "suggestion": "Create a dispatch policy for this combination",
        }
    except Exception as e:
        logger.error("Policy validation error", error=str(e))
        raise HTTPException(status_code=500, detail="Validation failed")


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    logger.warning("ValueError in request", error=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return HTTPException(status_code=404, detail="Resource not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)
