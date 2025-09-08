"""
FastAPI application for Inference Gateway service.
"""

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .openai_service import openai_service
from .schemas import (
    EmbeddingRequest,
    EmbeddingResponse,
    ErrorResponse,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    ModerationRequest,
    ModerationResponse,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting Inference Gateway service")
    yield
    logger.info("Shutting down Inference Gateway service")


# Create FastAPI application
app = FastAPI(
    title="Inference Gateway Service",
    description="OpenAI integration with content moderation and PII scrubbing",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Test OpenAI API connectivity
        openai_status = "healthy"
        try:
            # Simple API test
            models = openai_service.client.models.list()
            if not models.data:
                openai_status = "unhealthy"
        except Exception as e:
            logger.warning(f"OpenAI API test failed: {e}")
            openai_status = "unhealthy"

        dependencies = {"openai": openai_status, "pii_service": "healthy", "moderation": "healthy"}

        overall_status = (
            "healthy"
            if all(status == "healthy" for status in dependencies.values())
            else "degraded"
        )

        return HealthResponse(
            status=overall_status,
            service="inference-gateway",
            version="1.0.0",
            timestamp=datetime.now(UTC),
            dependencies=dependencies,
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unhealthy"
        )


@app.post("/v1/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """
    Generate text using OpenAI's completion API with moderation and PII scrubbing.

    This endpoint provides educational content generation with built-in safety measures:
    - Content moderation to block harmful content
    - PII detection and scrubbing to protect privacy
    - Educational context envelope for subject/grade awareness
    """
    try:
        logger.info(f"Text generation request: model={request.model}, context={request.context}")

        response = await openai_service.generate_text(request)

        # Log moderation and PII results
        logger.info(
            f"Generation completed: moderation={response.moderation_result}, "
            f"pii_detected={response.pii_detected}, pii_scrubbed={response.pii_scrubbed}"
        )

        return response

    except Exception as e:
        logger.error(f"Text generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text generation failed: {str(e)}",
        )


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """
    Generate embeddings using OpenAI's embeddings API with PII scrubbing.

    This endpoint creates vector embeddings for educational content with:
    - PII detection and scrubbing to protect sensitive information
    - Educational context awareness for subject-specific embeddings
    """
    try:
        logger.info(f"Embedding request: model={request.model}, context={request.context}")

        response = await openai_service.generate_embeddings(request)

        logger.info(
            f"Embeddings completed: pii_detected={response.pii_detected}, "
            f"pii_scrubbed={response.pii_scrubbed}"
        )

        return response

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}",
        )


@app.post("/v1/moderate", response_model=ModerationResponse)
async def moderate_content(request: ModerationRequest):
    """
    Moderate content using OpenAI's moderation API.

    This endpoint provides content safety checking with:
    - Configurable thresholds for educational content
    - Category-specific scoring for different types of harmful content
    """
    try:
        logger.info(f"Moderation request: model={request.model}, threshold={request.threshold}")

        response = await openai_service.moderate_content(request)

        # Log moderation results
        blocked_count = sum(1 for result in response.results if result.flagged)
        logger.info(f"Moderation completed: {blocked_count}/{len(response.results)} blocked")

        return response

    except Exception as e:
        logger.error(f"Content moderation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content moderation failed: {str(e)}",
        )


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    error_response = ErrorResponse(
        error="HTTP Error", message=exc.detail, timestamp=datetime.now(UTC)
    )
    return JSONResponse(status_code=exc.status_code, content=error_response.model_dump(mode="json"))


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    error_response = ErrorResponse(
        error="Server Error",
        message=f"An unexpected error occurred: {exc}",
        timestamp=datetime.now(UTC),
    )
    return JSONResponse(status_code=500, content=error_response.model_dump(mode="json"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
