"""
Tests for private brain request functionality.
"""

import pytest
from app.models import PrivateBrainRequest
from app.schemas import PrivateBrainRequestCreate
from app.services import PrivateBrainOrchestrator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestPrivateBrainRequest:
    """Test private brain request functionality."""

    @pytest.mark.asyncio
    async def test_create_new_request(self, client: AsyncClient, sample_request_data: dict):
        """Test creating a new private brain request."""
        response = await client.post("/private-brain/request", json=sample_request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["learner_id"] == sample_request_data["learner_id"]
        assert data["status"] == "PENDING"
        assert data["is_new_request"] is True
        assert "created" in data["message"]

    @pytest.mark.asyncio
    async def test_idempotent_requests(self, client: AsyncClient, sample_request_data: dict):
        """Test that multiple requests for the same learner are idempotent."""
        # First request
        response1 = await client.post("/private-brain/request", json=sample_request_data)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["is_new_request"] is True

        # Second request (should be idempotent)
        response2 = await client.post("/private-brain/request", json=sample_request_data)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["is_new_request"] is False
        assert data2["learner_id"] == data1["learner_id"]
        assert "updated" in data2["message"]

        # Third request (should also be idempotent)
        response3 = await client.post("/private-brain/request", json=sample_request_data)
        assert response3.status_code == 200
        data3 = response3.json()
        assert data3["is_new_request"] is False

    @pytest.mark.asyncio
    async def test_request_logging(self, db_session: AsyncSession, sample_request_data: dict):
        """Test that requests are properly logged."""
        orchestrator = PrivateBrainOrchestrator(db_session)
        request_data = PrivateBrainRequestCreate(**sample_request_data)

        # Make a request
        await orchestrator.request_private_brain(request_data)

        # Check that request was logged
        from sqlalchemy import func, select

        result = await db_session.execute(
            select(func.count(PrivateBrainRequest.id)).where(
                PrivateBrainRequest.learner_id == sample_request_data["learner_id"]
            )
        )
        request_count = result.scalar()
        assert request_count == 1

    @pytest.mark.asyncio
    async def test_request_count_tracking(
        self, db_session: AsyncSession, sample_request_data: dict
    ):
        """Test that request count is properly tracked."""
        orchestrator = PrivateBrainOrchestrator(db_session)
        request_data = PrivateBrainRequestCreate(**sample_request_data)

        # First request
        instance1, is_new1 = await orchestrator.request_private_brain(request_data)
        assert is_new1 is True
        assert instance1.request_count == 1

        # Second request
        instance2, is_new2 = await orchestrator.request_private_brain(request_data)
        assert is_new2 is False
        assert instance2.request_count == 2
        assert instance2.id == instance1.id

        # Third request
        instance3, is_new3 = await orchestrator.request_private_brain(request_data)
        assert is_new3 is False
        assert instance3.request_count == 3

    @pytest.mark.asyncio
    async def test_different_learners_separate_instances(self, db_session: AsyncSession):
        """Test that different learners get separate instances."""
        orchestrator = PrivateBrainOrchestrator(db_session)

        # Request for learner 1
        request1 = PrivateBrainRequestCreate(learner_id=1, request_source="test")
        instance1, is_new1 = await orchestrator.request_private_brain(request1)

        # Request for learner 2
        request2 = PrivateBrainRequestCreate(learner_id=2, request_source="test")
        instance2, is_new2 = await orchestrator.request_private_brain(request2)

        assert is_new1 is True
        assert is_new2 is True
        assert instance1.id != instance2.id
        assert instance1.learner_id == 1
        assert instance2.learner_id == 2

    @pytest.mark.asyncio
    async def test_request_validation(self, client: AsyncClient):
        """Test request validation."""
        # Test with missing learner_id
        response = await client.post("/private-brain/request", json={})
        assert response.status_code == 422

        # Test with invalid learner_id type
        response = await client.post("/private-brain/request", json={"learner_id": "invalid"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_request_with_optional_fields(self, client: AsyncClient, sample_learner_id: int):
        """Test request with optional fields."""
        request_data = {
            "learner_id": sample_learner_id,
            "request_source": "custom-service",
            "request_id": "custom-id-456",
        }

        response = await client.post("/private-brain/request", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["learner_id"] == sample_learner_id
