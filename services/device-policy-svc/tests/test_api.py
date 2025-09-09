"""Integration tests for policy API endpoints."""

from fastapi.testclient import TestClient

from app.main import app
from app.models import PolicyStatus, PolicyType

client = TestClient(app)


class TestPolicyAPI:
    """Test policy API endpoints."""

    def test_create_policy_endpoint(self) -> None:
        """Test policy creation endpoint."""
        policy_data = {
            "name": "Test Kiosk Policy",
            "description": "Test policy for kiosk mode",
            "policy_type": PolicyType.KIOSK.value,
            "config": {
                "mode": "single_app",
                "apps": [
                    {
                        "package_name": "com.aivo.study",
                        "app_name": "Aivo Study",
                        "auto_launch": True,
                        "allow_exit": False,
                        "fullscreen": True,
                    }
                ],
            },
            "priority": 100,
        }

        response = client.post("/policies", json=policy_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Kiosk Policy"
        assert data["policy_type"] == PolicyType.KIOSK.value
        assert data["status"] == PolicyStatus.DRAFT.value

    def test_list_policies_endpoint(self) -> None:
        """Test policy listing endpoint."""
        response = client.get("/policies")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_policy_endpoint(self) -> None:
        """Test policy retrieval endpoint."""
        # First create a policy
        policy_data = {
            "name": "Test Policy",
            "description": "Test description",
            "policy_type": PolicyType.NETWORK.value,
            "config": {
                "wifi_networks": [
                    {
                        "ssid": "SchoolWiFi",
                        "security": "WPA2",
                        "password": "school123",
                        "auto_connect": True,
                    }
                ],
                "mobile_data": {"enabled": False},
                "hotspot": {"enabled": False},
            },
            "priority": 50,
        }

        create_response = client.post("/policies", json=policy_data)
        assert create_response.status_code == 201

        policy_id = create_response.json()["policy_id"]

        # Now get the policy
        response = client.get(f"/policies/{policy_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["policy_id"] == policy_id
        assert data["name"] == "Test Policy"


class TestAllowlistAPI:
    """Test allowlist API endpoints."""

    def test_add_allowlist_entry_endpoint(self) -> None:
        """Test adding allowlist entry endpoint."""
        entry_data = {
            "entry_type": "domain",
            "value": "education.com",
            "category": "educational",
            "description": "Educational content site",
        }

        response = client.post("/allowlist", json=entry_data)

        assert response.status_code == 201
        data = response.json()
        assert data["entry_type"] == "domain"
        assert data["value"] == "education.com"
        assert data["category"] == "educational"
        assert data["is_active"] is True

    def test_get_active_allowlist_endpoint(self) -> None:
        """Test retrieving active allowlist endpoint."""
        response = client.get("/allowlist/active")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_bulk_add_allowlist_endpoint(self) -> None:
        """Test bulk adding allowlist entries endpoint."""
        entries_data = {
            "entries": [
                {
                    "entry_type": "domain",
                    "value": "khan-academy.org",
                    "category": "educational",
                },
                {
                    "entry_type": "url",
                    "value": "https://coursera.org/learn",
                    "category": "educational",
                },
            ]
        }

        response = client.post("/allowlist/bulk", json=entries_data)

        assert response.status_code == 201
        data = response.json()
        assert len(data) == 2
        assert all(entry["is_active"] for entry in data)


class TestDevicePolicyAPI:
    """Test device policy assignment endpoints."""

    def test_assign_policy_to_device_endpoint(self) -> None:
        """Test assigning policy to device endpoint."""
        # First create a policy
        policy_data = {
            "name": "Device Test Policy",
            "description": "Test policy for device assignment",
            "policy_type": PolicyType.KIOSK.value,
            "config": {"mode": "single_app", "apps": []},
            "priority": 75,
        }

        policy_response = client.post("/policies", json=policy_data)
        assert policy_response.status_code == 201

        policy_id = policy_response.json()["policy_id"]
        device_id = "test-device-001"

        # Assign policy to device
        assignment_data = {"policy_id": policy_id, "device_id": device_id}

        response = client.post("/device-policies", json=assignment_data)

        assert response.status_code == 201
        data = response.json()
        assert data["policy_id"] == policy_id
        assert data["device_id"] == device_id

    def test_get_device_policies_endpoint(self) -> None:
        """Test retrieving device policies endpoint."""
        device_id = "test-device-001"

        response = client.get(f"/device-policies/{device_id}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestPolicySyncAPI:
    """Test policy synchronization endpoints."""

    def test_policy_sync_endpoint(self) -> None:
        """Test policy sync endpoint."""
        device_id = "test-device-sync"

        response = client.get(
            "/policy/sync",
            params={"device_id": device_id, "timeout": 1},
        )

        # Should return 200 with sync response or 204 for no changes
        assert response.status_code in [200, 204]
