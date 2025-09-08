"""FastAPI application for Math Recognizer service."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .recognition_service import math_recognition_service
from .schemas import (
    GradeRequest,
    GradeResponse,
    HealthResponse,
    InkData,
    RecognitionRequest,
    RecognitionResponse,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, str(settings.log_level).upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Math Recognizer Service",
    description=(
        "Convert digital ink to LaTeX/AST and grade "
        "mathematical expressions"
    ),
    version=settings.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
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
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service_name=settings.service_name,
        version=settings.service_version,
        timestamp=datetime.now(tz=UTC).isoformat(),
        dependencies={
            "ink_service": "unknown",  # Could ping ink service here
            "cas_service": "available",
        },
    )


@app.post("/recognize/{session_id}", response_model=RecognitionResponse)
async def recognize_math(
    session_id: UUID,
    page_number: int = 1,
    region_x: float | None = None,
    region_y: float | None = None,
    region_width: float | None = None,
    region_height: float | None = None,
) -> RecognitionResponse:
    """Recognize mathematical expression from ink session.

    Args:
        session_id: Ink session identifier
        page_number: Page number to recognize (default: 1)
        region_x: Optional bounding box X coordinate
        region_y: Optional bounding box Y coordinate
        region_width: Optional bounding box width
        region_height: Optional bounding box height

    Returns:
        Recognition result with LaTeX, AST, and confidence
    """
    try:
        # Build region if coordinates provided
        region = None
        if all(
            x is not None
            for x in [region_x, region_y, region_width, region_height]
        ):
            region = {
                "x": region_x,
                "y": region_y,
                "width": region_width,
                "height": region_height,
            }

        request = RecognitionRequest(
            session_id=session_id,
            page_number=page_number,
            region=region,
        )

        result = await math_recognition_service.recognize_from_session(request)

        if not result.success and result.error_message:
            # Return specific HTTP status codes based on error type
            if "not found" in result.error_message.lower():
                raise HTTPException(
                    status_code=404, detail=result.error_message,
                )
            if "timeout" in result.error_message.lower():
                raise HTTPException(
                    status_code=408, detail=result.error_message,
                )
            raise HTTPException(
                status_code=400, detail=result.error_message,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in math recognition endpoint")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}",
        ) from e


@app.post("/recognize", response_model=RecognitionResponse)
async def recognize_math_from_ink(ink_data: InkData) -> RecognitionResponse:
    """Recognize mathematical expression from direct ink data.

    Args:
        ink_data: Digital ink stroke data

    Returns:
        Recognition result with LaTeX, AST, and confidence
    """
    try:
        result = await math_recognition_service.recognize_from_ink(ink_data)

        if not result.success and result.error_message:
            if "timeout" in result.error_message.lower():
                raise HTTPException(
                    status_code=408, detail=result.error_message,
                )
            raise HTTPException(
                status_code=400, detail=result.error_message,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in direct ink recognition endpoint")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}",
        ) from e


@app.post("/grade", response_model=GradeResponse)
async def grade_expression(request: GradeRequest) -> GradeResponse:
    """Grade mathematical expressions for correctness and equivalence.

    Args:
        request: Grading request with student and correct expressions

    Returns:
        Grading result with score, feedback, and optional steps
    """
    try:
        return await math_recognition_service.grade_expression(request)

    except Exception as e:
        logger.exception("Error in grading endpoint")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}",
        ) from e


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "message": (
            "Math Recognizer Service - Convert ink to LaTeX/AST "
            "and grade expressions"
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
