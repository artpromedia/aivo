"""FastAPI application for ELA Evaluator service."""

import logging
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .evaluator_service import ela_evaluator_service
from .schemas import (
    EvaluationHistoryRequest,
    EvaluationHistoryResponse,
    EvaluationRequest,
    EvaluationResponse,
    HealthResponse,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, str(settings.log_level).upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def _raise_validation_error(message: str) -> None:
    """Raise HTTPException for validation errors."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=message
    )


def _raise_processing_error(message: str) -> None:
    """Raise HTTPException for processing errors."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
    )


def _raise_not_found_error(message: str) -> None:
    """Raise HTTPException for not found errors."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


# Create FastAPI application
app = FastAPI(
    title="ELA Evaluator Service",
    description=(
        "Rubric-based scoring for English Language Arts submissions "
        "with PII moderation and content safety"
    ),
    version=settings.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
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
        service_name=settings.service_name,
        version=settings.service_version,
        timestamp=datetime.now(tz=UTC).isoformat(),
        dependencies={
            "database": "available",
            "redis": "available",
            "ai_models": "available",
        },
    )


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_submission(
    request: EvaluationRequest,
) -> EvaluationResponse:
    """Evaluate ELA submission using rubric scoring with PII moderation.

    Args:
        request: Evaluation request containing prompt, submission, and config

    Returns:
        Evaluation response with rubric scores and safety assessment
    """
    try:
        # Validate submission length
        if len(request.submission) > settings.max_submission_length:
            _raise_validation_error(
                f"Submission too long. Maximum length: "
                f"{settings.max_submission_length} characters"
            )

        # Validate grade band is supported
        if request.grade_band not in settings.supported_grade_bands:
            _raise_validation_error(
                f"Grade band '{request.grade_band}' not supported. "
                f"Supported: {settings.supported_grade_bands}"
            )

        result = await ela_evaluator_service.evaluate_submission(request)

        if not result:
            _raise_processing_error("Failed to process evaluation")
        else:
            return result

    except HTTPException:
        raise
    except (ValueError, RuntimeError) as e:
        logger.exception("Error in evaluation endpoint")
        _raise_processing_error(f"Processing error: {e!s}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error in evaluation endpoint")
        _raise_processing_error(f"Internal server error: {e!s}")


@app.get("/evaluations", response_model=EvaluationHistoryResponse)
async def get_evaluation_history(
    request: EvaluationHistoryRequest,
) -> EvaluationHistoryResponse:
    """Get evaluation history with filtering and pagination.

    Args:
        request: History request with filtering parameters

    Returns:
        Paginated evaluation history
    """
    try:
        result = await ela_evaluator_service.get_evaluation_history(request)

        if result is None:
            _raise_not_found_error("No evaluations found")
        else:
            return result

    except HTTPException:
        raise
    except (ValueError, RuntimeError) as e:
        logger.exception("Error in evaluation history endpoint")
        _raise_processing_error(f"Processing error: {e!s}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error in evaluation history endpoint")
        _raise_processing_error(f"Internal server error: {e!s}")


@app.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation_by_id(evaluation_id: str) -> EvaluationResponse:
    """Get specific evaluation by ID.

    Args:
        evaluation_id: UUID of the evaluation to retrieve

    Returns:
        Complete evaluation details
    """
    try:
        result = await ela_evaluator_service.get_evaluation_by_id(
            evaluation_id
        )

        if result is None:
            _raise_not_found_error(
                f"Evaluation {evaluation_id} not found"
            )
        else:
            return result

    except HTTPException:
        raise
    except (ValueError, RuntimeError) as e:
        logger.exception("Error in get evaluation endpoint")
        _raise_processing_error(f"Processing error: {e!s}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error in get evaluation endpoint")
        _raise_processing_error(f"Internal server error: {e!s}")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "message": (
            "ELA Evaluator Service - Rubric scoring with PII moderation"
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=str(settings.log_level).lower(),
    )
