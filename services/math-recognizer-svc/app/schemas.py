"""Pydantic models for the Math Recognizer service."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Point(BaseModel):
    """A point in a stroke with coordinates and metadata."""

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    pressure: float | None = Field(None, description="Pressure value (0-1)")
    timestamp: int | None = Field(None, description="Timestamp in ms")


class Stroke(BaseModel):
    """A digital ink stroke consisting of points."""

    stroke_id: UUID = Field(..., description="Unique stroke identifier")
    tool_type: str = Field(
        default="pen",
        description="Tool type (pen, pencil)",
    )
    color: str = Field(default="#000000", description="Stroke color")
    width: float = Field(default=2.0, description="Stroke width")
    points: list[Point] = Field(
        ...,
        description="List of points in the stroke",
    )


class RecognitionRequest(BaseModel):
    """Request for math recognition from session ID."""

    session_id: UUID = Field(..., description="Ink session identifier")
    page_number: int | None = Field(
        1,
        description="Page number to recognize",
    )
    region: dict[str, float] | None = Field(
        None,
        description="Bounding box region {x, y, width, height}",
    )


class InkData(BaseModel):
    """Direct ink data for recognition (alternative to session ID)."""

    strokes: list[Stroke] = Field(..., description="List of ink strokes")
    canvas_width: int = Field(..., description="Canvas width in pixels")
    canvas_height: int = Field(..., description="Canvas height in pixels")


class RecognitionResponse(BaseModel):
    """Response from math recognition."""

    success: bool = Field(..., description="Recognition success status")
    latex: str | None = Field(None, description="LaTeX representation")
    ast: dict[str, Any] | None = Field(
        None,
        description="Abstract syntax tree",
    )
    confidence: float = Field(..., description="Confidence score (0-1)")
    processing_time: float = Field(
        ...,
        description="Processing time in seconds",
    )
    error_message: str | None = Field(
        None,
        description="Error message if failed",
    )


class GradeRequest(BaseModel):
    """Request for grading mathematical expressions."""

    student_expression: str = Field(
        ...,
        description="Student's mathematical expression (LaTeX or raw)",
    )
    correct_expression: str = Field(
        ...,
        description="Correct mathematical expression (LaTeX or raw)",
    )
    tolerance: float | None = Field(
        1e-6,
        description="Numerical tolerance for comparison",
    )
    check_equivalence: bool = Field(
        True,
        description="Check mathematical equivalence",
    )
    return_steps: bool = Field(
        False,
        description="Return step-by-step solution",
    )


class GradingStep(BaseModel):
    """A step in the mathematical solution."""

    step_number: int = Field(..., description="Step number")
    expression: str = Field(..., description="Expression at this step")
    explanation: str = Field(..., description="Explanation of the step")
    rule_applied: str | None = Field(
        None,
        description="Mathematical rule applied",
    )


class GradeResponse(BaseModel):
    """Response from mathematical grading."""

    is_correct: bool = Field(..., description="Whether the answer is correct")
    is_equivalent: bool = Field(
        ...,
        description="Whether expressions are mathematically equivalent",
    )
    score: float = Field(..., description="Grading score (0-1)")
    feedback: str = Field(..., description="Feedback message")
    steps: list[GradingStep] | None = Field(
        None,
        description="Step-by-step solution",
    )
    error_message: str | None = Field(
        None,
        description="Error message if grading failed",
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    service_name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Current timestamp")
    dependencies: dict[str, str] = Field(
        default_factory=dict,
        description="Status of dependencies",
    )
