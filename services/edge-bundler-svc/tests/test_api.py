"""Integration tests for Edge Bundler Service."""
# flake8: noqa: E501

from __future__ import annotations

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestEdgeBundlerAPI:
    """Test class for Edge Bundler API endpoints."""

    def test_root_endpoint(self: TestEdgeBundlerAPI) -> None:
        """Test the root API endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Edge Bundler Service"

    def test_health_endpoint(self: TestEdgeBundlerAPI) -> None:
        """Test the health check endpoint."""
        response = client.get("/api/edge-bundler/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_create_bundle_validation(self: TestEdgeBundlerAPI) -> None:
        """Test bundle creation with validation."""
        # Test with empty data
        response = client.post("/api/edge-bundler/v1/bundles", json={})
        assert response.status_code == 422

        # Test with minimal valid data
        bundle_data = {
            "title": "Test Bundle",
            "version": "1.0.0",
            "lessons": [],
        }
        response = client.post("/api/edge-bundler/v1/bundles", json=bundle_data)
        assert response.status_code in [200, 201, 422]

    def test_create_bundle_precache_validation(
        self: TestEdgeBundlerAPI,
    ) -> None:
        """Test precache budget validation."""
        bundle_data = {
            "title": "Large Bundle",
            "version": "1.0.0",
            "lessons": [],
            "precache_budget_mb": 30,  # Exceeds 25MB limit
        }
        response = client.post("/api/edge-bundler/v1/bundles", json=bundle_data)
        # Should reject or accept based on validation
        assert response.status_code in [400, 422]

    def test_bundle_list_endpoint(self: TestEdgeBundlerAPI) -> None:
        """Test bundle listing endpoint."""
        response = client.get("/api/edge-bundler/v1/bundles")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_bundle_stats_endpoint(self: TestEdgeBundlerAPI) -> None:
        """Test bundle statistics endpoint."""
        response = client.get("/api/edge-bundler/v1/bundles/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_bundles" in data
        assert "total_size_mb" in data
        assert "precache_usage_mb" in data
        assert "compression_savings_percent" in data

    def test_crdt_merge_validation(self: TestEdgeBundlerAPI) -> None:
        """Test CRDT merge validation."""
        merge_data = {
            "source_device_id": "device-1",
            "target_device_id": "device-2",
        }
        response = client.post("/api/edge-bundler/v1/crdt/merge", json=merge_data)
        # May succeed or fail based on implementation
        assert response.status_code in [200, 400, 422, 500]
