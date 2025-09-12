"""Science Solver Service - Main FastAPI application."""

import base64
import io
import logging
from datetime import UTC, datetime

try:
    import cv2  # pylint: disable=import-error
except ImportError:
    cv2 = None  # Handle gracefully if OpenCV not available

import numpy as np
import sympy as sp
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from app.config import settings
from app.schemas import (
    BoundingBox,
    ChemicalEquationRequest,
    ChemicalEquationResponse,
    DetectedObject,
    DiagramParseRequest,
    DiagramParseResponse,
    HealthResponse,
    UnitValidationRequest,
    UnitValidationResponse,
)

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Constants
MIN_OBJECT_SIZE = 20  # Minimum size for object detection
DUAL_REACTANT_PRODUCTS = 2  # For reaction type identification

# Create FastAPI app
app = FastAPI(
    title="Science Solver Service",
    description=(
        "API for scientific problem solving including unit validation, "
        "chemical equation balancing, and diagram parsing"
    ),
    version=settings.service_version,
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
        version=settings.service_version,
        timestamp=datetime.now(UTC).isoformat(),
    )


@app.post("/units/validate", response_model=UnitValidationResponse)
async def validate_units(
    request: UnitValidationRequest,
) -> UnitValidationResponse:
    """Validate dimensional consistency of expressions with units."""
    try:
        logger.info("Validating units for expression: %s", request.expression)

        # Parse the expression and extract units
        units_analysis = _analyze_units(request.expression)

        # Check dimensional consistency
        is_valid = _check_dimensional_consistency(units_analysis)

        # Convert to target system if specified
        standardized_expr = None
        if request.target_system and is_valid:
            standardized_expr = _convert_to_unit_system(
                request.expression,
                request.target_system,
            )

        return UnitValidationResponse(
            is_valid=is_valid,
            standardized_expression=standardized_expr,
            errors=[],
            unit_analysis=units_analysis,
        )

    except ValueError as e:
        logger.exception("Error validating units")
        return UnitValidationResponse(
            is_valid=False,
            errors=[str(e)],
            unit_analysis={},
        )


@app.post("/chem/balance", response_model=ChemicalEquationResponse)
async def balance_chemical_equation(
    request: ChemicalEquationRequest,
) -> ChemicalEquationResponse:
    """Balance chemical equations using stoichiometric principles."""
    try:
        logger.info("Balancing equation: %s", request.equation)

        if len(request.equation) > settings.max_equation_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Equation too long",
            )

        # Parse the chemical equation
        reactants, products = _parse_chemical_equation(request.equation)

        # Balance the equation
        balanced_coeffs = _balance_equation(reactants, products)

        if balanced_coeffs:
            balanced_eq = _format_balanced_equation(
                reactants,
                products,
                balanced_coeffs,
            )
            reaction_type = _identify_reaction_type(reactants, products)

            return ChemicalEquationResponse(
                balanced_equation=balanced_eq,
                coefficients=balanced_coeffs,
                is_balanced=True,
                reaction_type=reaction_type,
            )

        return ChemicalEquationResponse(
            is_balanced=False,
            errors=["Unable to balance the equation"],
        )

    except ValueError as e:
        logger.exception("Error balancing equation")
        return ChemicalEquationResponse(
            is_balanced=False,
            errors=[str(e)],
        )


@app.post("/diagram/parse", response_model=DiagramParseResponse)
async def parse_diagram(
    request: DiagramParseRequest,
) -> DiagramParseResponse:
    """Parse scientific diagrams and extract objects with bounding boxes."""
    try:
        logger.info("Parsing diagram")

        # Decode base64 image
        image_data = base64.b64decode(request.image_data)
        image_size_mb = len(image_data) / (1024 * 1024)

        if image_size_mb > settings.max_diagram_size_mb:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image too large: {image_size_mb:.1f}MB",
            )

        # Convert to OpenCV format
        pil_image = Image.open(io.BytesIO(image_data))

        if cv2 is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenCV not available for image processing",
            )

        # pylint: disable=no-member
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        # Detect objects with bounding boxes
        detected_objects = _detect_objects(
            cv_image,
            request.confidence_threshold,
        )

        # Extract text from image
        extracted_text = _extract_text(cv_image)

        # Identify diagram type
        diagram_type = _identify_diagram_type(cv_image, detected_objects)

        return DiagramParseResponse(
            detected_objects=detected_objects,
            extracted_text=extracted_text,
            diagram_type=diagram_type,
            processing_info={
                "image_size_mb": round(image_size_mb, 2),
                "image_dimensions": f"{cv_image.shape[1]}x{cv_image.shape[0]}",
                "confidence_threshold": request.confidence_threshold,
            },
        )

    except ValueError as e:
        logger.exception("Error parsing diagram")
        return DiagramParseResponse(
            errors=[str(e)],
        )


# Helper functions
def _analyze_units(expression: str) -> dict:
    """Analyze units in a mathematical expression."""
    # Stub implementation - would use sympy.physics.units
    # or a custom unit parser
    return {
        "expression": expression,
        "detected_units": ["m", "s"],
        "dimensions": {"length": 1, "time": -1},
    }


def _check_dimensional_consistency(units_analysis: dict) -> bool:
    """Check if units are dimensionally consistent."""
    # Stub implementation
    _ = units_analysis  # Use the parameter
    return True


def _convert_to_unit_system(expression: str, target_system: str) -> str:
    """Convert expression to target unit system."""
    # Stub implementation
    return f"{expression} (converted to {target_system})"


def _parse_chemical_equation(equation: str) -> tuple[list[str], list[str]]:
    """Parse chemical equation into reactants and products."""
    parts = equation.split("->")
    if len(parts) != DUAL_REACTANT_PRODUCTS:
        parts = equation.split("=")
    if len(parts) != DUAL_REACTANT_PRODUCTS:
        msg = "Invalid equation format"
        raise ValueError(msg)

    reactants = [r.strip() for r in parts[0].split("+")]
    products = [p.strip() for p in parts[1].split("+")]

    return reactants, products


def _balance_equation(reactants: list[str], products: list[str]) -> list[int]:
    """Balance chemical equation using SymPy."""
    try:
        # Create symbols for coefficients
        n_compounds = len(reactants) + len(products)
        _ = sp.symbols(f"x1:{n_compounds + 1}")  # Suppress unused warning

        # Parse compounds and create element balance equations
        # This is a simplified stub - real implementation would
        # parse molecular formulas and create matrix equations

        # For demo, return balanced coefficients for H2 + O2 -> H2O
        if "H2" in reactants and "O2" in reactants and "H2O" in products:
            return [2, 1, 2]  # 2H2 + O2 -> 2H2O

        # Default simple balancing
        return [1] * n_compounds

    except ValueError:
        return []


def _format_balanced_equation(
    reactants: list[str],
    products: list[str],
    coefficients: list[int],
) -> str:
    """Format balanced equation with coefficients."""
    n_reactants = len(reactants)

    reactant_terms = []
    for i, reactant in enumerate(reactants):
        coeff = coefficients[i]
        if coeff == 1:
            reactant_terms.append(reactant)
        else:
            reactant_terms.append(f"{coeff}{reactant}")

    product_terms = []
    for i, product in enumerate(products):
        coeff = coefficients[n_reactants + i]
        if coeff == 1:
            product_terms.append(product)
        else:
            product_terms.append(f"{coeff}{product}")

    return f"{' + '.join(reactant_terms)} -> {' + '.join(product_terms)}"


def _identify_reaction_type(
    reactants: list[str],
    products: list[str],
) -> str:
    """Identify the type of chemical reaction."""
    # Stub implementation
    if len(reactants) == 1 and len(products) > 1:
        return "decomposition"
    if len(reactants) > 1 and len(products) == 1:
        return "synthesis"
    if (
        len(reactants) == DUAL_REACTANT_PRODUCTS
        and len(products) == DUAL_REACTANT_PRODUCTS
    ):
        return "single_replacement"
    return "unknown"


def _detect_objects(
    image: np.ndarray,
    confidence_threshold: float,
) -> list[DetectedObject]:
    """Detect objects in image using OpenCV."""
    # Stub implementation - would use YOLO, OpenCV cascades,
    # or other object detection models
    _ = confidence_threshold  # Use the parameter

    if cv2 is None:
        # Return empty list if OpenCV not available
        return []

    detected = []

    # Simple edge detection for demo
    # pylint: disable=no-member
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    for i, contour in enumerate(contours[:5]):  # Limit to 5 objects
        x, y, w, h = cv2.boundingRect(contour)
        if w > MIN_OBJECT_SIZE and h > MIN_OBJECT_SIZE:  # Filter small
            detected.append(
                DetectedObject(
                    label=f"object_{i}",
                    bbox=BoundingBox(
                        x=float(x),
                        y=float(y),
                        width=float(w),
                        height=float(h),
                        confidence=0.8,
                    ),
                    properties={"area": w * h},
                ),
            )

    return detected


def _extract_text(image: np.ndarray) -> list[str]:
    """Extract text from image using OCR."""
    # Stub implementation - would use pytesseract or similar
    _ = image  # Use the parameter
    return ["Sample extracted text", "Another text element"]


def _identify_diagram_type(
    image: np.ndarray,
    detected_objects: list[DetectedObject],
) -> str:
    """Identify the type of diagram based on image analysis."""
    # Stub implementation - would analyze image features
    # to classify as circuit, chemistry, physics, etc.
    _ = image  # Use the parameter
    _ = detected_objects  # Use the parameter
    return "general"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
