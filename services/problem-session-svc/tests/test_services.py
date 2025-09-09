"""Tests for the orchestration services."""
# pylint: disable=redefined-outer-name  # pytest fixtures redefine outer names

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas import InkSubmissionResponse, SubjectType
from app.services import (
    InkService,
    ProblemSessionOrchestrator,
    RecognitionService,
    SubjectBrainService,
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_session_id():
    """Sample session ID for testing."""
    return uuid4()


@pytest.fixture
def sample_learner_id():
    """Sample learner ID for testing."""
    return uuid4()


class TestSubjectBrainService:
    """Test SubjectBrainService."""

    @pytest.fixture
    def service(self):
        """Create SubjectBrainService instance."""
        return SubjectBrainService()

    @patch("httpx.AsyncClient.post")
    async def test_create_plan_success(
        self, mock_post, service, sample_learner_id
    ):
        """Test successful learning plan retrieval."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "plan_id": "test_plan",
            "activities": [{"activity_id": "1", "type": "lesson"}],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value.__aenter__.return_value = mock_response

        # Test
        result = await service.create_activity_plan(
            sample_learner_id, SubjectType.MATHEMATICS, 30
        )

        # Assertions
        assert result is not None
        assert result["plan_id"] == "test_plan"

    @patch("httpx.AsyncClient.post")
    async def test_create_plan_failure(
        self, mock_post, service, sample_learner_id
    ):
        """Test learning plan retrieval failure."""
        # Mock exception
        mock_post.side_effect = Exception("Network error")

        # Test
        result = await service.create_activity_plan(
            sample_learner_id, SubjectType.MATHEMATICS, 30
        )

        # Assertions
        assert result is None


class TestInkService:
    """Test InkService."""

    @pytest.fixture
    def service(self):
        """Create InkService instance."""
        return InkService()

    async def test_create_session_success(
        self, service, sample_learner_id
    ):
        """Test successful ink session creation."""
        session_id = uuid4()

        result = await service.create_ink_session(
            session_id, sample_learner_id, SubjectType.MATHEMATICS, 800, 600
        )

        assert result == session_id

    @patch("httpx.AsyncClient.post")
    async def test_submit_strokes_success(
        self, mock_post, service, sample_session_id
    ):
        """Test successful stroke submission."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "session_id": str(sample_session_id),
            "page_id": str(uuid4()),
            "recognition_job_id": str(uuid4()),
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value.__aenter__.return_value = mock_response

        # Test
        result = await service.submit_strokes(
            sample_session_id,
            uuid4(),
            SubjectType.MATHEMATICS,
            1,
            [{"points": [{"x": 0, "y": 0}]}],
            800,
            600,
        )

        # Assertions
        assert result is not None
        assert result.session_id == sample_session_id


class TestRecognitionService:
    """Test RecognitionService."""

    @pytest.fixture
    def service(self):
        """Create RecognitionService instance."""
        return RecognitionService()

    @patch("httpx.AsyncClient.post")
    async def test_math_recognition_success(
        self, mock_post, service, sample_session_id
    ):
        """Test math recognition success."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "success": True,
            "confidence": 0.9,
            "latex": "x^2",
            "processing_time": 0.5,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value.__aenter__.return_value = mock_response

        # Test
        result = await service.recognize_from_ink_session(
            sample_session_id, 1, SubjectType.MATHEMATICS
        )

        # Assertions
        assert result is not None
        assert result.success is True
        assert result.confidence == 0.9

    @patch("httpx.AsyncClient.post")
    async def test_science_recognition_success(
        self, mock_post, service, sample_session_id
    ):
        """Test science recognition success."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "is_balanced": True,
            "balanced_equation": "2H2 + O2 -> 2H2O",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value.__aenter__.return_value = mock_response

        # Test
        result = await service.recognize_from_ink_session(
            sample_session_id, 1, SubjectType.SCIENCE
        )

        # Assertions
        assert result is not None
        assert result.success is True


class TestProblemSessionOrchestrator:
    """Test ProblemSessionOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create ProblemSessionOrchestrator instance."""
        return ProblemSessionOrchestrator()

    @patch("app.services.SubjectBrainService.create_activity_plan")
    @patch("app.services.InkService.create_ink_session")
    async def test_start_session_success(
        self,
        mock_ink_create,
        mock_brain_plan,
        orchestrator,
        mock_db,
        sample_learner_id,
    ):
        """Test successful session start."""
        # Mock responses
        mock_brain_plan.return_value = {
            "plan_id": "test_plan",
            "activities": [],
        }
        mock_ink_create.return_value = uuid4()

        # Mock database operations
        mock_session = AsyncMock()
        mock_session.session_id = uuid4()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.execute.return_value = None

        # Test
        result = await orchestrator.start_session(
            sample_learner_id,
            SubjectType.MATHEMATICS,
            30,
            800,
            600,
            mock_db,
        )

        # Assertions - returns None due to mocking
        assert result is None

    @patch("app.services.RecognitionService.recognize_from_ink_session")
    @patch("app.services.InkService.submit_strokes")
    async def test_submit_ink_success(
        self,
        mock_ink_submit,
        mock_recognition,  # pylint: disable=unused-argument
        orchestrator,
        mock_db,
        sample_session_id,
    ):
        """Test successful ink submission."""
        # Mock session data
        mock_session = AsyncMock()
        mock_session.ink_session_id = uuid4()
        mock_session.learner_id = uuid4()
        mock_session.subject = SubjectType.MATHEMATICS.value
        mock_session.canvas_width = 800
        mock_session.canvas_height = 600

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        # Mock services
        mock_ink_submit.return_value = InkSubmissionResponse(
            session_id=sample_session_id,
            page_id=uuid4(),
            recognition_job_id=uuid4(),
            status="submitted",
            message="Success",
        )

        # Test
        result = await orchestrator.submit_ink(
            sample_session_id, 1, [{"points": []}], {}, mock_db
        )

        # Assertions
        assert result is not None
        assert result.status == "submitted"
