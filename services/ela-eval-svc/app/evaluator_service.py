"""ELA Evaluator service implementation."""

import asyncio
import logging
import time
from uuid import UUID, uuid4

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from .config import settings
from .schemas import (
    ContentModerationFlag,
    EvaluationHistoryRequest,
    EvaluationHistoryResponse,
    EvaluationRequest,
    EvaluationResponse,
    EvaluationSummary,
    GradeBand,
    PIIEntity,
    RubricCriterion,
    RubricScore,
    ScoreLevel,
)

logger = logging.getLogger(__name__)


class ELAEvaluatorService:
    """Service for ELA rubric evaluation with PII moderation."""

    def __init__(self: "ELAEvaluatorService") -> None:
        """Initialize the ELA evaluator service."""
        self.analyzer_engine = None
        self.anonymizer_engine = None
        self._initialize_pii_engines()

    def _initialize_pii_engines(self: "ELAEvaluatorService") -> None:
        """Initialize PII detection and anonymization engines."""
        try:
            if settings.enable_pii_detection:
                self.analyzer_engine = AnalyzerEngine()
                self.anonymizer_engine = AnonymizerEngine()
                logger.info("PII engines initialized successfully")
        except (ImportError, RuntimeError) as e:
            logger.warning("Failed to initialize PII engines: %s", str(e))
            self.analyzer_engine = None
            self.anonymizer_engine = None

    async def evaluate_submission(
        self: "ELAEvaluatorService", request: EvaluationRequest
    ) -> EvaluationResponse:
        """Evaluate an ELA submission using rubric scoring.

        Args:
            request: Evaluation request with submission and configuration

        Returns:
            Evaluation response with scores and safety assessment
        """
        start_time = time.time()
        evaluation_id = uuid4()

        try:
            # Step 1: PII Detection and Anonymization
            pii_entities = []
            anonymized_submission = request.submission
            pii_detected = False

            if request.enable_pii_detection and self.analyzer_engine:
                pii_entities, anonymized_submission, pii_detected = (
                    await self._detect_and_anonymize_pii(request.submission)
                )

            # Step 2: Content Moderation
            content_flags = []
            is_safe = True

            if request.enable_content_moderation:
                content_flags, is_safe = await self._moderate_content(
                    anonymized_submission
                )

            # Step 3: Rubric Scoring (use anonymized text)
            scores = await self._score_submission(
                request.prompt, anonymized_submission, request.grade_band,
                request.criteria
            )

            # Step 4: Generate Teacher Notes
            teacher_notes = await self._generate_teacher_notes(
                scores, request.grade_band
            )

            # Step 5: Suggest Next Steps
            suggested_next_steps = await self._generate_next_steps(
                scores, request.grade_band
            )

            # Calculate overall score
            overall_score = sum(score.score.value for score in scores) / len(
                scores
            )

            processing_time = int((time.time() - start_time) * 1000)

            return EvaluationResponse(
                evaluation_id=evaluation_id,
                scores=scores,
                overall_score=overall_score,
                grade_band=request.grade_band,
                pii_detected=pii_detected,
                pii_entities=pii_entities,
                content_flags=content_flags,
                is_safe=is_safe,
                teacher_notes=teacher_notes,
                suggested_next_steps=suggested_next_steps,
                processing_time_ms=processing_time,
                model_used=settings.default_model,
            )

        except Exception as e:
            logger.exception("Error in submission evaluation")
            raise RuntimeError(f"Evaluation failed: {e}") from e

    async def _detect_and_anonymize_pii(
        self: "ELAEvaluatorService", text: str
    ) -> tuple[list[PIIEntity], str, bool]:
        """Detect and anonymize PII in text.

        Args:
            text: Input text to analyze

        Returns:
            Tuple of (PII entities, anonymized text, PII detected flag)
        """
        if not self.analyzer_engine or not self.anonymizer_engine:
            return [], text, False

        try:
            # Analyze text for PII
            results = self.analyzer_engine.analyze(
                text=text,
                language="en",
                score_threshold=settings.pii_confidence_threshold,
            )

            if not results:
                return [], text, False

            # Convert results to our schema
            pii_entities = []
            for result in results:
                entity = PIIEntity(
                    entity_type=result.entity_type,
                    text=text[result.start:result.end],
                    start=result.start,
                    end=result.end,
                    confidence=result.score,
                    anonymized_text=f"[{result.entity_type}]",
                )
                pii_entities.append(entity)

            # Anonymize text
            anonymized_result = self.anonymizer_engine.anonymize(
                text=text, analyzer_results=results
            )

            return pii_entities, anonymized_result.text, True

        except (RuntimeError, ValueError) as e:
            logger.warning("PII detection failed: %s", str(e))
            return [], text, False

    async def _moderate_content(
        self: "ELAEvaluatorService", text: str
    ) -> tuple[list[ContentModerationFlag], bool]:
        """Moderate content for safety.

        Args:
            text: Text to moderate

        Returns:
            Tuple of (content flags, is_safe flag)
        """
        # Simplified content moderation - in production, use dedicated service
        content_flags = []

        # Basic keyword filtering
        inappropriate_keywords = [
            "hate", "violence", "inappropriate", "harmful"
        ]

        text_lower = text.lower()
        for keyword in inappropriate_keywords:
            if keyword in text_lower:
                flag = ContentModerationFlag(
                    category="inappropriate_content",
                    severity="medium",
                    confidence=0.8,
                    description=(
                        f"Contains potentially inappropriate keyword: "
                        f"{keyword}"
                    ),
                )
                content_flags.append(flag)

        is_safe = len(content_flags) == 0
        return content_flags, is_safe

    async def _score_submission(
        self: "ELAEvaluatorService",
        prompt: str,
        submission: str,
        grade_band: GradeBand,
        criteria: list[RubricCriterion],
    ) -> list[RubricScore]:
        """Score submission using AI-powered rubric evaluation.

        Args:
            prompt: Writing prompt
            submission: Student submission (anonymized)
            grade_band: Grade band for appropriate expectations
            criteria: List of criteria to evaluate

        Returns:
            List of rubric scores for each criterion
        """
        scores = []

        for criterion in criteria:
            try:
                score = await self._score_criterion(
                    prompt, submission, grade_band, criterion
                )
                scores.append(score)
            except (ValueError, RuntimeError) as e:
                logger.warning("Failed to score %s: %s", criterion, str(e))
                # Provide default score if AI scoring fails
                scores.append(
                    RubricScore(
                        criterion=criterion,
                        score=ScoreLevel.DEVELOPING,
                        reasoning="Unable to evaluate due to processing error",
                        strengths=[],
                        areas_for_improvement=["Requires manual review"],
                    )
                )

        return scores

    async def _score_criterion(
        self: "ELAEvaluatorService",
        prompt: str,
        submission: str,
        grade_band: GradeBand,
        criterion: RubricCriterion,
    ) -> RubricScore:
        """Score a specific rubric criterion using AI.

        Args:
            prompt: Writing prompt
            submission: Student submission
            grade_band: Grade band
            criterion: Specific criterion to evaluate

        Returns:
            Rubric score for the criterion
        """
        # Simulate AI scoring - in production, integrate with OpenAI/Anthropic
        # Use prompt, submission, and grade_band for actual AI scoring
        logger.info(
            "Scoring criterion %s for grade band %s "
            "(prompt: %d chars, submission: %d chars)",
            criterion.value, grade_band.value, len(prompt), len(submission)
        )
        await asyncio.sleep(0.1)  # Simulate processing time

        # Mock scoring logic based on criterion and grade band
        mock_scores = {
            RubricCriterion.IDEAS_AND_CONTENT: ScoreLevel.PROFICIENT,
            RubricCriterion.ORGANIZATION: ScoreLevel.DEVELOPING,
            RubricCriterion.VOICE: ScoreLevel.PROFICIENT,
            RubricCriterion.WORD_CHOICE: ScoreLevel.DEVELOPING,
            RubricCriterion.SENTENCE_FLUENCY: ScoreLevel.PROFICIENT,
            RubricCriterion.CONVENTIONS: ScoreLevel.DEVELOPING,
        }

        score = mock_scores.get(criterion, ScoreLevel.DEVELOPING)

        return RubricScore(
            criterion=criterion,
            score=score,
            reasoning=f"Student demonstrates {score.name.lower()} level "
            f"performance in {criterion.value.replace('_', ' ')} "
            f"for {grade_band.value} grade band.",
            strengths=[
                "Clear understanding of the topic",
                "Good effort in responding to prompt",
            ],
            areas_for_improvement=[
                "Could provide more specific examples",
                "Work on sentence variety",
            ],
        )

    async def _generate_teacher_notes(
        self: "ELAEvaluatorService",
        scores: list[RubricScore],
        grade_band: GradeBand,
    ) -> str:
        """Generate comprehensive teacher notes based on rubric scores.

        Args:
            scores: List of rubric scores
            grade_band: Grade band for appropriate feedback

        Returns:
            Generated teacher notes
        """
        # Simulate AI generation - in production, use LLM
        await asyncio.sleep(0.1)

        overall_score = sum(score.score.value for score in scores) / len(
            scores
        )

        if overall_score >= 3.5:
            performance_level = "excellent"
        elif overall_score >= 2.5:
            performance_level = "good"
        elif overall_score >= 1.5:
            performance_level = "developing"
        else:
            performance_level = "needs support"

        return (
            f"This student shows {performance_level} performance for "
            f"{grade_band.value} grade level. The writing demonstrates "
            f"understanding of the assignment and shows effort in "
            f"responding to the prompt. Continue to encourage creative "
            f"expression while working on technical skills."
        )

    async def _generate_next_steps(
        self: "ELAEvaluatorService",
        scores: list[RubricScore],
        grade_band: GradeBand,
    ) -> list[str]:
        """Generate suggested next steps based on evaluation.

        Args:
            scores: List of rubric scores
            grade_band: Grade band for appropriate activities

        Returns:
            List of suggested learning activities
        """
        # Simulate AI generation - in production, use LLM
        await asyncio.sleep(0.1)

        # Use grade_band to tailor suggestions appropriately
        logger.debug(
            "Generating next steps for grade band %s", grade_band.value
        )

        suggestions = [
            "Practice writing with graphic organizers",
            "Read mentor texts in similar genres",
            "Focus on adding descriptive details",
            "Work on paragraph transitions",
            "Practice peer editing and revision",
        ]

        # Customize based on lowest scoring areas
        lowest_score = min(score.score.value for score in scores)
        if lowest_score <= 2:
            suggestions.extend([
                "Provide additional scaffolding for writing structure",
                "Use sentence frames and starters",
                "Practice with shorter writing tasks first",
            ])

        return suggestions[:5]  # Return top 5 suggestions

    async def get_evaluation_history(
        self: "ELAEvaluatorService", request: EvaluationHistoryRequest
    ) -> EvaluationHistoryResponse:
        """Get evaluation history with filtering.

        Args:
            request: History request with filters

        Returns:
            Paginated evaluation history
        """
        # Mock implementation - in production, query database
        mock_evaluations = [
            EvaluationSummary(
                evaluation_id=uuid4(),
                student_id=request.student_id,
                assignment_id=request.assignment_id,
                grade_band=GradeBand.GRADES_3_5,
                overall_score=3.2,
                has_content_flags=False,
            )
        ]

        return EvaluationHistoryResponse(
            evaluations=mock_evaluations,
            total_count=len(mock_evaluations),
            has_more=False,
        )

    async def get_evaluation_by_id(
        self: "ELAEvaluatorService", evaluation_id: str
    ) -> EvaluationResponse | None:
        """Get specific evaluation by ID.

        Args:
            evaluation_id: UUID of evaluation to retrieve

        Returns:
            Evaluation response or None if not found
        """
        # Mock implementation - in production, query database
        try:
            UUID(evaluation_id)  # Validate UUID format
        except ValueError:
            return None

        # Return None to simulate not found - in production, query database
        return None


# Global service instance
ela_evaluator_service = ELAEvaluatorService()
