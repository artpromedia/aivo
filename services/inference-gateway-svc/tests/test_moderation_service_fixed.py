"""
Tests for content moderation service.
"""

import pytest
from app.moderation_service import ModerationService
from app.schemas import ModerationResult


class TestModerationService:
    """Test moderation service functionality."""

    @pytest.mark.asyncio
    async def test_moderate_safe_content(self, mock_openai_client):
        """Test moderation of safe content."""
        mock_openai_client.moderations.create.return_value.results = [
            type(
                "MockResult",
                (),
                {
                    "flagged": False,
                    "category_scores": type(
                        "MockScores", (), {"model_dump": lambda: {"harassment": 0.1, "hate": 0.05}}
                    )(),
                },
            )()
        ]

        moderation_service = ModerationService(mock_openai_client)
        content = "This is a safe and friendly message."

        result, scores = await moderation_service.moderate_content(content)

        assert result == ModerationResult.PASSED
        assert isinstance(scores, dict)
        assert "harassment" in scores

    @pytest.mark.asyncio
    async def test_moderate_harmful_content(self, mock_openai_client):
        """Test moderation of harmful content."""
        mock_openai_client.moderations.create.return_value.results = [
            type(
                "MockResult",
                (),
                {
                    "flagged": True,
                    "category_scores": type(
                        "MockScores", (), {"model_dump": lambda: {"harassment": 0.9, "hate": 0.8}}
                    )(),
                },
            )()
        ]

        moderation_service = ModerationService(mock_openai_client)
        content = "This content should be blocked due to harmful nature."

        result, scores = await moderation_service.moderate_content(content, threshold=0.8)

        assert result == ModerationResult.BLOCKED
        assert scores["harassment"] > 0.8

    @pytest.mark.asyncio
    async def test_moderate_with_custom_threshold(self, mock_openai_client):
        """Test moderation with custom threshold."""
        mock_openai_client.moderations.create.return_value.results = [
            type(
                "MockResult",
                (),
                {
                    "flagged": True,
                    "category_scores": type(
                        "MockScores", (), {"model_dump": lambda: {"harassment": 0.7, "hate": 0.6}}
                    )(),
                },
            )()
        ]

        moderation_service = ModerationService(mock_openai_client)
        content = "Borderline content for threshold testing."

        result, _ = await moderation_service.moderate_content(content, threshold=0.99)

        assert result == ModerationResult.PASSED

        # Test with different content
        result, _ = await moderation_service.moderate_content(content, threshold=0.5)
        assert result in [ModerationResult.PASSED, ModerationResult.BLOCKED]

    @pytest.mark.asyncio
    async def test_moderate_batch_content(self, mock_openai_client):
        """Test batch moderation."""
        mock_openai_client.moderations.create.return_value.results = [
            type(
                "MockResult",
                (),
                {
                    "flagged": False,
                    "category_scores": type(
                        "MockScores", (), {"model_dump": lambda: {"harassment": 0.1, "hate": 0.05}}
                    )(),
                },
            )()
        ]

        moderation_service = ModerationService(mock_openai_client)
        contents = ["This is safe content.", "Another safe message.", "One more friendly text."]

        results = await moderation_service.moderate_batch(contents)

        assert len(results) == 3
        assert all(result[0] == ModerationResult.PASSED for result in results)
        assert all(isinstance(result[1], dict) for result in results)

    @pytest.mark.asyncio
    async def test_get_moderation_summary(self, mock_openai_client):
        """Test moderation summary generation."""
        # Mock different results
        results = [
            (ModerationResult.PASSED, {"harassment": 0.1, "hate": 0.05}),
            (ModerationResult.BLOCKED, {"harassment": 0.9, "hate": 0.8}),
            (ModerationResult.PASSED, {"harassment": 0.2, "hate": 0.1}),
            (ModerationResult.ERROR, {}),
        ]

        moderation_service = ModerationService(mock_openai_client)
        summary = moderation_service.get_moderation_summary(results)

        assert summary["total"] == 4
        assert summary["passed"] == 2
        assert summary["blocked"] == 1
        assert summary["errors"] == 1
        assert summary["block_rate"] == 0.25
        assert "average_scores" in summary

    @pytest.mark.asyncio
    async def test_moderation_error_handling(self):
        """Test error handling in moderation."""
        # Create moderation service with None client to force error
        moderation_service = ModerationService()
        moderation_service.client = None  # Force error

        result, scores = await moderation_service.moderate_content("test")

        assert result == ModerationResult.ERROR
        assert scores == {}
