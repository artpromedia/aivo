"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from .enums import SubjectType, LevelType, SessionStatus, QuestionType, AnswerResult, EventType


class BaselineStartRequest(BaseModel):
    """Request to start baseline assessment."""
    user_id: str = Field(..., description="User identifier")
    subject: SubjectType = Field(..., description="Subject to assess")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user123",
                "subject": "mathematics"
            }
        }
    )


class BaselineStartResponse(BaseModel):
    """Response for baseline assessment start."""
    session_id: str = Field(..., description="Assessment session ID")
    user_id: str = Field(..., description="User identifier")
    subject: SubjectType = Field(..., description="Subject being assessed")
    status: SessionStatus = Field(..., description="Session status")
    started_at: datetime = Field(..., description="Session start time")
    expires_at: datetime = Field(..., description="Session expiration time")
    first_question: "Question" = Field(..., description="First assessment question")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "sess_123",
                "user_id": "user123",
                "subject": "mathematics",
                "status": "active",
                "started_at": "2025-09-02T10:00:00Z",
                "expires_at": "2025-09-02T12:00:00Z",
                "first_question": {
                    "question_id": "q1",
                    "text": "What is 2 + 2?",
                    "type": "multiple_choice",
                    "options": ["2", "3", "4", "5"],
                    "estimated_level": "L1"
                }
            }
        }
    )


class Question(BaseModel):
    """Assessment question."""
    question_id: str = Field(..., description="Question identifier")
    text: str = Field(..., description="Question text")
    type: QuestionType = Field(..., description="Question type")
    options: Optional[List[str]] = Field(None, description="Multiple choice options")
    estimated_level: LevelType = Field(..., description="Estimated difficulty level")
    subject: Optional[SubjectType] = Field(None, description="Question subject")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "q1",
                "text": "What is the result of 15 ÷ 3?",
                "type": "multiple_choice",
                "options": ["3", "4", "5", "6"],
                "estimated_level": "L2",
                "subject": "mathematics"
            }
        }
    )


class BaselineAnswerRequest(BaseModel):
    """Request to submit answer for baseline assessment."""
    session_id: str = Field(..., description="Assessment session ID")
    question_id: str = Field(..., description="Question being answered")
    answer: Union[str, int, bool] = Field(..., description="User's answer")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "sess_123",
                "question_id": "q1",
                "answer": "4"
            }
        }
    )


class AnswerEvaluation(BaseModel):
    """Answer evaluation result."""
    question_id: str = Field(..., description="Question identifier")
    user_answer: Union[str, int, bool] = Field(..., description="User's answer")
    correct_answer: Union[str, int, bool] = Field(..., description="Correct answer")
    result: AnswerResult = Field(..., description="Evaluation result")
    explanation: Optional[str] = Field(None, description="Answer explanation")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "q1",
                "user_answer": "4",
                "correct_answer": "4",
                "result": "correct",
                "explanation": "Correct! 2 + 2 = 4"
            }
        }
    )


class BaselineAnswerResponse(BaseModel):
    """Response for baseline answer submission."""
    session_id: str = Field(..., description="Assessment session ID")
    evaluation: AnswerEvaluation = Field(..., description="Answer evaluation")
    next_question: Optional[Question] = Field(None, description="Next question if available")
    is_complete: bool = Field(..., description="Whether assessment is complete")
    current_level_estimate: Optional[LevelType] = Field(None, description="Current level estimate")
    confidence: Optional[float] = Field(None, description="Confidence in level estimate")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "sess_123",
                "evaluation": {
                    "question_id": "q1",
                    "user_answer": "4",
                    "correct_answer": "4",
                    "result": "correct",
                    "explanation": "Correct!"
                },
                "next_question": {
                    "question_id": "q2",
                    "text": "What is 8 × 7?",
                    "type": "multiple_choice",
                    "options": ["54", "56", "58", "60"],
                    "estimated_level": "L3"
                },
                "is_complete": False,
                "current_level_estimate": "L2",
                "confidence": 0.6
            }
        }
    )


class SubjectLevelResult(BaseModel):
    """Level result for a subject."""
    subject: SubjectType = Field(..., description="Subject assessed")
    level: LevelType = Field(..., description="Assessed level L0-L4")
    confidence: float = Field(..., description="Confidence in assessment", ge=0.0, le=1.0)
    questions_answered: int = Field(..., description="Number of questions answered")
    correct_answers: int = Field(..., description="Number of correct answers")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subject": "mathematics",
                "level": "L2",
                "confidence": 0.85,
                "questions_answered": 6,
                "correct_answers": 4
            }
        }
    )


class BaselineReportResponse(BaseModel):
    """Baseline assessment report."""
    session_id: str = Field(..., description="Assessment session ID")
    user_id: str = Field(..., description="User identifier")
    status: SessionStatus = Field(..., description="Session status")
    started_at: datetime = Field(..., description="Assessment start time")
    completed_at: Optional[datetime] = Field(None, description="Assessment completion time")
    results: List[SubjectLevelResult] = Field(..., description="Assessment results per subject")
    overall_summary: Dict[str, Any] = Field(..., description="Overall assessment summary")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "sess_123",
                "user_id": "user123",
                "status": "completed",
                "started_at": "2025-09-02T10:00:00Z",
                "completed_at": "2025-09-02T10:15:00Z",
                "results": [
                    {
                        "subject": "mathematics",
                        "level": "L2",
                        "confidence": 0.85,
                        "questions_answered": 6,
                        "correct_answers": 4
                    }
                ],
                "overall_summary": {
                    "total_questions": 6,
                    "total_correct": 4,
                    "accuracy": 0.67,
                    "assessment_duration_minutes": 15
                }
            }
        }
    )


class AssessmentEvent(BaseModel):
    """Event payload for assessment events."""
    event_type: EventType = Field(..., description="Type of event")
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    session_id: str = Field(..., description="Assessment session ID")
    user_id: str = Field(..., description="User identifier")
    data: Dict[str, Any] = Field(..., description="Event-specific data")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "BASELINE_COMPLETE",
                "event_id": "evt_123",
                "timestamp": "2025-09-02T10:15:00Z",
                "session_id": "sess_123",
                "user_id": "user123",
                "data": {
                    "subject": "mathematics",
                    "level": "L2",
                    "confidence": 0.85,
                    "questions_answered": 6
                }
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "SESSION_NOT_FOUND",
                "message": "Assessment session not found",
                "details": {"session_id": "sess_123"}
            }
        }
    )
