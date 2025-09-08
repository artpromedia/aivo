"""
Assessment engine for baseline assessment logic.
"""

import logging
import random
from datetime import datetime, timedelta
from uuid import uuid4

from .config import settings
from .enums import AnswerResult, LevelType, QuestionType, SessionStatus, SubjectType
from .schemas import AnswerEvaluation, Question, SubjectLevelResult

logger = logging.getLogger(__name__)


class AssessmentSession:
    """Assessment session data."""

    def __init__(self, user_id: str, subject: SubjectType) -> None:
        self.session_id = str(uuid4())
        self.user_id = user_id
        self.subject = subject
        self.status = SessionStatus.ACTIVE
        self.started_at = datetime.utcnow()
        self.expires_at = self.started_at + timedelta(hours=2)
        self.completed_at: datetime | None = None

        # Assessment state
        self.questions_answered: list[str] = []
        self.answers: dict[str, any] = {}
        self.evaluations: dict[str, AnswerEvaluation] = {}
        self.current_level_estimate = LevelType.L2  # Start at middle level
        self.confidence = 0.0
        self.correct_count = 0

    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at

    def is_complete(self) -> bool:
        """Check if assessment is complete."""
        return (
            self.status == SessionStatus.COMPLETED
            or len(self.questions_answered) >= settings.max_questions
            or self.confidence >= settings.convergence_threshold
        )

    def should_continue(self) -> bool:
        """Check if assessment should continue."""
        return (
            not self.is_complete()
            and not self.is_expired()
            and len(self.questions_answered) < settings.max_questions
        )


class QuestionBank:
    """Question bank for baseline assessment."""

    def __init__(self) -> None:
        """Initialize question bank with sample questions."""
        self._questions = self._generate_question_bank()

    def _generate_question_bank(self) -> dict[str, list[Question]]:
        """Generate a sample question bank organized by subject and level."""
        questions = {}

        # Mathematics questions
        math_questions = [
            # L0 - Basic counting
            Question(
                question_id="math_l0_1",
                text="How many apples are there if you have 2 apples and get 1 more?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["2", "3", "4", "5"],
                estimated_level=LevelType.L0,
                subject=SubjectType.MATHEMATICS,
            ),
            Question(
                question_id="math_l0_2",
                text="What number comes after 5?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["4", "6", "7", "8"],
                estimated_level=LevelType.L0,
                subject=SubjectType.MATHEMATICS,
            ),
            # L1 - Basic arithmetic
            Question(
                question_id="math_l1_1",
                text="What is 7 + 3?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["9", "10", "11", "12"],
                estimated_level=LevelType.L1,
                subject=SubjectType.MATHEMATICS,
            ),
            Question(
                question_id="math_l1_2",
                text="What is 15 - 8?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["6", "7", "8", "9"],
                estimated_level=LevelType.L1,
                subject=SubjectType.MATHEMATICS,
            ),
            # L2 - Multiplication/Division
            Question(
                question_id="math_l2_1",
                text="What is 6 × 7?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["40", "42", "44", "48"],
                estimated_level=LevelType.L2,
                subject=SubjectType.MATHEMATICS,
            ),
            Question(
                question_id="math_l2_2",
                text="What is 24 ÷ 6?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["3", "4", "5", "6"],
                estimated_level=LevelType.L2,
                subject=SubjectType.MATHEMATICS,
            ),
            # L3 - Fractions/Decimals
            Question(
                question_id="math_l3_1",
                text="What is 1/2 + 1/4?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["1/6", "2/6", "3/4", "1/3"],
                estimated_level=LevelType.L3,
                subject=SubjectType.MATHEMATICS,
            ),
            Question(
                question_id="math_l3_2",
                text="What is 0.5 × 0.8?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["0.3", "0.4", "0.45", "0.6"],
                estimated_level=LevelType.L3,
                subject=SubjectType.MATHEMATICS,
            ),
            # L4 - Advanced concepts
            Question(
                question_id="math_l4_1",
                text="If f(x) = 2x + 3, what is f(5)?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["11", "13", "15", "17"],
                estimated_level=LevelType.L4,
                subject=SubjectType.MATHEMATICS,
            ),
            Question(
                question_id="math_l4_2",
                text="What is the square root of 144?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["10", "11", "12", "13"],
                estimated_level=LevelType.L4,
                subject=SubjectType.MATHEMATICS,
            ),
        ]

        questions[SubjectType.MATHEMATICS] = math_questions

        # Science questions
        science_questions = [
            Question(
                question_id="sci_l1_1",
                text="What do plants need to grow?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["Only water", "Only sunlight", "Water and sunlight", "Nothing"],
                estimated_level=LevelType.L1,
                subject=SubjectType.SCIENCE,
            ),
            Question(
                question_id="sci_l2_1",
                text="What is the process by which plants make food?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["Respiration", "Photosynthesis", "Digestion", "Absorption"],
                estimated_level=LevelType.L2,
                subject=SubjectType.SCIENCE,
            ),
        ]

        questions[SubjectType.SCIENCE] = science_questions

        return questions

    def get_question(
        self, subject: SubjectType, level: LevelType, exclude_ids: list[str] = None
    ) -> Question | None:
        """Get a question for the specified subject and level."""
        if subject not in self._questions:
            return None

        exclude_ids = exclude_ids or []
        available_questions = [
            q
            for q in self._questions[subject]
            if q.estimated_level == level and q.question_id not in exclude_ids
        ]

        if not available_questions:
            # Try adjacent levels if no questions available
            level_order = [LevelType.L0, LevelType.L1, LevelType.L2, LevelType.L3, LevelType.L4]
            current_idx = level_order.index(level)

            for offset in [1, -1, 2, -2]:
                new_idx = current_idx + offset
                if 0 <= new_idx < len(level_order):
                    adjacent_level = level_order[new_idx]
                    available_questions = [
                        q
                        for q in self._questions[subject]
                        if q.estimated_level == adjacent_level and q.question_id not in exclude_ids
                    ]
                    if available_questions:
                        break

        return random.choice(available_questions) if available_questions else None

    def get_correct_answer(self, question_id: str) -> str | None:
        """Get the correct answer for a question."""
        # Simple correct answer mapping for demo
        answers = {
            "math_l0_1": "3",
            "math_l0_2": "6",
            "math_l1_1": "10",
            "math_l1_2": "7",
            "math_l2_1": "42",
            "math_l2_2": "4",
            "math_l3_1": "3/4",
            "math_l3_2": "0.4",
            "math_l4_1": "13",
            "math_l4_2": "12",
            "sci_l1_1": "Water and sunlight",
            "sci_l2_1": "Photosynthesis",
        }
        return answers.get(question_id)


class AssessmentEngine:
    """Core assessment engine for baseline assessments."""

    def __init__(self) -> None:
        """Initialize assessment engine."""
        self.sessions: dict[str, AssessmentSession] = {}
        self.question_bank = QuestionBank()
        logger.info("Assessment engine initialized")

    def start_assessment(
        self, user_id: str, subject: SubjectType
    ) -> tuple[AssessmentSession, Question]:
        """Start a new baseline assessment session."""
        session = AssessmentSession(user_id, subject)
        self.sessions[session.session_id] = session

        # Get first question (start at L2 level)
        first_question = self.question_bank.get_question(subject, LevelType.L2)
        if not first_question:
            raise ValueError(f"No questions available for subject {subject}")

        logger.info(
            f"Started assessment session {session.session_id} for user {user_id} in {subject}"
        )
        return session, first_question

    def submit_answer(
        self, session_id: str, question_id: str, answer: any
    ) -> tuple[AnswerEvaluation, Question | None, bool]:
        """Submit an answer and get evaluation with next question if applicable."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.is_expired():
            session.status = SessionStatus.EXPIRED
            raise ValueError(f"Session {session_id} has expired")

        # Evaluate answer
        correct_answer = self.question_bank.get_correct_answer(question_id)
        result = (
            AnswerResult.CORRECT
            if str(answer).lower() == str(correct_answer).lower()
            else AnswerResult.INCORRECT
        )

        evaluation = AnswerEvaluation(
            question_id=question_id,
            user_answer=answer,
            correct_answer=correct_answer,
            result=result,
            explanation=f"{'Correct!' if result == AnswerResult.CORRECT else 'Incorrect.'} The answer is {correct_answer}",
        )

        # Update session
        session.questions_answered.append(question_id)
        session.answers[question_id] = answer
        session.evaluations[question_id] = evaluation

        if result == AnswerResult.CORRECT:
            session.correct_count += 1

        # Update level estimate using adaptive algorithm
        self._update_level_estimate(session, question_id, result)

        # Check if assessment should continue
        next_question = None
        is_complete = False

        if session.should_continue() and len(session.questions_answered) >= settings.min_questions:
            # Check convergence
            if session.confidence >= settings.convergence_threshold:
                is_complete = True
                session.status = SessionStatus.COMPLETED
                session.completed_at = datetime.utcnow()
            else:
                next_question = self._get_next_question(session)
        elif len(session.questions_answered) < settings.min_questions:
            next_question = self._get_next_question(session)
        else:
            is_complete = True
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.utcnow()

        logger.info(
            f"Answer submitted for session {session_id}: {result}, "
            f"level estimate: {session.current_level_estimate}, "
            f"confidence: {session.confidence:.2f}, "
            f"complete: {is_complete}"
        )

        return evaluation, next_question, is_complete

    def get_session(self, session_id: str) -> AssessmentSession | None:
        """Get assessment session by ID."""
        return self.sessions.get(session_id)

    def get_baseline_report(self, session_id: str) -> SubjectLevelResult:
        """Generate baseline assessment report."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        result = SubjectLevelResult(
            subject=session.subject,
            level=session.current_level_estimate,
            confidence=session.confidence,
            questions_answered=len(session.questions_answered),
            correct_answers=session.correct_count,
        )

        logger.info(
            f"Generated baseline report for session {session_id}: {result.level} with {result.confidence:.2f} confidence"
        )
        return result

    def _update_level_estimate(
        self, session: AssessmentSession, question_id: str, result: AnswerResult
    ) -> None:
        """Update level estimate using simple adaptive algorithm."""
        # Get the question to know its level
        question_level = None
        for questions in self.question_bank._questions.values():
            for q in questions:
                if q.question_id == question_id:
                    question_level = q.estimated_level
                    break
            if question_level:
                break

        if not question_level:
            return

        # Simple adaptive algorithm
        level_values = {
            LevelType.L0: 0,
            LevelType.L1: 1,
            LevelType.L2: 2,
            LevelType.L3: 3,
            LevelType.L4: 4,
        }
        levels = [LevelType.L0, LevelType.L1, LevelType.L2, LevelType.L3, LevelType.L4]

        current_value = level_values[session.current_level_estimate]
        question_value = level_values[question_level]

        if result == AnswerResult.CORRECT:
            # Correct answer: move toward question level or higher
            if question_value > current_value:
                new_value = min(4, current_value + 0.5)
            else:
                new_value = min(4, current_value + 0.2)
        else:
            # Incorrect answer: move toward lower level
            if question_value <= current_value:
                new_value = max(0, current_value - 0.5)
            else:
                new_value = max(0, current_value - 0.2)

        session.current_level_estimate = levels[int(round(new_value))]

        # Update confidence based on consistency
        total_questions = len(session.questions_answered)
        if total_questions >= settings.min_questions:
            # Simple confidence calculation based on accuracy and consistency
            accuracy = session.correct_count / total_questions
            consistency_bonus = 0.1 if total_questions >= 5 else 0
            session.confidence = min(
                1.0, accuracy * 0.8 + consistency_bonus + (total_questions * 0.05)
            )

    def _get_next_question(self, session: AssessmentSession) -> Question | None:
        """Get the next question based on current level estimate."""
        # Try to get question at current estimated level
        next_question = self.question_bank.get_question(
            session.subject, session.current_level_estimate, session.questions_answered
        )

        # If no question available at current level, try adjacent levels
        if not next_question:
            level_order = [LevelType.L0, LevelType.L1, LevelType.L2, LevelType.L3, LevelType.L4]
            current_idx = level_order.index(session.current_level_estimate)

            for offset in [1, -1, 2, -2]:
                new_idx = current_idx + offset
                if 0 <= new_idx < len(level_order):
                    next_question = self.question_bank.get_question(
                        session.subject, level_order[new_idx], session.questions_answered
                    )
                    if next_question:
                        break

        return next_question


# Global assessment engine instance
assessment_engine = AssessmentEngine()
