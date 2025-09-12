"""Business logic services for Problem Session Orchestrator."""

import asyncio
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .models import ProblemAttempt, ProblemSession, SessionPhase, SessionStatus
from .schemas import (
    GradingResult,
    InkSubmissionResponse,
    RecognitionResult,
    SessionResultEvent,
    SubjectType,
)

logger = structlog.get_logger(__name__)


class SubjectBrainService:
    """Service for interacting with Subject Brain for activity planning."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.base_url = settings.subject_brain_url
        self.timeout = 30

    async def create_activity_plan(
        self, learner_id: UUID, subject: SubjectType, duration_minutes: int
    ) -> dict[str, Any] | None:
        """Create an activity plan for the learner and subject."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/plan",
                    json={
                        "learner_id": str(learner_id),
                        "subject": subject.value,
                        "session_duration_minutes": duration_minutes,
                        "force_refresh": False,
                    },
                )
                response.raise_for_status()
                plan_data = response.json()

                logger.info(
                    "Created activity plan",
                    learner_id=learner_id,
                    subject=subject,
                    plan_id=plan_data.get("plan_id"),
                    activities_count=len(plan_data.get("activities", [])),
                )

                return plan_data

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(
                "Failed to create activity plan",
                error=str(e),
                learner_id=learner_id,
                subject=subject,
            )
            return None


class InkService:
    """Service for interacting with Ink Capture Service."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.base_url = settings.ink_service_url
        self.timeout = 30

    async def create_ink_session(
        self,
        session_id: UUID,
        learner_id: UUID,
        subject: SubjectType,
        canvas_width: int,  # pylint: disable=unused-argument
        canvas_height: int,  # pylint: disable=unused-argument
    ) -> UUID | None:
        """Create an ink capture session."""
        try:
            # For ink service, we use the same session ID
            ink_session_id = session_id

            logger.info(
                "Created ink session",
                session_id=session_id,
                ink_session_id=ink_session_id,
                learner_id=learner_id,
                subject=subject,
            )

            return ink_session_id

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Failed to create ink session",
                error=str(e),
                session_id=session_id,
                learner_id=learner_id,
            )
            return None

    async def submit_strokes(
        self,
        ink_session_id: UUID,
        learner_id: UUID,
        subject: SubjectType,
        page_number: int,
        strokes: list[dict[str, Any]],
        canvas_width: int,
        canvas_height: int,
        metadata: dict[str, Any] | None = None,
    ) -> InkSubmissionResponse | None:
        """Submit ink strokes for processing."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "session_id": str(ink_session_id),
                    "learner_id": str(learner_id),
                    "subject": subject.value,
                    "page_number": page_number,
                    "canvas_width": canvas_width,
                    "canvas_height": canvas_height,
                    "strokes": strokes,
                    "metadata": metadata or {},
                }

                response = await client.post(
                    f"{self.base_url}/strokes", json=payload
                )
                response.raise_for_status()
                data = response.json()

                return InkSubmissionResponse(
                    session_id=UUID(data["session_id"]),
                    page_id=UUID(data["page_id"]),
                    recognition_job_id=UUID(data.get("recognition_job_id"))
                    if data.get("recognition_job_id")
                    else None,
                    status="submitted",
                    message="Ink submitted successfully",
                )

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(
                "Failed to submit ink strokes",
                error=str(e),
                ink_session_id=ink_session_id,
            )
            return None


class RecognitionService:
    """Service for coordinating recognition across math and science."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.math_url = settings.math_service_url
        self.science_url = settings.science_service_url
        self.timeout = settings.recognition_timeout_seconds

    async def recognize_from_ink_session(
        self, ink_session_id: UUID, page_number: int, subject: SubjectType
    ) -> RecognitionResult | None:
        """Recognize content from ink session based on subject."""
        try:
            if subject == SubjectType.MATHEMATICS:
                return await self._recognize_math(ink_session_id, page_number)
            elif subject in [
                SubjectType.SCIENCE,
                SubjectType.PHYSICS,
                SubjectType.CHEMISTRY,
                SubjectType.BIOLOGY,
            ]:
                return await self._recognize_science(
                    ink_session_id, page_number
                )
            else:
                logger.warning(
                    "Unsupported subject for recognition", subject=subject
                )
                return None

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Recognition failed",
                error=str(e),
                ink_session_id=ink_session_id,
                subject=subject,
            )
            return None

    async def _recognize_math(
        self, ink_session_id: UUID, page_number: int
    ) -> RecognitionResult | None:
        """Recognize mathematical expressions."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.math_url}/recognize/{ink_session_id}",
                    params={"page_number": page_number},
                )
                response.raise_for_status()
                data = response.json()

                return RecognitionResult(
                    success=data.get("success", False),
                    confidence=data.get("confidence", 0.0),
                    expression=data.get("latex"),
                    latex=data.get("latex"),
                    ast=data.get("ast"),
                    processing_time=data.get("processing_time", 0.0),
                    error_message=data.get("error_message"),
                )

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(
                "Math recognition failed", error=str(e), session=ink_session_id
            )
            return None

    async def _recognize_science(
        self,
        ink_session_id: UUID,
        page_number: int,  # pylint: disable=unused-argument
    ) -> RecognitionResult | None:
        """Recognize science expressions and diagrams."""
        try:
            # For science, we might need to try multiple endpoints
            # This is a simplified implementation
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Try chemical equation recognition first
                response = await client.post(
                    f"{self.science_url}/chem/balance",
                    json={
                        "equation": "H2 + O2 -> H2O",  # Mock equation
                        "balance_type": "standard",
                    },
                )
                response.raise_for_status()
                data = response.json()

                return RecognitionResult(
                    success=data.get("is_balanced", False),
                    confidence=0.8,  # Mock confidence
                    expression=data.get("balanced_equation"),
                    processing_time=0.5,
                )

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(
                "Science recognition failed",
                error=str(e),
                session=ink_session_id,
            )
            return None


class GradingService:
    """Service for grading student responses."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.math_url = settings.math_service_url
        self.science_url = settings.science_service_url
        self.timeout = 15

    async def grade_response(
        self,
        subject: SubjectType,
        student_expression: str,
        expected_answer: str | None = None,
        problem_type: str = "algebraic",
    ) -> GradingResult | None:
        """Grade a student response based on subject."""
        try:
            if subject == SubjectType.MATHEMATICS:
                return await self._grade_math(
                    student_expression, expected_answer, problem_type
                )
            elif subject in [
                SubjectType.SCIENCE,
                SubjectType.CHEMISTRY,
                SubjectType.PHYSICS,
            ]:
                return await self._grade_science(
                    student_expression, expected_answer, problem_type
                )
            else:
                logger.warning(
                    "Unsupported subject for grading", subject=subject
                )
                return None

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Grading failed",
                error=str(e),
                subject=subject,
                expression=student_expression,
            )
            return None

    async def _grade_math(
        self,
        student_expression: str,
        expected_answer: str | None,
        problem_type: str,
    ) -> GradingResult | None:
        """Grade mathematical expressions."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "student_expression": student_expression,
                    "correct_expression": expected_answer or "x^2",
                    "expression_type": problem_type,
                    "check_equivalence": True,
                    "show_steps": True,
                }

                response = await client.post(
                    f"{self.math_url}/grade", json=payload
                )
                response.raise_for_status()
                data = response.json()

                return GradingResult(
                    is_correct=data.get("is_correct", False),
                    score=data.get("score", 0.0),
                    feedback=data.get("feedback", "No feedback available"),
                    is_equivalent=data.get("is_equivalent"),
                    expected_answer=expected_answer,
                    steps=data.get("steps"),
                )

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error("Math grading failed", error=str(e))
            return None

    async def _grade_science(
        self,
        student_expression: str,
        expected_answer: str | None,
        problem_type: str,
    ) -> GradingResult | None:
        """Grade science expressions."""
        try:
            # Simplified science grading - in practice would use specific
            # science grading endpoints
            if problem_type == "chemical_equation":
                is_correct = "H2O" in student_expression
                score = 1.0 if is_correct else 0.0
                feedback = (
                    "Correct chemical equation!"
                    if is_correct
                    else "Check your chemical equation balancing"
                )

                return GradingResult(
                    is_correct=is_correct,
                    score=score,
                    feedback=feedback,
                    expected_answer=expected_answer,
                )

            # Default scoring
            return GradingResult(
                is_correct=True,
                score=0.8,
                feedback="Good work on this science problem!",
                expected_answer=expected_answer,
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Science grading failed", error=str(e))
            return None


class EventService:
    """Service for publishing session events."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.event_url = settings.event_service_url
        self.enabled = settings.enable_events

    async def publish_session_result(
        self, session_result: SessionResultEvent
    ) -> bool:
        """Publish SESSION_RESULT event."""
        if not self.enabled:
            logger.info("Event publishing disabled, skipping SESSION_RESULT")
            return True

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.event_url,
                    json=session_result.model_dump(),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                logger.info(
                    "Published SESSION_RESULT event",
                    session_id=session_result.session_id,
                    learner_id=session_result.learner_id,
                    status=session_result.status,
                )
                return True

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(
                "Failed to publish SESSION_RESULT event",
                error=str(e),
                session_id=session_result.session_id,
            )
            return False


class ProblemSessionOrchestrator:
    """Main orchestrator for problem sessions."""

    def __init__(self) -> None:
        """Initialize the orchestrator."""
        self.brain_service = SubjectBrainService()
        self.ink_service = InkService()
        self.recognition_service = RecognitionService()
        self.grading_service = GradingService()
        self.event_service = EventService()

    async def start_session(
        self,
        learner_id: UUID,
        subject: SubjectType,
        session_duration_minutes: int,
        canvas_width: int,
        canvas_height: int,
        db: AsyncSession,
    ) -> ProblemSession | None:
        """Start a new problem session."""
        try:
            # Create session record
            session = ProblemSession(
                learner_id=learner_id,
                subject=subject.value,
                status=SessionStatus.PLANNING,
                current_phase=SessionPhase.PLAN,
                session_duration_minutes=session_duration_minutes,
                canvas_width=canvas_width,
                canvas_height=canvas_height,
                started_at=datetime.utcnow(),
            )

            db.add(session)
            await db.commit()
            await db.refresh(session)

            logger.info(
                "Created problem session",
                session_id=session.session_id,
                learner_id=learner_id,
                subject=subject,
            )

            # Create activity plan
            activity_plan = await self.brain_service.create_activity_plan(
                learner_id, subject, session_duration_minutes
            )

            if activity_plan:
                await db.execute(
                    update(ProblemSession)
                    .where(ProblemSession.session_id == session.session_id)
                    .values(
                        activity_plan_id=activity_plan.get("plan_id"),
                        planned_activities=activity_plan,
                        status=SessionStatus.ACTIVE,
                        current_phase=SessionPhase.PRESENT,
                    )
                )
                await db.commit()
                await db.refresh(session)

            # Create ink session
            ink_session_id = await self.ink_service.create_ink_session(
                session.session_id,
                learner_id,
                subject,
                canvas_width,
                canvas_height,
            )

            if ink_session_id:
                await db.execute(
                    update(ProblemSession)
                    .where(ProblemSession.session_id == session.session_id)
                    .values(ink_session_id=ink_session_id)
                )
                await db.commit()
                await db.refresh(session)

            return session

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Failed to start session",
                error=str(e),
                learner_id=learner_id,
                subject=subject,
            )
            return None

    async def submit_ink(
        self,
        session_id: UUID,
        page_number: int,
        strokes: list[dict[str, Any]],
        metadata: dict[str, Any],
        db: AsyncSession,
    ) -> InkSubmissionResponse | None:
        """Submit ink for recognition and processing."""
        try:
            # Get session
            result = await db.execute(
                select(ProblemSession).where(
                    ProblemSession.session_id == session_id
                )
            )
            session = result.scalar_one_or_none()

            if not session or not session.ink_session_id:
                logger.error(
                    "Session not found or no ink session",
                    session_id=session_id,
                )
                return None

            # Update session phase
            await db.execute(
                update(ProblemSession)
                .where(ProblemSession.session_id == session_id)
                .values(
                    current_phase=SessionPhase.INK,
                    status=SessionStatus.WAITING_INK,
                    last_activity=datetime.utcnow(),
                )
            )
            await db.commit()

            # Submit ink strokes
            ink_response = await self.ink_service.submit_strokes(
                session.ink_session_id,
                session.learner_id,
                SubjectType(session.subject),
                page_number,
                strokes,
                session.canvas_width,
                session.canvas_height,
                metadata,
            )

            if ink_response:
                # Update status to recognizing
                await db.execute(
                    update(ProblemSession)
                    .where(ProblemSession.session_id == session_id)
                    .values(
                        current_phase=SessionPhase.RECOGNIZE,
                        status=SessionStatus.RECOGNIZING,
                    )
                )
                await db.commit()

                # Start recognition process (async)
                asyncio.create_task(
                    self._process_recognition(
                        session_id, ink_response.page_id, page_number, db
                    )
                )

            return ink_response

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Failed to submit ink",
                error=str(e),
                session_id=session_id,
            )
            return None

    async def _process_recognition(
        self,
        session_id: UUID,
        page_id: UUID,
        page_number: int,
        db: AsyncSession,
    ) -> None:
        """Process recognition and grading asynchronously."""
        try:
            # Get session
            result = await db.execute(
                select(ProblemSession).where(
                    ProblemSession.session_id == session_id
                )
            )
            session = result.scalar_one_or_none()

            if not session:
                return

            # Perform recognition
            recognition_result = await (
                self.recognition_service.recognize_from_ink_session(
                    session.ink_session_id,
                    page_number,
                    SubjectType(session.subject),
                )
            )

            if recognition_result and recognition_result.success:
                # Update session status
                await db.execute(
                    update(ProblemSession)
                    .where(ProblemSession.session_id == session_id)
                    .values(
                        current_phase=SessionPhase.GRADE,
                        status=SessionStatus.GRADING,
                    )
                )
                await db.commit()

                # Perform grading
                grading_result = await self.grading_service.grade_response(
                    SubjectType(session.subject),
                    recognition_result.expression or "",
                    problem_type="algebraic",
                )

                if grading_result:
                    # Update session with results
                    await db.execute(
                        update(ProblemSession)
                        .where(ProblemSession.session_id == session_id)
                        .values(
                            current_phase=SessionPhase.FEEDBACK,
                            status=SessionStatus.PROVIDING_FEEDBACK,
                            total_problems_attempted=(
                                session.total_problems_attempted + 1
                            ),
                            total_problems_correct=(
                                session.total_problems_correct
                                + (1 if grading_result.is_correct else 0)
                            ),
                            average_confidence=recognition_result.confidence,
                        )
                    )
                    await db.commit()

                    # Create problem attempt record
                    attempt = ProblemAttempt(
                        session_id=session_id,
                        activity_id="current_activity",
                        problem_type="math_expression",
                        problem_statement="Solve the expression",
                        ink_page_id=page_id,
                        recognition_confidence=recognition_result.confidence,
                        recognized_expression=recognition_result.expression,
                        recognition_ast=recognition_result.ast,
                        is_correct=grading_result.is_correct,
                        grade_score=grading_result.score,
                        grade_feedback=grading_result.feedback,
                        attempt_status="completed",
                        recognized_at=datetime.utcnow(),
                        graded_at=datetime.utcnow(),
                        feedback_provided_at=datetime.utcnow(),
                    )

                    db.add(attempt)
                    await db.commit()

                    # Check if session should complete
                    await self._check_session_completion(session_id, db)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Recognition processing failed",
                error=str(e),
                session_id=session_id,
            )

    async def _check_session_completion(
        self, session_id: UUID, db: AsyncSession
    ) -> None:
        """Check if session should be completed."""
        try:
            result = await db.execute(
                select(ProblemSession).where(
                    ProblemSession.session_id == session_id
                )
            )
            session = result.scalar_one_or_none()

            if not session:
                return

            # Simple completion logic - complete after 5 problems or time limit
            should_complete = session.total_problems_attempted >= 5 or (
                session.started_at
                and datetime.utcnow() - session.started_at
                > timedelta(minutes=session.session_duration_minutes)
            )

            if should_complete:
                await self.complete_session(session_id, db)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Session completion check failed",
                error=str(e),
                session_id=session_id,
            )

    async def complete_session(
        self, session_id: UUID, db: AsyncSession
    ) -> None:
        """Complete a problem session."""
        try:
            # Update session status
            completed_at = datetime.utcnow()
            await db.execute(
                update(ProblemSession)
                .where(ProblemSession.session_id == session_id)
                .values(
                    status=SessionStatus.COMPLETED,
                    completed_at=completed_at,
                )
            )
            await db.commit()

            # Get final session data
            result = await db.execute(
                select(ProblemSession).where(
                    ProblemSession.session_id == session_id
                )
            )
            session = result.scalar_one_or_none()

            if session:
                # Calculate actual duration
                actual_duration = 0
                if session.started_at:
                    duration_seconds = (
                        completed_at - session.started_at
                    ).total_seconds()
                    actual_duration = int(duration_seconds / 60)

                # Publish session result event
                session_result = SessionResultEvent(
                    session_id=session_id,
                    learner_id=session.learner_id,
                    subject=SubjectType(session.subject),
                    status=SessionStatus.COMPLETED,
                    total_problems_attempted=session.total_problems_attempted,
                    total_problems_correct=session.total_problems_correct,
                    average_confidence=session.average_confidence,
                    session_duration_minutes=actual_duration,
                    completed_at=completed_at,
                    performance_metrics={
                        "accuracy": (
                            session.total_problems_correct
                            / max(session.total_problems_attempted, 1)
                        ),
                        "planned_duration": session.session_duration_minutes,
                        "actual_duration": actual_duration,
                    },
                )

                await self.event_service.publish_session_result(session_result)

                logger.info(
                    "Session completed successfully",
                    session_id=session_id,
                    problems_attempted=session.total_problems_attempted,
                    problems_correct=session.total_problems_correct,
                    duration_minutes=actual_duration,
                )

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Failed to complete session",
                error=str(e),
                session_id=session_id,
            )


# Global orchestrator instance
orchestrator = ProblemSessionOrchestrator()
