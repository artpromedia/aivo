"""Tests for policy engine."""

import pytest

from app.models import (
    GradeBand,
    LLMProvider,
    PolicyRequest,
    Region,
    SubjectType,
    TeacherOverride,
)
from app.services.policy_engine import PolicyEngine


class TestPolicyEngine:
    """Test policy engine functionality."""

    @pytest.fixture
    async def engine(self):
        """Create policy engine instance."""
        engine = PolicyEngine()
        await engine.initialize()
        return engine

    @pytest.mark.asyncio
    async def test_mathematics_routing(self, engine):
        """Test mathematics subject routing."""
        request = PolicyRequest(
            subject=SubjectType.MATH,
            grade_band=GradeBand.K_2,
            region=Region.US_WEST,
            student_id="test_student",
            teacher_id="test_teacher",
        )

        response = await engine.get_policy(request)
        assert response.provider in [
            LLMProvider.ANTHROPIC,
            LLMProvider.OPENAI,
        ]
        assert response.region == Region.US_WEST
        assert response.data_residency_compliant is True

    @pytest.mark.asyncio
    async def test_language_arts_routing(self, engine):
        """Test language arts subject routing."""
        request = PolicyRequest(
            subject=SubjectType.ENGLISH,
            grade_band=GradeBand.GRADE_6_8,
            region=Region.EU_CENTRAL,
            student_id="test_student",
            teacher_id="test_teacher",
        )

        response = await engine.get_policy(request)
        assert response.provider in [
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
        ]
        assert response.region == Region.EU_CENTRAL
        assert response.data_residency_compliant is True

    @pytest.mark.asyncio
    async def test_teacher_override(self, engine):
        """Test teacher override functionality."""
        # Create override
        override = TeacherOverride(
            teacher_id="test_teacher",
            preferred_provider=LLMProvider.ANTHROPIC,
            subject=SubjectType.SCIENCE,
            grade_band=GradeBand.GRADE_9_12,
            duration_hours=12,
            reason="Testing",
        )

        override_id = await engine.add_teacher_override(override)
        assert override_id is not None

        # Test policy with override
        request = PolicyRequest(
            subject=SubjectType.SCIENCE,
            grade_band=GradeBand.GRADE_9_12,
            region=Region.US_EAST,
            student_id="test_student",
            teacher_id="test_teacher",
        )

        response = await engine.get_policy(request)
        assert response.provider == LLMProvider.ANTHROPIC

    @pytest.mark.asyncio
    async def test_regional_compliance(self, engine):
        """Test regional data residency compliance."""
        # EU request
        request = PolicyRequest(
            subject=SubjectType.MATH,
            grade_band=GradeBand.K_2,
            region=Region.EU_CENTRAL,
            student_id="test_student",
            teacher_id="test_teacher",
        )

        response = await engine.get_policy(request)
        assert response.data_residency_compliant is True
        assert response.region == Region.EU_CENTRAL

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, engine):
        """Test statistics tracking."""
        # Make some requests
        for i in range(3):
            request = PolicyRequest(
                subject=SubjectType.MATH,
                grade_band=GradeBand.K_2,
                region=Region.US_WEST,
                student_id=f"student_{i}",
                teacher_id=f"teacher_{i}",
            )
            await engine.get_policy(request)

        stats = await engine.get_stats()
        assert stats["total_requests"] >= 3
        assert "provider_distribution" in stats
        assert "region_distribution" in stats
