"""
Tests for OpenAI integration service.
"""

from unittest.mock import Mock, patch

import pytest
from app.openai_service import OpenAIService
from app.schemas import ContentContext, EmbeddingRequest, GenerateRequest, ModerationRequest
from app.schemas import ModerationResult as ModerationResultEnum


class TestOpenAIService:
    """Test OpenAI service functionality."""

    @pytest.mark.asyncio
    async def test_generate_text_success(self, mock_openai_client):
        """Test successful text generation."""
        with patch("app.openai_service.OpenAI", return_value=mock_openai_client):
            openai_service = OpenAIService()

            request = GenerateRequest(
                prompt="Explain photosynthesis",
                max_tokens=100,
                temperature=0.7,
                context=ContentContext(subject="Science", grade_level="5th"),
            )

            response = await openai_service.generate_text(request)

            assert response.object == "text_completion"
            assert len(response.choices) == 1
            assert response.choices[0].text == "This is a test response."
            assert response.moderation_result == ModerationResultEnum.PASSED
            assert response.context.subject == "Science"

    @pytest.mark.asyncio
    async def test_generate_text_with_pii_scrubbing(self, mock_openai_client):
        """Test text generation with PII in prompt."""
        with patch("app.openai_service.OpenAI", return_value=mock_openai_client):
            openai_service = OpenAIService()

            request = GenerateRequest(
                prompt="My email is john@example.com. Explain photosynthesis.", max_tokens=100
            )

            response = await openai_service.generate_text(request)

            # Should detect PII
            assert response.pii_detected
            # PII should be scrubbed from prompt
            assert response.pii_scrubbed

    @pytest.mark.asyncio
    async def test_generate_text_blocked_content(self, mock_flagged_moderation):
        """Test text generation with blocked content."""
        with patch("app.openai_service.moderation_service.client", mock_flagged_moderation):
            with patch("app.openai_service.OpenAI"):
                openai_service = OpenAIService()

                request = GenerateRequest(
                    prompt="Harmful content that should be blocked", max_tokens=100
                )

                response = await openai_service.generate_text(request)

                assert response.moderation_result == ModerationResultEnum.BLOCKED
                assert "[Content blocked due to policy violation]" in response.choices[0].text
                assert response.choices[0].finish_reason == "content_filter"

    @pytest.mark.asyncio
    async def test_generate_text_skip_moderation(self, mock_openai_client):
        """Test text generation with moderation skipped."""
        with patch("app.openai_service.OpenAI", return_value=mock_openai_client):
            openai_service = OpenAIService()

            request = GenerateRequest(prompt="Test prompt", skip_moderation=True)

            response = await openai_service.generate_text(request)

            assert response.moderation_result == ModerationResultEnum.PASSED

    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self, mock_openai_client):
        """Test successful embedding generation."""
        with patch("app.openai_service.OpenAI", return_value=mock_openai_client):
            openai_service = OpenAIService()

            request = EmbeddingRequest(
                input="What is photosynthesis?", context=ContentContext(subject="Science")
            )

            response = await openai_service.generate_embeddings(request)

            assert response.object == "list"
            assert len(response.data) == 1
            assert len(response.data[0].embedding) == 5
            assert response.context.subject == "Science"

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, mock_openai_client):
        """Test batch embedding generation."""
        with patch("app.openai_service.OpenAI", return_value=mock_openai_client):
            openai_service = OpenAIService()

            # Mock multiple embeddings
            mock_openai_client.embeddings.create.return_value.data = [
                Mock(embedding=[0.1, 0.2]),
                Mock(embedding=[0.3, 0.4]),
            ]

            request = EmbeddingRequest(input=["Text 1", "Text 2"])

            response = await openai_service.generate_embeddings(request)

            assert len(response.data) == 2

    @pytest.mark.asyncio
    async def test_generate_embeddings_with_pii(self, mock_openai_client):
        """Test embedding generation with PII in input."""
        with patch("app.openai_service.OpenAI", return_value=mock_openai_client):
            openai_service = OpenAIService()

            request = EmbeddingRequest(input="Contact me at john@example.com for questions")

            response = await openai_service.generate_embeddings(request)

            assert response.pii_detected
            assert response.pii_scrubbed

    @pytest.mark.asyncio
    async def test_moderate_content_success(self, mock_openai_client):
        """Test successful content moderation."""
        with patch("app.openai_service.OpenAI", return_value=mock_openai_client):
            openai_service = OpenAIService()

            request = ModerationRequest(input="This is safe content", threshold=0.8)

            response = await openai_service.moderate_content(request)

            assert response.model == "text-moderation-latest"
            assert len(response.results) == 1
            assert not response.results[0].flagged

    @pytest.mark.asyncio
    async def test_moderate_content_batch(self, mock_openai_client):
        """Test batch content moderation."""
        with patch("app.openai_service.OpenAI", return_value=mock_openai_client):
            openai_service = OpenAIService()

            # Mock multiple moderation results
            mock_result1 = Mock()
            mock_result1.flagged = False
            mock_result1.categories = Mock()
            mock_result1.categories.__dict__ = {"hate": False}
            mock_result1.category_scores = Mock()
            mock_result1.category_scores.__dict__ = {"hate": 0.1}

            mock_result2 = Mock()
            mock_result2.flagged = False
            mock_result2.categories = Mock()
            mock_result2.categories.__dict__ = {"violence": False}
            mock_result2.category_scores = Mock()
            mock_result2.category_scores.__dict__ = {"violence": 0.05}

            mock_openai_client.moderations.create.return_value.results = [
                mock_result1,
                mock_result2,
            ]

            request = ModerationRequest(input=["Content 1", "Content 2"])

            response = await openai_service.moderate_content(request)

            assert len(response.results) == 2

    @pytest.mark.asyncio
    async def test_context_preservation(self, mock_openai_client):
        """Test that educational context is preserved through processing."""
        with patch("app.openai_service.OpenAI", return_value=mock_openai_client):
            openai_service = OpenAIService()

            context = ContentContext(
                subject="Mathematics",
                grade_level="8th",
                learning_objective="Understand algebraic expressions",
                content_type="practice_problem",
            )

            request = GenerateRequest(prompt="Create an algebra problem", context=context)

            response = await openai_service.generate_text(request)

            assert response.context.subject == "Mathematics"
            assert response.context.grade_level == "8th"
            assert response.context.learning_objective == "Understand algebraic expressions"
            assert response.context.content_type == "practice_problem"
