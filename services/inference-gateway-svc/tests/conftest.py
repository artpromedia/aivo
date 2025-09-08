"""
Test configuration and fixtures.
"""

from unittest.mock import Mock

import pytest
import pytest_asyncio
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = Mock()

    # Mock completions
    completion_response = Mock()
    completion_response.id = "test-completion-id"
    completion_response.created = 1634567890
    completion_response.model = "gpt-3.5-turbo"
    completion_response.choices = [
        Mock(text="This is a test response.", finish_reason="stop", logprobs=None)
    ]
    completion_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    client.completions.create.return_value = completion_response

    # Mock embeddings
    embedding_response = Mock()
    embedding_response.model = "text-embedding-ada-002"
    embedding_response.data = [Mock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5])]
    embedding_response.usage = Mock(prompt_tokens=5, total_tokens=5)
    client.embeddings.create.return_value = embedding_response

    # Mock moderation
    moderation_response = Mock()
    moderation_response.id = "test-moderation-id"
    moderation_response.model = "text-moderation-latest"
    moderation_result = Mock()
    moderation_result.flagged = False
    moderation_result.categories = Mock()
    moderation_result.categories.__dict__ = {
        "hate": False,
        "hate/threatening": False,
        "harassment": False,
        "harassment/threatening": False,
        "self-harm": False,
        "self-harm/intent": False,
        "self-harm/instructions": False,
        "sexual": False,
        "sexual/minors": False,
        "violence": False,
        "violence/graphic": False,
    }
    moderation_result.category_scores = Mock()
    moderation_result.category_scores.__dict__ = {
        "hate": 0.01,
        "hate/threatening": 0.01,
        "harassment": 0.01,
        "harassment/threatening": 0.01,
        "self-harm": 0.01,
        "self-harm/intent": 0.01,
        "self-harm/instructions": 0.01,
        "sexual": 0.01,
        "sexual/minors": 0.01,
        "violence": 0.01,
        "violence/graphic": 0.01,
    }
    moderation_response.results = [moderation_result]
    client.moderations.create.return_value = moderation_response

    # Mock models list for health check
    models_response = Mock()
    models_response.data = [Mock(id="gpt-3.5-turbo")]
    client.models.list.return_value = models_response

    return client


@pytest.fixture
def mock_flagged_moderation():
    """Mock OpenAI client that returns flagged content."""
    client = Mock()

    moderation_response = Mock()
    moderation_response.id = "test-moderation-id"
    moderation_response.model = "text-moderation-latest"
    moderation_result = Mock()
    moderation_result.flagged = True
    moderation_result.categories = Mock()
    moderation_result.categories.__dict__ = {
        "hate": True,
        "violence": False,
        "sexual": False,
    }
    moderation_result.category_scores = Mock()
    moderation_result.category_scores.__dict__ = {
        "hate": 0.95,  # High score for hate
        "violence": 0.01,
        "sexual": 0.01,
    }
    moderation_response.results = [moderation_result]
    client.moderations.create.return_value = moderation_response

    return client


@pytest_asyncio.fixture
async def client():
    """Create test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_generate_request():
    """Sample generation request data."""
    return {
        "prompt": "Explain photosynthesis for 5th grade students",
        "model": "gpt-3.5-turbo",
        "max_tokens": 100,
        "temperature": 0.7,
        "context": {
            "subject": "Science",
            "grade_level": "5th",
            "learning_objective": "Understand basic photosynthesis process",
        },
    }


@pytest.fixture
def sample_embedding_request():
    """Sample embedding request data."""
    return {
        "input": "What is photosynthesis?",
        "model": "text-embedding-ada-002",
        "context": {"subject": "Science", "grade_level": "5th"},
    }


@pytest.fixture
def sample_moderation_request():
    """Sample moderation request data."""
    return {"input": "This is a test message for moderation", "threshold": 0.8}


@pytest.fixture
def pii_text_sample():
    """Sample text containing PII."""
    return "My email is john.doe@example.com and my phone is 555-123-4567"


@pytest.fixture
def harmful_content_sample():
    """Sample harmful content for moderation testing."""
    return "I hate everyone and want to cause violence"
