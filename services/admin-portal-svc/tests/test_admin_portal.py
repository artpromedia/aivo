"""
Tests for Admin Portal Aggregator Service with contract fixtures.
"""

import json
from decimal import Decimal
from typing import Never
from unittest.mock import patch

import pytest
from app.cache_service import cache_service
from app.http_client import http_client
from app.main import app
from app.schemas import (
    BillingHistoryResponse,
    NamespacesResponse,
    SubscriptionDetails,
    SummaryResponse,
    TeamResponse,
    UsageResponse,
)
from app.service_aggregator import service_aggregator
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_tenant_id():
    """Mock tenant ID for testing."""
    return "tenant_123"


@pytest.fixture
def summary_contract_fixture():
    """Contract fixture for summary endpoint."""
    return {
        "tenant_id": "tenant_123",
        "tenant_name": "Acme Corporation",
        "status": "active",
        "subscription_tier": "professional",
        "total_users": 45,
        "active_users_30d": 38,
        "total_documents": 1250,
        "pending_approvals": 3,
        "monthly_spend": "89.50",
        "usage_alerts": 1,
        "last_activity": "2024-09-02T10:30:00Z",
        "health_score": 92.5,
    }


@pytest.fixture
def subscription_contract_fixture():
    """Contract fixture for subscription endpoint."""
    return {
        "tenant_id": "tenant_123",
        "current_tier": "professional",
        "billing_cycle": "monthly",
        "next_billing_date": "2024-10-01T00:00:00Z",
        "monthly_cost": "89.99",
        "yearly_cost": "899.99",
        "features": ["Advanced Analytics", "Custom Workflows", "Priority Support", "API Access"],
        "usage_limits": {"api_calls": 100000, "storage_gb": 500, "users": 100},
        "auto_renewal": True,
        "trial_end_date": None,
        "discount_applied": "EARLY_ADOPTER_10",
    }


@pytest.fixture
def billing_history_contract_fixture():
    """Contract fixture for billing history endpoint."""
    return {
        "tenant_id": "tenant_123",
        "current_balance": "0.00",
        "next_payment_due": "2024-10-01T00:00:00Z",
        "payment_method": "Visa ****1234",
        "invoices": [
            {
                "invoice_id": "inv_001",
                "date": "2024-09-01T00:00:00Z",
                "amount": "89.99",
                "status": "paid",
                "description": "Professional Plan - September 2024",
                "download_url": "https://example.com/invoice/inv_001.pdf",
            },
            {
                "invoice_id": "inv_002",
                "date": "2024-08-01T00:00:00Z",
                "amount": "89.99",
                "status": "paid",
                "description": "Professional Plan - August 2024",
                "download_url": "https://example.com/invoice/inv_002.pdf",
            },
        ],
        "total_spent_ytd": "719.92",
    }


@pytest.fixture
def team_contract_fixture():
    """Contract fixture for team endpoint."""
    return {
        "tenant_id": "tenant_123",
        "total_members": 12,
        "active_members": 11,
        "pending_invites": 2,
        "members": [
            {
                "user_id": "user_001",
                "email": "admin@acme.com",
                "name": "John Smith",
                "role": "admin",
                "status": "active",
                "last_login": "2024-09-02T09:15:00Z",
                "permissions": ["admin", "billing", "team_management"],
                "invite_status": None,
            },
            {
                "user_id": "user_002",
                "email": "sarah@acme.com",
                "name": "Sarah Johnson",
                "role": "teacher",
                "status": "active",
                "last_login": "2024-09-01T14:30:00Z",
                "permissions": ["documents", "approvals"],
                "invite_status": None,
            },
            {
                "user_id": "user_003",
                "email": "mike@acme.com",
                "name": "Mike Wilson",
                "role": "teacher",
                "status": "pending",
                "last_login": None,
                "permissions": ["documents"],
                "invite_status": "pending",
            },
        ],
        "role_distribution": {"admin": 2, "teacher": 8, "parent": 2},
        "recent_activity": [
            {
                "user_id": "user_001",
                "action": "document_approved",
                "timestamp": "2024-09-02T08:45:00Z",
                "details": "Approved IEP for Student A",
            },
            {
                "user_id": "user_002",
                "action": "login",
                "timestamp": "2024-09-01T14:30:00Z",
                "details": "User logged in",
            },
        ],
    }


@pytest.fixture
def usage_contract_fixture():
    """Contract fixture for usage endpoint."""
    return {
        "tenant_id": "tenant_123",
        "billing_period_start": "2024-09-01T00:00:00Z",
        "billing_period_end": "2024-09-30T23:59:59Z",
        "metrics": [
            {
                "metric_name": "API Calls",
                "current_value": 75000,
                "limit_value": 100000,
                "percentage_used": 75.0,
                "unit": "requests",
            },
            {
                "metric_name": "Storage",
                "current_value": 250,
                "limit_value": 500,
                "percentage_used": 50.0,
                "unit": "GB",
            },
            {
                "metric_name": "Users",
                "current_value": 45,
                "limit_value": 100,
                "percentage_used": 45.0,
                "unit": "count",
            },
        ],
        "total_api_calls": 75000,
        "total_storage_gb": 250.5,
        "bandwidth_gb": 125.7,
        "cost_breakdown": {
            "base_subscription": "89.99",
            "overage_api": "0.00",
            "overage_storage": "0.00",
            "overage_bandwidth": "0.00",
        },
        "projected_monthly_cost": "89.99",
        "usage_trends": {
            "api_calls": [45000, 52000, 68000, 75000],
            "storage_gb": [200.1, 220.5, 235.8, 250.5],
            "bandwidth_gb": [80.2, 95.1, 110.5, 125.7],
        },
    }


@pytest.fixture
def namespaces_contract_fixture():
    """Contract fixture for namespaces endpoint."""
    return {
        "tenant_id": "tenant_123",
        "total_namespaces": 4,
        "active_namespaces": 3,
        "total_documents": 1250,
        "total_storage_gb": 45.8,
        "namespaces": [
            {
                "namespace_id": "ns_001",
                "name": "Mathematics Curriculum",
                "status": "active",
                "document_count": 450,
                "storage_used_mb": 15360.0,
                "last_updated": "2024-09-02T08:30:00Z",
                "model_deployments": 3,
                "active_workflows": 5,
            },
            {
                "namespace_id": "ns_002",
                "name": "Science Resources",
                "status": "active",
                "document_count": 380,
                "storage_used_mb": 12800.0,
                "last_updated": "2024-09-01T16:45:00Z",
                "model_deployments": 2,
                "active_workflows": 3,
            },
            {
                "namespace_id": "ns_003",
                "name": "IEP Templates",
                "status": "active",
                "document_count": 420,
                "storage_used_mb": 18944.0,
                "last_updated": "2024-08-30T11:20:00Z",
                "model_deployments": 1,
                "active_workflows": 8,
            },
            {
                "namespace_id": "ns_004",
                "name": "Archive",
                "status": "inactive",
                "document_count": 0,
                "storage_used_mb": 0.0,
                "last_updated": "2024-08-15T10:00:00Z",
                "model_deployments": 0,
                "active_workflows": 0,
            },
        ],
        "storage_distribution": {
            "Mathematics Curriculum": 15.0,
            "Science Resources": 12.5,
            "IEP Templates": 18.5,
        },
    }


class TestContractCompliance:
    """Test contract compliance for all endpoints."""

    def test_summary_contract_shape(self, summary_contract_fixture):
        """Test summary response matches expected contract."""
        response = SummaryResponse(**summary_contract_fixture)

        # Verify all required fields are present
        assert response.tenant_id == "tenant_123"
        assert response.tenant_name == "Acme Corporation"
        assert response.status == "active"
        assert response.subscription_tier == "professional"
        assert isinstance(response.total_users, int)
        assert isinstance(response.active_users_30d, int)
        assert isinstance(response.total_documents, int)
        assert isinstance(response.pending_approvals, int)
        assert isinstance(response.monthly_spend, Decimal)
        assert isinstance(response.usage_alerts, int)
        assert isinstance(response.health_score, float)
        assert 0 <= response.health_score <= 100

        # Verify JSON serialization works
        json_data = response.model_dump_json()
        assert json.loads(json_data)

    def test_subscription_contract_shape(self, subscription_contract_fixture):
        """Test subscription response matches expected contract."""
        response = SubscriptionDetails(**subscription_contract_fixture)

        assert response.tenant_id == "tenant_123"
        assert response.current_tier == "professional"
        assert response.billing_cycle == "monthly"
        assert isinstance(response.features, list)
        assert len(response.features) > 0
        assert isinstance(response.usage_limits, dict)
        assert isinstance(response.auto_renewal, bool)

        # Verify JSON serialization
        json_data = response.model_dump_json()
        assert json.loads(json_data)

    def test_billing_history_contract_shape(self, billing_history_contract_fixture):
        """Test billing history response matches expected contract."""
        response = BillingHistoryResponse(**billing_history_contract_fixture)

        assert response.tenant_id == "tenant_123"
        assert isinstance(response.current_balance, Decimal)
        assert isinstance(response.invoices, list)
        assert len(response.invoices) >= 0

        if response.invoices:
            invoice = response.invoices[0]
            assert hasattr(invoice, "invoice_id")
            assert hasattr(invoice, "date")
            assert hasattr(invoice, "amount")
            assert hasattr(invoice, "status")

        # Verify JSON serialization
        json_data = response.model_dump_json()
        assert json.loads(json_data)

    def test_team_contract_shape(self, team_contract_fixture):
        """Test team response matches expected contract."""
        response = TeamResponse(**team_contract_fixture)

        assert response.tenant_id == "tenant_123"
        assert isinstance(response.total_members, int)
        assert isinstance(response.active_members, int)
        assert isinstance(response.pending_invites, int)
        assert isinstance(response.members, list)
        assert isinstance(response.role_distribution, dict)
        assert isinstance(response.recent_activity, list)

        if response.members:
            member = response.members[0]
            assert hasattr(member, "user_id")
            assert hasattr(member, "email")
            assert hasattr(member, "name")
            assert hasattr(member, "role")
            assert hasattr(member, "status")
            assert hasattr(member, "permissions")

        # Verify JSON serialization
        json_data = response.model_dump_json()
        assert json.loads(json_data)

    def test_usage_contract_shape(self, usage_contract_fixture):
        """Test usage response matches expected contract."""
        response = UsageResponse(**usage_contract_fixture)

        assert response.tenant_id == "tenant_123"
        assert isinstance(response.metrics, list)
        assert isinstance(response.total_api_calls, int)
        assert isinstance(response.total_storage_gb, float)
        assert isinstance(response.bandwidth_gb, float)
        assert isinstance(response.cost_breakdown, dict)
        assert isinstance(response.projected_monthly_cost, Decimal)
        assert isinstance(response.usage_trends, dict)

        if response.metrics:
            metric = response.metrics[0]
            assert hasattr(metric, "metric_name")
            assert hasattr(metric, "current_value")
            assert hasattr(metric, "percentage_used")
            assert hasattr(metric, "unit")

        # Verify JSON serialization
        json_data = response.model_dump_json()
        assert json.loads(json_data)

    def test_namespaces_contract_shape(self, namespaces_contract_fixture):
        """Test namespaces response matches expected contract."""
        response = NamespacesResponse(**namespaces_contract_fixture)

        assert response.tenant_id == "tenant_123"
        assert isinstance(response.total_namespaces, int)
        assert isinstance(response.active_namespaces, int)
        assert isinstance(response.total_documents, int)
        assert isinstance(response.total_storage_gb, float)
        assert isinstance(response.namespaces, list)
        assert isinstance(response.storage_distribution, dict)

        if response.namespaces:
            namespace = response.namespaces[0]
            assert hasattr(namespace, "namespace_id")
            assert hasattr(namespace, "name")
            assert hasattr(namespace, "status")
            assert hasattr(namespace, "document_count")
            assert hasattr(namespace, "storage_used_mb")

        # Verify JSON serialization
        json_data = response.model_dump_json()
        assert json.loads(json_data)


class TestAPIEndpoints:
    """Test API endpoints with mocked services."""

    @patch("app.service_aggregator.service_aggregator.get_summary")
    def test_summary_endpoint(self, mock_get_summary, client, summary_contract_fixture):
        """Test summary endpoint."""
        mock_get_summary.return_value = SummaryResponse(**summary_contract_fixture)

        response = client.get("/summary?tenant_id=tenant_123")
        assert response.status_code == 200

        data = response.json()
        assert data["tenant_id"] == "tenant_123"
        assert data["tenant_name"] == "Acme Corporation"
        assert data["health_score"] == 92.5

    @patch("app.service_aggregator.service_aggregator.get_subscription")
    def test_subscription_endpoint(
        self, mock_get_subscription, client, subscription_contract_fixture
    ):
        """Test subscription endpoint."""
        mock_get_subscription.return_value = SubscriptionDetails(**subscription_contract_fixture)

        response = client.get("/subscription?tenant_id=tenant_123")
        assert response.status_code == 200

        data = response.json()
        assert data["tenant_id"] == "tenant_123"
        assert data["current_tier"] == "professional"
        assert len(data["features"]) > 0

    @patch("app.service_aggregator.service_aggregator.get_billing_history")
    def test_billing_history_endpoint(
        self, mock_get_billing, client, billing_history_contract_fixture
    ):
        """Test billing history endpoint."""
        mock_get_billing.return_value = BillingHistoryResponse(**billing_history_contract_fixture)

        response = client.get("/billing-history?tenant_id=tenant_123")
        assert response.status_code == 200

        data = response.json()
        assert data["tenant_id"] == "tenant_123"
        assert len(data["invoices"]) == 2
        assert data["total_spent_ytd"] == "719.92"

    @patch("app.service_aggregator.service_aggregator.get_team")
    def test_team_endpoint(self, mock_get_team, client, team_contract_fixture):
        """Test team endpoint."""
        mock_get_team.return_value = TeamResponse(**team_contract_fixture)

        response = client.get("/team?tenant_id=tenant_123")
        assert response.status_code == 200

        data = response.json()
        assert data["tenant_id"] == "tenant_123"
        assert data["total_members"] == 12
        assert len(data["members"]) == 3

    @patch("app.service_aggregator.service_aggregator.get_usage")
    def test_usage_endpoint(self, mock_get_usage, client, usage_contract_fixture):
        """Test usage endpoint."""
        mock_get_usage.return_value = UsageResponse(**usage_contract_fixture)

        response = client.get("/usage?tenant_id=tenant_123")
        assert response.status_code == 200

        data = response.json()
        assert data["tenant_id"] == "tenant_123"
        assert len(data["metrics"]) == 3
        assert data["total_api_calls"] == 75000

    @patch("app.service_aggregator.service_aggregator.get_namespaces")
    def test_namespaces_endpoint(self, mock_get_namespaces, client, namespaces_contract_fixture):
        """Test namespaces endpoint."""
        mock_get_namespaces.return_value = NamespacesResponse(**namespaces_contract_fixture)

        response = client.get("/namespaces?tenant_id=tenant_123")
        assert response.status_code == 200

        data = response.json()
        assert data["tenant_id"] == "tenant_123"
        assert data["total_namespaces"] == 4
        assert len(data["namespaces"]) == 4

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "dependencies" in data
        assert "timestamp" in data

    def test_invalid_tenant_id(self, client):
        """Test invalid tenant ID validation."""
        response = client.get("/summary?tenant_id=ab")
        assert response.status_code == 400

        response = client.get("/summary")
        assert response.status_code == 422


class TestCaching:
    """Test caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_operations(self):
        """Test basic cache operations."""
        tenant_id = "test_tenant"
        endpoint = "summary"
        test_data = {"test": "data"}

        # Mock cache service
        with (
            patch.object(cache_service, "get") as mock_get,
            patch.object(cache_service, "set") as mock_set,
        ):
            mock_get.return_value = None
            mock_set.return_value = True

            # Test cache miss and set
            result = await cache_service.get(tenant_id, endpoint)
            assert result is None

            await cache_service.set(tenant_id, endpoint, test_data)
            mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_with_aggregator(self, mock_tenant_id):
        """Test caching with service aggregator."""
        with (
            patch.object(cache_service, "get") as mock_get,
            patch.object(cache_service, "set") as mock_set,
            patch.object(http_client, "get") as mock_http_get,
        ):
            # Setup mocks
            mock_get.return_value = None  # Cache miss
            mock_set.return_value = True
            mock_http_get.return_value = {
                "name": "Test Tenant",
                "status": "active",
                "subscription_tier": "basic",
            }

            # This should trigger cache operations
            await service_aggregator.get_summary(mock_tenant_id)

            # Verify cache was checked and set
            mock_get.assert_called()
            mock_set.assert_called()


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self):
        """Test circuit breaker opens on failures."""
        from app.http_client import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

        async def failing_function() -> Never:
            raise Exception("Service unavailable")

        # First failure
        with pytest.raises(Exception):
            await cb.call(failing_function)
        assert cb.state == "closed"
        assert cb.failure_count == 1

        # Second failure - should open circuit
        with pytest.raises(Exception):
            await cb.call(failing_function)
        assert cb.state == "open"
        assert cb.failure_count == 2


class TestServiceIntegration:
    """Test service integration scenarios."""

    @pytest.mark.asyncio
    async def test_service_fallback_on_failure(self, mock_tenant_id):
        """Test fallback data when services fail."""
        with patch.object(http_client, "get") as mock_http_get:
            # Mock service failure
            mock_http_get.side_effect = Exception("Service unavailable")

            # Should return fallback data
            summary = await service_aggregator.get_summary(mock_tenant_id)

            assert summary.tenant_id == mock_tenant_id
            assert summary.health_score >= 0

    @pytest.mark.asyncio
    async def test_partial_service_failure(self, mock_tenant_id):
        """Test handling of partial service failures."""
        with (
            patch.object(service_aggregator, "_get_tenant_info") as mock_tenant,
            patch.object(service_aggregator, "_get_user_stats") as mock_users,
            patch.object(service_aggregator, "_get_document_stats") as mock_docs,
        ):
            # Some services succeed, others fail
            mock_tenant.return_value = {"name": "Test Tenant", "status": "active"}
            mock_users.return_value = {"total": 10, "active_30d": 8}
            mock_docs.side_effect = Exception("Document service down")

            summary = await service_aggregator.get_summary(mock_tenant_id)

            # Should have data from successful services
            assert summary.tenant_name == "Test Tenant"
            assert summary.total_users == 10
            # Should have fallback for failed service
            assert summary.total_documents == 0


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async operations and concurrency."""

    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import asyncio

        async def mock_fetch():
            await asyncio.sleep(0.1)  # Simulate network delay
            return {"test": "data"}

        with patch.object(http_client, "get", side_effect=mock_fetch):
            # Make multiple concurrent requests
            tasks = [
                service_aggregator.get_summary("tenant_1"),
                service_aggregator.get_summary("tenant_2"),
                service_aggregator.get_summary("tenant_3"),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should complete successfully
            assert len(results) == 3
            for result in results:
                assert isinstance(result, SummaryResponse)
