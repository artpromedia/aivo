"""Main FastAPI application for Problem Session Orchestrator."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db
from .models import ProblemSession
from .schemas import (
    HealthResponse,
    InkSubmissionRequest,
    InkSubmissionResponse,
    SessionResponse,
    StartSessionRequest,
)
from .services import orchestrator

# Configure logging
logging.basicConfig(level=getattr(logging, str(settings.log_level).upper()))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Problem Session Orchestrator",
    description=(
        "Coordinates interactive learning sessions across multiple "
        "subject-specific services including ink capture, math recognition, "
        "and science solving"
    ),
    version="0.1.0",
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        timestamp=datetime.utcnow(),
        dependencies={
            "database": "healthy",
            "ink_service": "unknown",
            "math_service": "unknown",
            "science_service": "unknown",
            "subject_brain": "unknown",
        },
    )


@app.post("/start", response_model=SessionResponse)
async def start_session(
    request: StartSessionRequest, db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """Start a new problem session.

    Coordinates plan→present→ink→recognize→grade→feedback workflow.
    """
    try:
        logger.info(
            "Starting new problem session",
            learner_id=request.learner_id,
            subject=request.subject,
            duration=request.session_duration_minutes,
        )

        # Start the orchestrated session
        session = await orchestrator.start_session(
            learner_id=request.learner_id,
            subject=request.subject,
            session_duration_minutes=request.session_duration_minutes,
            canvas_width=request.canvas_width,
            canvas_height=request.canvas_height,
            db=db,
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start session",
            )

        return _session_to_response(session)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to start session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e!s}",
        ) from e


@app.post("/ink", response_model=InkSubmissionResponse)
async def submit_ink(
    request: InkSubmissionRequest, db: AsyncSession = Depends(get_db)
) -> InkSubmissionResponse:
    """Submit ink for recognition and processing."""
    try:
        logger.info(
            "Submitting ink for processing",
            session_id=request.session_id,
            page_number=request.page_number,
            stroke_count=len(request.strokes),
        )

        # Submit ink through orchestrator
        ink_response = await orchestrator.submit_ink(
            session_id=request.session_id,
            page_number=request.page_number,
            strokes=request.strokes,
            metadata=request.metadata,
            db=db,
        )

        if not ink_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to submit ink",
            )

        return ink_response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to submit ink")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e!s}",
        ) from e


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID, db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """Get session status and details."""
    try:
        result = await db.execute(
            select(ProblemSession).where(
                ProblemSession.session_id == session_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        return _session_to_response(session)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e!s}",
        ) from e


@app.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: UUID, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """Manually complete a session."""
    try:
        logger.info("Manually completing session", session_id=session_id)

        await orchestrator.complete_session(session_id, db)

        return {"status": "completed", "session_id": str(session_id)}

    except Exception as e:
        logger.exception("Failed to complete session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e!s}",
        ) from e


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "Problem Session Orchestrator",
        "version": "0.1.0",
        "description": (
            "Coordinates interactive learning sessions across multiple "
            "subject-specific services"
        ),
    }


def _session_to_response(session: ProblemSession) -> SessionResponse:
    """Convert database session to response model."""
    current_activity = None
    if session.planned_activities and session.current_activity_index >= 0:
        activities = session.planned_activities.get("activities", [])
        if session.current_activity_index < len(activities):
            current_activity = activities[session.current_activity_index]

    return SessionResponse(
        session_id=session.session_id,
        learner_id=session.learner_id,
        subject=session.subject,
        status=session.status,
        current_phase=session.current_phase,
        created_at=session.created_at,
        started_at=session.started_at,
        completed_at=session.completed_at,
        session_duration_minutes=session.session_duration_minutes,
        total_problems_attempted=session.total_problems_attempted,
        total_problems_correct=session.total_problems_correct,
        average_confidence=session.average_confidence,
        current_activity=current_activity,
        canvas_width=session.canvas_width,
        canvas_height=session.canvas_height,
        ink_session_id=session.ink_session_id,
        error_message=session.error_message,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=str(settings.log_level).lower(),
    )
