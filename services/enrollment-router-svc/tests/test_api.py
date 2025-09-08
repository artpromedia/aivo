"""
API integration tests for enrollment router service.
"""

from unittest.mock import patch

import pytest


class TestEnrollmentAPI:
    """Test enrollment API endpoints."""

    @pytest.mark.asyncio
    async def test_enroll_district_path_api(
        self, client, district_allocation, sample_learner_profile, sample_district_context
    ):
        """Test enrollment API for district path."""
        request_data = {
            "learner_profile": sample_learner_profile,
            "context": sample_district_context,
        }

        response = await client.post("/enroll", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["provision_source"] == "district"
        assert data["status"] == "completed"
        assert data["tenant_id"] == 1
        assert data["seats_reserved"] == 1
        assert data["decision_id"] > 0
        assert "district allocation" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_enroll_parent_path_api(
        self, client, sample_learner_profile, sample_parent_context
    ):
        """Test enrollment API for parent path."""
        with patch("app.services.PaymentService.create_checkout_session") as mock_checkout:
            mock_checkout.return_value = {
                "session_id": "cs_test_123",
                "session_url": "https://checkout.stripe.com/pay/cs_test_123",
                "subscription_id": 1,
            }

            request_data = {
                "learner_profile": sample_learner_profile,
                "context": sample_parent_context,
            }

            response = await client.post("/enroll", json=request_data)

            assert response.status_code == 200
            data = response.json()

            assert data["provision_source"] == "parent"
            assert data["status"] == "checkout_required"
            assert data["guardian_id"] == "guardian_123"
            assert data["checkout_session_id"] == "cs_test_123"
            assert data["checkout_url"] == "https://checkout.stripe.com/pay/cs_test_123"
            assert data["decision_id"] > 0

    @pytest.mark.asyncio
    async def test_enroll_validation_error(self, client):
        """Test enrollment API validation error."""
        # Missing required fields
        request_data = {
            "learner_profile": {
                "email": "test@example.com"
                # Missing first_name and last_name
            },
            "context": {
                "source": "test"
                # Missing tenant_id or guardian_id
            },
        }

        response = await client.post("/enroll", json=request_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_enrollment_decision(self, client, enrollment_decision):
        """Test getting enrollment decision by ID."""
        response = await client.get(f"/enrollments/{enrollment_decision.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["decision_id"] == enrollment_decision.id
        assert data["provision_source"] == "district"
        assert data["status"] == "completed"
        assert data["learner_profile"]["email"] == "test@example.com"
        assert data["tenant_id"] == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_enrollment_decision(self, client):
        """Test getting nonexistent enrollment decision."""
        response = await client.get("/enrollments/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_enrollment_decisions(self, client, enrollment_decision):
        """Test listing enrollment decisions."""
        response = await client.get("/enrollments")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1

        # Find our decision in the list
        found_decision = next((d for d in data if d["decision_id"] == enrollment_decision.id), None)
        assert found_decision is not None
        assert found_decision["learner_profile"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_list_enrollment_decisions_with_tenant_filter(self, client, enrollment_decision):
        """Test listing enrollment decisions filtered by tenant."""
        response = await client.get("/enrollments?tenant_id=1")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # All returned decisions should have tenant_id = 1
        for decision in data:
            assert decision["tenant_id"] == 1

    @pytest.mark.asyncio
    async def test_list_enrollment_decisions_with_guardian_filter(self, client):
        """Test listing enrollment decisions filtered by guardian."""
        response = await client.get("/enrollments?guardian_id=guardian_123")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # All returned decisions should have guardian_id = guardian_123
        for decision in data:
            if decision["guardian_id"] is not None:
                assert decision["guardian_id"] == "guardian_123"


class TestDistrictSeatAPI:
    """Test district seat management API endpoints."""

    @pytest.mark.asyncio
    async def test_create_district_allocation(self, client):
        """Test creating district seat allocation."""
        request_data = {"tenant_id": 2, "total_seats": 100}

        response = await client.post("/districts/seats", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["tenant_id"] == 2
        assert data["total_seats"] == 100
        assert data["reserved_seats"] == 0
        assert data["used_seats"] == 0
        assert data["available_seats"] == 100
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_district_allocation(self, client, district_allocation):
        """Test getting district seat allocation."""
        response = await client.get(f"/districts/{district_allocation.tenant_id}/seats")

        assert response.status_code == 200
        data = response.json()

        assert data["tenant_id"] == district_allocation.tenant_id
        assert data["total_seats"] == district_allocation.total_seats
        assert data["available_seats"] == district_allocation.available_seats

    @pytest.mark.asyncio
    async def test_get_nonexistent_district_allocation(self, client):
        """Test getting nonexistent district allocation."""
        response = await client.get("/districts/999/seats")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_district_allocation(self, client, district_allocation):
        """Test updating district seat allocation."""
        request_data = {"total_seats": 150, "is_active": True}

        response = await client.put(
            f"/districts/{district_allocation.tenant_id}/seats", json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_seats"] == 150
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_district_allocations(self, client, district_allocation):
        """Test listing district allocations."""
        response = await client.get("/districts")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1

        # Find our allocation in the list
        found_allocation = next(
            (a for a in data if a["tenant_id"] == district_allocation.tenant_id), None
        )
        assert found_allocation is not None
        assert found_allocation["total_seats"] == district_allocation.total_seats

    @pytest.mark.asyncio
    async def test_list_active_district_allocations_only(self, client, district_allocation):
        """Test listing only active district allocations."""
        # Make sure our allocation is active
        assert district_allocation.is_active is True

        response = await client.get("/districts?active_only=true")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # All returned allocations should be active
        for allocation in data:
            assert allocation["is_active"] is True


class TestHealthAPI:
    """Test health check API."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "enrollment-router"
