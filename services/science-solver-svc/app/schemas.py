"""Pydantic schemas for Science Solver Service."""

from typing import Any

from pydantic import BaseModel, Field


# Request schemas
class UnitValidationRequest(BaseModel):
    """Request model for unit validation."""

    expression: str = Field(
        ...,
        description="Mathematical expression with units to validate",
        examples=["10 m/s + 5 mph", "F = ma where F in N, m in kg, a in m/s²"],
    )
    target_system: str | None = Field(
        default=None,
        description="Target unit system for conversion",
        examples=["SI", "Imperial", "CGS", "US"],
    )


class ChemicalEquationRequest(BaseModel):
    """Request model for chemical equation balancing."""

    equation: str = Field(
        ...,
        description="Unbalanced chemical equation",
        examples=[
            "H2 + O2 -> H2O",
            "C2H6 + O2 -> CO2 + H2O",
            "Fe + HCl -> FeCl2 + H2",
        ],
    )
    balance_type: str = Field(
        default="standard",
        description="Type of balancing algorithm",
        examples=["standard", "redox", "ionic"],
    )


class DiagramParseRequest(BaseModel):
    """Request model for diagram parsing."""

    image_data: str = Field(
        ...,
        description="Base64 encoded image data",
    )
    parse_type: str = Field(
        default="general",
        description="Type of diagram parsing",
        examples=["general", "circuit", "chemistry", "physics"],
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for object detection",
    )


# Response schemas
class UnitValidationResponse(BaseModel):
    """Response model for unit validation."""

    is_valid: bool = Field(
        ...,
        description="Whether the units are dimensionally consistent",
    )
    standardized_expression: str | None = Field(
        default=None,
        description="Expression converted to standard units",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of validation errors if any",
    )
    unit_analysis: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed dimensional analysis results",
    )


class ChemicalEquationResponse(BaseModel):
    """Response model for chemical equation balancing."""

    balanced_equation: str | None = Field(
        default=None,
        description="Balanced chemical equation",
    )
    coefficients: list[int] | None = Field(
        default=None,
        description="Stoichiometric coefficients",
    )
    is_balanced: bool = Field(
        ...,
        description="Whether balancing was successful",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of balancing errors if any",
    )
    reaction_type: str | None = Field(
        default=None,
        description="Type of chemical reaction identified",
    )


class BoundingBox(BaseModel):
    """Bounding box coordinates."""

    x: float = Field(..., description="X coordinate of top-left corner")
    y: float = Field(..., description="Y coordinate of top-left corner")
    width: float = Field(..., description="Width of the bounding box")
    height: float = Field(..., description="Height of the bounding box")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence score",
    )


class DetectedObject(BaseModel):
    """Detected object in diagram."""

    label: str = Field(..., description="Object label/class")
    bbox: BoundingBox = Field(..., description="Bounding box coordinates")
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional object properties",
    )


class DiagramParseResponse(BaseModel):
    """Response model for diagram parsing."""

    detected_objects: list[DetectedObject] = Field(
        default_factory=list,
        description="List of detected objects with bounding boxes",
    )
    extracted_text: list[str] = Field(
        default_factory=list,
        description="Text extracted from the diagram",
    )
    diagram_type: str | None = Field(
        default=None,
        description="Identified diagram type",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of parsing errors if any",
    )
    processing_info: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional processing metadata",
    )


# Health check response
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy")
    service: str = Field(default="science-solver-svc")
    version: str = Field(default="0.1.0")
    timestamp: str = Field(..., description="Current timestamp")
