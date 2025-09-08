"""
Tests for private brain status functionality and state transitions.
"""

from datetime import UTC, datetime

import pytest
from app.models import PrivateBrainInstance, PrivateBrainStatus
from app.schemas import PrivateBrainInstanceUpdate, PrivateBrainRequestCreate
from app.services import PrivateBrainOrchestrator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestPrivateBrainStatus:
    """Test private brain status functionality."""

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, client: AsyncClient):
        """Test getting status for non-existent learner."""
        response = await client.get("/private-brain/status/999999")

        assert response.status_code == 404
        response_data = response.json()
        assert (
            "not found" in response_data["detail"].lower()
            or "no private brain" in response_data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_get_status_pending(self, client: AsyncClient, sample_request_data: dict):
        """Test getting status for pending instance."""
        # Create request first
        await client.post("/private-brain/request", json=sample_request_data)

        # Get status
        learner_id = sample_request_data["learner_id"]
        response = await client.get(f"/private-brain/status/{learner_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["learner_id"] == learner_id
        assert data["status"] == "PENDING"
        assert data["ns_uid"] is None
        assert data["checkpoint_hash"] is None
        assert data["request_count"] == 1
        assert data["error_message"] is None
        assert data["retry_count"] == 0

    @pytest.mark.asyncio
    async def test_status_transitions(self, db_session: AsyncSession, sample_request_data: dict):
        """Test status transitions from PENDING to READY."""
        orchestrator = PrivateBrainOrchestrator(db_session)
        request_data = PrivateBrainRequestCreate(**sample_request_data)

        # Create instance
        instance, _ = await orchestrator.request_private_brain(request_data)
        assert instance.status == PrivateBrainStatus.PENDING

        # Update to CLONING
        updated = await orchestrator.update_instance(
            instance.id, PrivateBrainInstanceUpdate(status=PrivateBrainStatus.CLONING)
        )
        assert updated.status == PrivateBrainStatus.CLONING

        # Update to READY with namespace and checkpoint
        updated = await orchestrator.update_instance(
            instance.id,
            PrivateBrainInstanceUpdate(
                status=PrivateBrainStatus.READY,
                ns_uid="ns-test123",
                checkpoint_hash="checkpoint-hash-456",
                ready_at=datetime.now(UTC),
            ),
        )
        assert updated.status == PrivateBrainStatus.READY
        assert updated.ns_uid == "ns-test123"
        assert updated.checkpoint_hash == "checkpoint-hash-456"
        assert updated.ready_at is not None

    @pytest.mark.asyncio
    async def test_error_status(self, db_session: AsyncSession, sample_request_data: dict):
        """Test error status handling."""
        orchestrator = PrivateBrainOrchestrator(db_session)
        request_data = PrivateBrainRequestCreate(**sample_request_data)

        # Create instance
        instance, _ = await orchestrator.request_private_brain(request_data)

        # Update to ERROR
        error_message = "Failed to clone namespace"
        updated = await orchestrator.update_instance(
            instance.id,
            PrivateBrainInstanceUpdate(
                status=PrivateBrainStatus.ERROR, error_message=error_message
            ),
        )

        assert updated.status == PrivateBrainStatus.ERROR
        assert updated.error_message == error_message

    @pytest.mark.asyncio
    async def test_get_ready_status_via_api(
        self, client: AsyncClient, db_session: AsyncSession, sample_request_data: dict
    ):
        """Test getting READY status via API."""
        # Create instance directly in database
        instance = PrivateBrainInstance(
            learner_id=sample_request_data["learner_id"],
            status=PrivateBrainStatus.READY,
            ns_uid="ns-ready123",
            checkpoint_hash="checkpoint-ready456",
            request_count=1,
        )

        db_session.add(instance)
        await db_session.commit()
        await db_session.refresh(instance)

        # Get status via API
        learner_id = sample_request_data["learner_id"]
        response = await client.get(f"/private-brain/status/{learner_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "READY"
        assert data["ns_uid"] == "ns-ready123"
        assert data["checkpoint_hash"] == "checkpoint-ready456"

    @pytest.mark.asyncio
    async def test_async_cloning_process(self, db_session: AsyncSession, sample_learner_id: int):
        """Test async cloning process simulation (simplified for testing)."""
        orchestrator = PrivateBrainOrchestrator(db_session)

        # Create new request (without background task)
        request_data = PrivateBrainRequestCreate(
            learner_id=sample_learner_id, required_capability="test", priority=1
        )
        instance, _ = await orchestrator.request_private_brain(request_data)

        # Manually simulate the cloning process for testing
        await orchestrator.update_instance(
            instance.id, PrivateBrainInstanceUpdate(status=PrivateBrainStatus.CLONING)
        )

        # Simulate completion
        await orchestrator.update_instance(
            instance.id,
            PrivateBrainInstanceUpdate(
                status=PrivateBrainStatus.READY,
                ns_uid="test-ns-uid",
                checkpoint_hash="test-checkpoint-hash",
                ready_at=datetime.now(UTC),
            ),
        )

        # Verify final state
        final_instance = await orchestrator.get_status(sample_learner_id)
        assert final_instance.status == PrivateBrainStatus.READY
        assert final_instance.ns_uid == "test-ns-uid"
        assert final_instance.checkpoint_hash == "test-checkpoint-hash"

    @pytest.mark.asyncio
    async def test_list_instances_endpoint(self, client: AsyncClient, sample_request_data: dict):
        """Test the list instances endpoint."""
        # Create a few instances
        await client.post("/private-brain/request", json=sample_request_data)

        request_data_2 = {
            **sample_request_data,
            "learner_id": sample_request_data["learner_id"] + 1,
        }
        await client.post("/private-brain/request", json=request_data_2)

        # List instances
        response = await client.get("/private-brain/status")

        assert response.status_code == 200
        data = response.json()

        assert "instances" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert len(data["instances"]) >= 2

    @pytest.mark.asyncio
    async def test_list_instances_with_filters(
        self, client: AsyncClient, sample_request_data: dict
    ):
        """Test listing instances with status filter."""
        # Create instance
        await client.post("/private-brain/request", json=sample_request_data)

        # List with PENDING filter
        response = await client.get("/private-brain/status?status_filter=PENDING")

        assert response.status_code == 200
        data = response.json()

        assert len(data["instances"]) >= 1
        for instance in data["instances"]:
            assert instance["status"] == "PENDING"

    @pytest.mark.asyncio
    async def test_ready_at_timestamp(self, db_session: AsyncSession, sample_request_data: dict):
        """Test that ready_at timestamp is set when status becomes READY."""
        orchestrator = PrivateBrainOrchestrator(db_session)
        request_data = PrivateBrainRequestCreate(**sample_request_data)

        # Create instance
        instance, _ = await orchestrator.request_private_brain(request_data)
        assert instance.ready_at is None

        # Update to READY
        updated = await orchestrator.update_instance(
            instance.id,
            PrivateBrainInstanceUpdate(
                status=PrivateBrainStatus.READY,
                ns_uid="ns-test",
                checkpoint_hash="checkpoint-test",
                ready_at=datetime.now(UTC),
            ),
        )

        assert updated.ready_at is not None
        assert updated.ready_at > instance.created_at
