"""
Comprehensive tests for Assessment Service.
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from app.main import app
from app.enums import SubjectType, LevelType, SessionStatus, AnswerResult
from app.assessment_engine import assessment_engine
from app.event_service import event_service

# Create test client
client = TestClient(app)


@pytest.fixture
def mock_event_service():
    """Mock event service for testing."""
    with patch.object(event_service, 'publish_session_started', new_callable=AsyncMock) as mock_session, \
         patch.object(event_service, 'publish_question_answered', new_callable=AsyncMock) as mock_question, \
         patch.object(event_service, 'publish_baseline_complete', new_callable=AsyncMock) as mock_complete:
        
        yield {
            'session_started': mock_session,
            'question_answered': mock_question,
            'baseline_complete': mock_complete
        }


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test health check returns 200 and correct information."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "assessment-svc"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns service information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "Assessment Service"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data


class TestBaselineAssessment:
    """Test baseline assessment workflow."""
    
    def setup_method(self):
        """Clean up assessment engine before each test."""
        assessment_engine.sessions.clear()
    
    def test_start_baseline_assessment(self, mock_event_service):
        """Test starting a baseline assessment."""
        request_data = {
            "user_id": "test-user-123",
            "subject": "mathematics"
        }
        
        response = client.post("/baseline/start", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == "test-user-123"
        assert data["subject"] == "mathematics"
        assert data["status"] == "active"
        assert "session_id" in data
        assert "first_question" in data
        assert "started_at" in data
        assert "expires_at" in data
        
        # Verify first question structure
        question = data["first_question"]
        assert "question_id" in question
        assert "text" in question
        assert "estimated_level" in question
        assert "options" in question
        assert len(question["options"]) >= 2
        
        # Verify event was published
        mock_event_service['session_started'].assert_called_once()
    
    def test_start_assessment_invalid_subject(self):
        """Test starting assessment with invalid subject."""
        request_data = {
            "user_id": "test-user-123",
            "subject": "invalid_subject"
        }
        
        response = client.post("/baseline/start", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_submit_baseline_answer(self, mock_event_service):
        """Test submitting an answer to baseline assessment."""
        # First start an assessment
        start_request = {
            "user_id": "test-user-123",
            "subject": "mathematics"
        }
        start_response = client.post("/baseline/start", json=start_request)
        assert start_response.status_code == 200
        
        start_data = start_response.json()
        session_id = start_data["session_id"]
        question_id = start_data["first_question"]["question_id"]
        
        # Submit answer
        answer_request = {
            "session_id": session_id,
            "question_id": question_id,
            "answer": "A"
        }
        
        response = client.post("/baseline/answer", json=answer_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == session_id
        assert "evaluation" in data
        assert "is_complete" in data
        assert "current_level_estimate" in data
        assert "confidence" in data
        
        # Verify evaluation structure
        evaluation = data["evaluation"]
        assert "result" in evaluation
        assert "user_answer" in evaluation
        assert "correct_answer" in evaluation
        assert "explanation" in evaluation
        
        # Verify events were published
        mock_event_service['question_answered'].assert_called_once()
    
    def test_submit_answer_invalid_session(self):
        """Test submitting answer with invalid session ID."""
        answer_request = {
            "session_id": "invalid-session",
            "question_id": "q1",
            "answer": "A"
        }
        
        response = client.post("/baseline/answer", json=answer_request)
        assert response.status_code == 400
    
    def test_complete_baseline_assessment(self, mock_event_service):
        """Test completing a full baseline assessment (5-7 questions)."""
        # Start assessment
        start_request = {
            "user_id": "test-user-123",
            "subject": "mathematics"
        }
        start_response = client.post("/baseline/start", json=start_request)
        session_id = start_response.json()["session_id"]
        
        question_count = 0
        is_complete = False
        current_question_id = start_response.json()["first_question"]["question_id"]
        
        # Answer questions until assessment is complete
        while not is_complete and question_count < 10:  # Safety limit
            answer_request = {
                "session_id": session_id,
                "question_id": current_question_id,
                "answer": "A"  # Always answer A for consistency
            }
            
            response = client.post("/baseline/answer", json=answer_request)
            assert response.status_code == 200
            
            data = response.json()
            is_complete = data["is_complete"]
            question_count += 1
            
            if not is_complete:
                assert "next_question" in data
                current_question_id = data["next_question"]["question_id"]
            else:
                # Assessment completed
                assert data["next_question"] is None
                break
        
        # Verify assessment completed within expected range
        assert 5 <= question_count <= 7, f"Expected 5-7 questions, got {question_count}"
        assert is_complete, "Assessment should be complete"
        
        # Verify baseline complete event was published
        mock_event_service['baseline_complete'].assert_called_once()
    
    def test_get_baseline_report(self, mock_event_service):
        """Test getting baseline assessment report."""
        # Complete an assessment first
        start_request = {
            "user_id": "test-user-123",
            "subject": "mathematics"
        }
        start_response = client.post("/baseline/start", json=start_request)
        session_id = start_response.json()["session_id"]
        
        # Answer enough questions to complete assessment
        current_question_id = start_response.json()["first_question"]["question_id"]
        for i in range(7):  # Answer 7 questions to ensure completion
            answer_request = {
                "session_id": session_id,
                "question_id": current_question_id,
                "answer": "A"
            }
            
            response = client.post("/baseline/answer", json=answer_request)
            data = response.json()
            
            if data["is_complete"]:
                break
            
            if "next_question" in data and data["next_question"]:
                current_question_id = data["next_question"]["question_id"]
        
        # Get report
        response = client.get(f"/baseline/report?sessionId={session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == session_id
        assert data["user_id"] == "test-user-123"
        assert data["status"] in ["completed", "in_progress"]
        assert "results" in data
        assert len(data["results"]) == 1
        assert "overall_summary" in data
        
        # Verify result structure
        result = data["results"][0]
        assert result["subject"] == "mathematics"
        assert "level" in result
        assert "confidence" in result
        assert "questions_answered" in result
        assert "correct_answers" in result
        
        # Verify overall summary
        summary = data["overall_summary"]
        assert "total_questions" in summary
        assert "total_correct" in summary
        assert "accuracy" in summary
        assert "assessment_duration_minutes" in summary
    
    def test_get_report_invalid_session(self):
        """Test getting report for non-existent session."""
        response = client.get("/baseline/report?sessionId=invalid-session")
        assert response.status_code == 404
    
    def test_get_session_status(self, mock_event_service):
        """Test getting session status."""
        # Start assessment
        start_request = {
            "user_id": "test-user-123",
            "subject": "mathematics"
        }
        start_response = client.post("/baseline/start", json=start_request)
        session_id = start_response.json()["session_id"]
        
        # Get session status
        response = client.get(f"/sessions/{session_id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == session_id
        assert data["status"] == "active"
        assert data["is_expired"] is False
        assert data["is_complete"] is False
        assert data["questions_answered"] == 0
        assert "current_level_estimate" in data
        assert "confidence" in data
    
    def test_get_status_invalid_session(self):
        """Test getting status for non-existent session."""
        response = client.get("/sessions/invalid-session/status")
        assert response.status_code == 404


class TestAssessmentEngine:
    """Test assessment engine functionality."""
    
    def setup_method(self):
        """Clean up assessment engine before each test."""
        assessment_engine.sessions.clear()
    
    def test_assessment_convergence(self):
        """Test that assessment converges within expected number of questions."""
        session, first_question = assessment_engine.start_assessment(
            "test-user", SubjectType.MATHEMATICS
        )
        
        question_count = 1
        current_question = first_question
        
        # Answer questions until convergence
        while question_count <= 10:  # Safety limit
            # Simulate consistent correct answers for L2 level
            answer = current_question.options[0]  # Always first option
            
            evaluation, next_question, is_complete = assessment_engine.submit_answer(
                session.session_id,
                current_question.question_id,
                answer
            )
            
            if is_complete:
                break
            
            question_count += 1
            current_question = next_question
        
        assert 5 <= question_count <= 7, f"Expected convergence in 5-7 questions, got {question_count}"
        assert session.is_complete()
        assert session.current_level_estimate in [LevelType.L0, LevelType.L1, LevelType.L2, LevelType.L3, LevelType.L4]
    
    def test_level_estimation_accuracy(self):
        """Test that level estimation responds to answer patterns."""
        session, first_question = assessment_engine.start_assessment(
            "test-user", SubjectType.MATHEMATICS
        )
        
        # Simulate pattern of mostly correct answers
        current_question = first_question
        for i in range(5):
            # Answer correctly 80% of the time
            if i < 4:
                # Find a correct answer (simulate correct response)
                answer = current_question.options[0]
            else:
                # Wrong answer occasionally
                answer = current_question.options[-1]
            
            evaluation, next_question, is_complete = assessment_engine.submit_answer(
                session.session_id,
                current_question.question_id,
                answer
            )
            
            if is_complete:
                break
            
            current_question = next_question
        
        # Level should be estimated based on performance
        assert session.current_level_estimate is not None
        assert session.confidence > 0


class TestEventService:
    """Test event service functionality."""
    
    @pytest.mark.asyncio
    async def test_publish_baseline_complete_event(self):
        """Test publishing baseline complete event."""
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            
            await event_service.publish_baseline_complete(
                session_id="test-session",
                user_id="test-user",
                subject="mathematics",
                level="L2",
                confidence=0.85,
                questions_answered=6,
                correct_answers=5
            )
            
            # Verify HTTP call was made
            mock_post.assert_called_once()
            
            # Verify event payload structure
            call_args = mock_post.call_args
            event_data = call_args.kwargs['json']
            
            # Check event_type - it might be an enum or string
            event_type = event_data['event_type']
            if hasattr(event_type, 'value'):
                assert event_type.value == 'BASELINE_COMPLETE'
            else:
                assert event_type == 'BASELINE_COMPLETE'
            assert event_data['session_id'] == 'test-session'
            assert event_data['user_id'] == 'test-user'
            assert event_data['data']['subject'] == 'mathematics'
            assert event_data['data']['level'] == 'L2'
            assert event_data['data']['confidence'] == 0.85


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_validation_error_handling(self):
        """Test handling of validation errors."""
        # Invalid request body
        response = client.post("/baseline/start", json={})
        assert response.status_code == 422
    
    def test_session_expiration(self, mock_event_service):
        """Test handling of expired sessions."""
        # Start assessment
        start_request = {
            "user_id": "test-user-123",
            "subject": "mathematics"
        }
        start_response = client.post("/baseline/start", json=start_request)
        session_id = start_response.json()["session_id"]
        
        # Manually expire the session
        session = assessment_engine.get_session(session_id)
        session.expires_at = datetime.utcnow() - timedelta(hours=1)
        
        # Try to submit answer to expired session
        answer_request = {
            "session_id": session_id,
            "question_id": "any-question",
            "answer": "A"
        }
        
        response = client.post("/baseline/answer", json=answer_request)
        assert response.status_code == 400
