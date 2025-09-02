"""
FastAPI application for Assessment Service.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .enums import SessionStatus
from .schemas import (
    BaselineStartRequest, BaselineStartResponse,
    BaselineAnswerRequest, BaselineAnswerResponse,
    BaselineReportResponse, ErrorResponse
)
from .assessment_engine import assessment_engine
from .event_service import event_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Assessment Service",
    description="Baseline assessment service for L0-L4 subject level evaluation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    logger.error(f"ValueError: {exc}")
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message=str(exc)
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="An internal error occurred"
        ).model_dump()
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "assessment-svc",
        "version": "1.0.0"
    }


@app.post("/baseline/start", response_model=BaselineStartResponse)
async def start_baseline_assessment(request: BaselineStartRequest):
    """
    Start a new baseline assessment session.
    
    This endpoint initiates a baseline assessment for a user in a specific subject.
    Returns the session details and the first question.
    """
    try:
        logger.info(f"Starting baseline assessment for user {request.user_id} in {request.subject}")
        
        # Start assessment session
        session, first_question = assessment_engine.start_assessment(
            request.user_id,
            request.subject
        )
        
        # Publish session started event
        await event_service.publish_session_started(
            session.session_id,
            session.user_id,
            session.subject.value
        )
        
        response = BaselineStartResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            subject=session.subject,
            status=session.status,
            started_at=session.started_at,
            expires_at=session.expires_at,
            first_question=first_question
        )
        
        logger.info(f"Baseline assessment started: session {session.session_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to start baseline assessment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start assessment: {str(e)}"
        )


@app.post("/baseline/answer", response_model=BaselineAnswerResponse)
async def submit_baseline_answer(request: BaselineAnswerRequest):
    """
    Submit an answer for baseline assessment.
    
    This endpoint processes a user's answer, evaluates it, and returns
    the evaluation result along with the next question if the assessment continues.
    """
    try:
        logger.info(f"Submitting answer for session {request.session_id}, question {request.question_id}")
        
        # Submit answer and get evaluation
        evaluation, next_question, is_complete = assessment_engine.submit_answer(
            request.session_id,
            request.question_id,
            request.answer
        )
        
        # Get updated session
        session = assessment_engine.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Publish question answered event
        await event_service.publish_question_answered(
            session.session_id,
            session.user_id,
            request.question_id,
            request.answer,
            evaluation.result.value,
            session.current_level_estimate.value,
            session.confidence
        )
        
        # If assessment is complete, publish baseline complete event
        if is_complete:
            await event_service.publish_baseline_complete(
                session.session_id,
                session.user_id,
                session.subject.value,
                session.current_level_estimate.value,
                session.confidence,
                len(session.questions_answered),
                session.correct_count
            )
        
        response = BaselineAnswerResponse(
            session_id=session.session_id,
            evaluation=evaluation,
            next_question=next_question,
            is_complete=is_complete,
            current_level_estimate=session.current_level_estimate,
            confidence=session.confidence
        )
        
        logger.info(
            f"Answer processed for session {request.session_id}: "
            f"{evaluation.result}, complete: {is_complete}"
        )
        return response
        
    except ValueError as e:
        logger.error(f"Invalid request for answer submission: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit answer: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process answer: {str(e)}"
        )


@app.get("/baseline/report", response_model=BaselineReportResponse)
async def get_baseline_report(sessionId: str):
    """
    Get baseline assessment report.
    
    This endpoint returns the complete assessment report for a given session,
    including the final level assessment and detailed results.
    """
    try:
        logger.info(f"Generating baseline report for session {sessionId}")
        
        # Get session
        session = assessment_engine.get_session(sessionId)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {sessionId} not found"
            )
        
        # Generate baseline report
        result = assessment_engine.get_baseline_report(sessionId)
        
        # Calculate overall summary
        total_questions = len(session.questions_answered)
        accuracy = session.correct_count / total_questions if total_questions > 0 else 0
        duration_minutes = 0
        if session.completed_at and session.started_at:
            duration_minutes = (session.completed_at - session.started_at).total_seconds() / 60
        
        overall_summary = {
            "total_questions": total_questions,
            "total_correct": session.correct_count,
            "accuracy": round(accuracy, 2),
            "assessment_duration_minutes": round(duration_minutes, 1)
        }
        
        response = BaselineReportResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            results=[result],
            overall_summary=overall_summary
        )
        
        logger.info(f"Baseline report generated for session {sessionId}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate baseline report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@app.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Get the current status of an assessment session."""
    session = assessment_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "is_expired": session.is_expired(),
        "is_complete": session.is_complete(),
        "questions_answered": len(session.questions_answered),
        "current_level_estimate": session.current_level_estimate.value,
        "confidence": session.confidence
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Assessment Service",
        "version": "1.0.0",
        "description": "Baseline assessment service for L0-L4 subject level evaluation",
        "endpoints": {
            "start_assessment": "POST /baseline/start",
            "submit_answer": "POST /baseline/answer",
            "get_report": "GET /baseline/report?sessionId=",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
