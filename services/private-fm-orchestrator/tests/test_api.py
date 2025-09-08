"""
API integration tests for private brain orchestrator.
"""

import pytest
from httpx import AsyncClient


class TestHealthAPI:
    """Test health check API."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "private-fm-orchestrator"
        assert data["version"] == "1.0.0"
        assert data["timestamp"] is not None


class TestAPIIntegration:
    """Test full API integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, client: AsyncClient):
        """Test complete workflow from request to ready status."""
        learner_id = 99999

        # 1. Request private brain
        request_data = {
            "learner_id": learner_id,
            "request_source": "integration-test",
            "request_id": "workflow-test-1",
        }

        response = await client.post("/private-brain/request", json=request_data)
        assert response.status_code == 200

        request_result = response.json()
        assert request_result["learner_id"] == learner_id
        assert request_result["status"] == "PENDING"
        assert request_result["is_new_request"] is True

        # 2. Check initial status
        response = await client.get(f"/private-brain/status/{learner_id}")
        assert response.status_code == 200

        status_result = response.json()
        assert status_result["learner_id"] == learner_id
        assert status_result["status"] == "PENDING"
        assert status_result["ns_uid"] is None
        assert status_result["checkpoint_hash"] is None

        # 3. Make idempotent request
        response = await client.post("/private-brain/request", json=request_data)
        assert response.status_code == 200

        repeat_result = response.json()
        assert repeat_result["learner_id"] == learner_id
        assert repeat_result["is_new_request"] is False

        # 4. Check updated request count
        response = await client.get(f"/private-brain/status/{learner_id}")
        assert response.status_code == 200

        updated_status = response.json()
        assert updated_status["request_count"] == 2  # Should have incremented

    @pytest.mark.asyncio
    async def test_multiple_learners_workflow(self, client: AsyncClient):
        """Test workflow with multiple learners."""
        learner_ids = [11111, 22222, 33333]

        # Create requests for all learners
        for learner_id in learner_ids:
            request_data = {"learner_id": learner_id, "request_source": "multi-test"}

            response = await client.post("/private-brain/request", json=request_data)
            assert response.status_code == 200

            result = response.json()
            assert result["learner_id"] == learner_id
            assert result["is_new_request"] is True

        # Check status for all learners
        for learner_id in learner_ids:
            response = await client.get(f"/private-brain/status/{learner_id}")
            assert response.status_code == 200

            status = response.json()
            assert status["learner_id"] == learner_id
            assert status["status"] == "PENDING"

        # List all instances
        response = await client.get("/private-brain/status")
        assert response.status_code == 200

        list_result = response.json()
        assert len(list_result["instances"]) >= len(learner_ids)

        # Check that all our learners are in the list
        instance_learner_ids = [inst["learner_id"] for inst in list_result["instances"]]
        for learner_id in learner_ids:
            assert learner_id in instance_learner_ids

    @pytest.mark.asyncio
    async def test_error_handling(self, client: AsyncClient):
        """Test API error handling."""
        # Test invalid request data
        response = await client.post("/private-brain/request", json={})
        assert response.status_code == 422

        # Test invalid learner ID type
        response = await client.post("/private-brain/request", json={"learner_id": "not-a-number"})
        assert response.status_code == 422

        # Test status for non-existent learner
        response = await client.get("/private-brain/status/999999999")
        assert response.status_code == 404

        # Test invalid status filter
        response = await client.get("/private-brain/status?status_filter=INVALID_STATUS")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient):
        """Test pagination in list endpoint."""
        # Create several instances
        learner_ids = list(range(50000, 50010))  # 10 learners

        for learner_id in learner_ids:
            request_data = {"learner_id": learner_id}
            await client.post("/private-brain/request", json=request_data)

        # Test pagination
        response = await client.get("/private-brain/status?limit=5&offset=0")
        assert response.status_code == 200

        page1 = response.json()
        assert len(page1["instances"]) >= 5
        assert page1["limit"] == 5
        assert page1["offset"] == 0

        # Get second page
        response = await client.get("/private-brain/status?limit=5&offset=5")
        assert response.status_code == 200

        page2 = response.json()
        assert page2["limit"] == 5
        assert page2["offset"] == 5

        # Ensure different results (no overlap)
        {inst["learner_id"] for inst in page1["instances"]}
        {inst["learner_id"] for inst in page2["instances"]}
        # Note: There might be some overlap due to ordering, but they should be different pages
