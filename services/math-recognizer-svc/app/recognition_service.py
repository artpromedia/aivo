"""Math recognition service using machine learning and pattern matching."""

import asyncio
import logging
import time
from typing import Any

import httpx
import numpy as np

try:
    from PIL import Image
except ImportError as e:
    msg = "PIL (Pillow) is required but not installed"
    raise ImportError(msg) from e

from .cas_service import cas_service
from .config import settings
from .schemas import (
    GradeRequest,
    GradeResponse,
    InkData,
    RecognitionRequest,
    RecognitionResponse,
)

# Type alias for mathematical expressions (SymPy expressions)
MathExpression = Any

logger = logging.getLogger(__name__)


class MathRecognitionService:
    """Service for mathematical ink recognition and conversion."""

    def __init__(self) -> None:
        """Initialize the recognition service."""
        self.confidence_threshold = settings.confidence_threshold
        self.max_processing_time = settings.max_recognition_time

    async def recognize_from_session(
        self, request: RecognitionRequest,
    ) -> RecognitionResponse:
        """Recognize math from ink session ID.

        Args:
            request: Recognition request with session ID

        Returns:
            Recognition response with LaTeX, AST, and confidence
        """
        start_time = time.time()

        try:
            # Fetch ink data from ink service
            ink_data = await self._fetch_ink_data(
                request.session_id, request.page_number,
            )

            if not ink_data:
                return RecognitionResponse(
                    success=False,
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    error_message="Failed to fetch ink data from session",
                )

            # Apply region filtering if specified
            if request.region:
                ink_data = self._filter_by_region(ink_data, request.region)

            # Perform recognition
            return await self._recognize_ink(ink_data, start_time)

        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            logger.exception("Error in math recognition")
            return RecognitionResponse(
                success=False,
                confidence=0.0,
                processing_time=time.time() - start_time,
                error_message=f"Recognition error: {e!s}",
            )

    async def recognize_from_ink(
        self, ink_data: InkData,
    ) -> RecognitionResponse:
        """Recognize math from direct ink data.

        Args:
            ink_data: Direct ink stroke data

        Returns:
            Recognition response with LaTeX, AST, and confidence
        """
        start_time = time.time()
        return await self._recognize_ink(ink_data, start_time)

    async def _recognize_ink(
        self, ink_data: InkData, start_time: float,
    ) -> RecognitionResponse:
        """Internal method to perform ink recognition.

        Args:
            ink_data: Ink stroke data
            start_time: Recognition start time

        Returns:
            Recognition response
        """
        try:
            # Check for timeout
            if time.time() - start_time > self.max_processing_time:
                return RecognitionResponse(
                    success=False,
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    error_message="Recognition timeout",
                )

            # Convert strokes to image for processing
            image = self._strokes_to_image(ink_data)

            # Perform OCR/ML recognition (placeholder implementation)
            latex_expr, confidence = await self._perform_recognition(image)

            if confidence < self.confidence_threshold:
                return RecognitionResponse(
                    success=False,
                    latex=latex_expr,
                    confidence=confidence,
                    processing_time=time.time() - start_time,
                    error_message="Confidence below threshold",
                )

            # Parse to AST using CAS
            ast_data = None
            if latex_expr:
                parsed_expr = cas_service.parse_expression(latex_expr)
                if parsed_expr:
                    ast_data = cas_service.to_ast(parsed_expr)

            return RecognitionResponse(
                success=True,
                latex=latex_expr,
                ast=ast_data,
                confidence=confidence,
                processing_time=time.time() - start_time,
            )

        except (ValueError, TypeError, AttributeError) as e:
            logger.exception("Error in ink recognition")
            return RecognitionResponse(
                success=False,
                confidence=0.0,
                processing_time=time.time() - start_time,
                error_message=f"Recognition error: {e!s}",
            )

    async def grade_expression(self, request: GradeRequest) -> GradeResponse:
        """Grade mathematical expressions for correctness and equivalence.

        Args:
            request: Grading request

        Returns:
            Grading response with score and feedback
        """
        try:
            # Parse both expressions
            student_expr = cas_service.parse_expression(
                request.student_expression,
            )
            correct_expr = cas_service.parse_expression(
                request.correct_expression,
            )

            if student_expr is None:
                return GradeResponse(
                    is_correct=False,
                    is_equivalent=False,
                    score=0.0,
                    feedback="Unable to parse student expression",
                )

            if correct_expr is None:
                return GradeResponse(
                    is_correct=False,
                    is_equivalent=False,
                    score=0.0,
                    feedback="Unable to parse correct expression",
                )

            # Check for exact match
            is_exact = student_expr.equals(correct_expr)

            # Check for mathematical equivalence
            is_equivalent = False
            if request.check_equivalence:
                is_equivalent = cas_service.are_equivalent(
                    student_expr, correct_expr, request.tolerance,
                )

            # Calculate score
            score = 1.0 if is_exact else 0.8 if is_equivalent else 0.0

            # Generate feedback
            feedback = self._generate_feedback(
                is_exact, is_equivalent, student_expr, correct_expr,
            )

            # Generate step-by-step solution if requested
            steps = None
            if request.return_steps and "=" in request.correct_expression:
                steps = cas_service.solve_step_by_step(
                    request.correct_expression,
                )

            return GradeResponse(
                is_correct=is_exact,
                is_equivalent=is_equivalent,
                score=score,
                feedback=feedback,
                steps=steps,
            )

        except (ValueError, TypeError, AttributeError) as e:
            logger.exception("Error in expression grading")
            return GradeResponse(
                is_correct=False,
                is_equivalent=False,
                score=0.0,
                feedback=f"Grading error: {e!s}",
            )

    async def _fetch_ink_data(
        self, session_id: str, page_number: int | None,
    ) -> InkData | None:
        """Fetch ink data from the ink service.

        Args:
            session_id: Session identifier
            page_number: Page number to fetch

        Returns:
            Ink data or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.ink_service_url}/sessions/{session_id}"
                if page_number:
                    url += f"/pages/{page_number}"

                response = await client.get(url)
                response.raise_for_status()

                data = response.json()
                return InkData(**data)

        except (httpx.RequestError, httpx.HTTPStatusError, ValueError):
            logger.exception("Failed to fetch ink data")
            return None

    def _filter_by_region(
        self, ink_data: InkData, region: dict[str, float],
    ) -> InkData:
        """Filter strokes by bounding box region.

        Args:
            ink_data: Original ink data
            region: Bounding box {x, y, width, height}

        Returns:
            Filtered ink data
        """
        x, y = region["x"], region["y"]
        width, height = region["width"], region["height"]

        filtered_strokes = []
        for stroke in ink_data.strokes:
            # Check if stroke intersects with region
            stroke_points = [
                point for point in stroke.points
                if x <= point.x <= x + width and y <= point.y <= y + height
            ]

            if stroke_points:
                # Create new stroke with filtered points
                filtered_stroke = stroke.model_copy()
                filtered_stroke.points = stroke_points
                filtered_strokes.append(filtered_stroke)

        return InkData(
            strokes=filtered_strokes,
            canvas_width=ink_data.canvas_width,
            canvas_height=ink_data.canvas_height,
        )

    def _strokes_to_image(self, ink_data: InkData) -> Image.Image:
        """Convert ink strokes to PIL Image.

        Args:
            ink_data: Ink stroke data

        Returns:
            PIL Image representation
        """
        # Create blank image
        img = Image.new(
            "RGB",
            (ink_data.canvas_width, ink_data.canvas_height),
            "white",
        )

        # Simple rasterization (in practice, use more sophisticated methods)
        pixels = np.array(img)

        for stroke in ink_data.strokes:
            # Draw stroke points
            for point in stroke.points:
                x, y = int(point.x), int(point.y)
                if (
                    0 <= x < ink_data.canvas_width
                    and 0 <= y < ink_data.canvas_height
                ):
                    # Simple black pixel (could use stroke width and color)
                    pixels[y, x] = [0, 0, 0]

        return Image.fromarray(pixels)

    async def _perform_recognition(
        self, _image: Image.Image,
    ) -> tuple[str, float]:
        """Perform OCR/ML recognition on image.

        Args:
            image: PIL Image to recognize

        Returns:
            Tuple of (latex_expression, confidence)
        """
        # Placeholder implementation
        # In practice, this would use TensorFlow/PyTorch models,
        # TrOCR, MyScript, or other math recognition APIs

        await asyncio.sleep(0.1)  # Simulate processing time

        # Mock recognition results based on image analysis
        # This is where you'd integrate with actual ML models
        mock_expressions = [
            ("x^2 + 2x + 1", 0.95),
            ("\\frac{a}{b} = c", 0.87),
            ("\\int_{0}^{\\infty} e^{-x} dx", 0.82),
            ("\\sqrt{x + y}", 0.79),
        ]

        # Return a mock result (in practice, analyze the actual image)
        return mock_expressions[0]

    def _generate_feedback(
        self,
        is_exact: bool,
        is_equivalent: bool,
        student_expr: MathExpression,
        correct_expr: MathExpression,
    ) -> str:
        """Generate feedback message for grading.

        Args:
            is_exact: Whether expressions are exactly equal
            is_equivalent: Whether expressions are mathematically equivalent
            student_expr: Student's expression
            correct_expr: Correct expression

        Returns:
            Feedback message
        """
        if is_exact:
            return "Correct! Your answer matches exactly."
        if is_equivalent:
            return "Correct! Your answer is mathematically equivalent."

        student_latex = cas_service.to_latex(student_expr)
        correct_latex = cas_service.to_latex(correct_expr)
        return (
            f"Incorrect. You wrote: {student_latex}, "
            f"but the correct answer is: {correct_latex}"
        )


# Global service instance
math_recognition_service = MathRecognitionService()
