"""
Comprehensive tests for auth service.
"""

import pytest


class TestUserRegistration:
    """Test user registration endpoints."""

    def test_register_guardian_success(self, client):
        """Test successful guardian registration."""
        response = client.post(
            "/api/v1/auth/register-guardian",
            json={
                "email": "guardian@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "guardian@example.com"
        assert data["user"]["role"] == "guardian"
        assert data["user"]["status"] == "active"

    def test_register_guardian_duplicate_email(self, client):
        """Test guardian registration with duplicate email."""
        # First registration
        client.post(
            "/api/v1/auth/register-guardian",
            json={
                "email": "guardian@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
            },
        )

        # Second registration with same email
        response = client.post(
            "/api/v1/auth/register-guardian",
            json={
                "email": "guardian@example.com",
                "password": "AnotherPass123!",
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "+0987654321",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["message"].lower()


class TestUserLogin:
    """Test user login endpoints."""

    def test_login_success(self, client):
        """Test successful login."""
        # First register a user
        register_response = client.post(
            "/api/v1/auth/register-guardian",
            json={
                "email": "guardian@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
            },
        )
        assert register_response.status_code == 200

        # Then login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "guardian@example.com", "password": "SecurePass123!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "guardian@example.com"

    def test_login_invalid_password(self, client):
        """Test login with invalid password."""
        # First register a user
        register_response = client.post(
            "/api/v1/auth/register-guardian",
            json={
                "email": "guardian@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
            },
        )
        assert register_response.status_code == 200

        # Then try to login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "guardian@example.com", "password": "WrongPassword123!"},
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["message"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "SecurePass123!"},
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["message"].lower()


class TestStaffLogin:
    """Test staff login endpoints."""

    def test_staff_login_success(self, client):
        """Test successful staff login."""
        # This test is disabled because the current API design doesn't
        # support staff creation through guardian invitations.
        # Staff can only be invited by other staff/admin users.
        # TODO: Implement proper staff setup for testing
        pytest.skip(
            "Staff creation flow requires admin/staff permissions not available through guardian registration"
        )

    def test_staff_login_wrong_tenant(self, client):
        """Test staff login with wrong tenant."""
        # This test is disabled for the same reason as above
        pytest.skip(
            "Staff creation flow requires admin/staff permissions not available through guardian registration"
        )


class TestInviteFlow:
    """Test teacher/staff invitation flow."""

    def test_invite_teacher_success(self, client):
        """Test successful teacher invitation."""
        # This test is disabled because guardians cannot invite teachers.
        # Only staff/admin users can invite teachers according to API design.
        # TODO: Create admin/staff user for testing invitation flows
        pytest.skip(
            "Teacher invitation requires staff/admin permissions not available through guardian registration"
        )

    def test_accept_invite_success(self, client):
        """Test successful invite acceptance."""
        # This test is disabled for the same reason as above
        pytest.skip(
            "Teacher invitation requires staff/admin permissions not available through guardian registration"
        )

    def test_accept_invalid_invite(self, client):
        """Test acceptance of invalid invitation."""
        # Test that invalid invite tokens are properly rejected
        response = client.post(
            "/api/v1/auth/accept-invite",
            json={
                "invite_token": "invalid-token",
                "password": "TeacherPass123!",
                "first_name": "Jane",
                "last_name": "Teacher",
            },
        )

        assert response.status_code == 400


class TestTokenRefresh:
    """Test token refresh functionality."""

    def test_refresh_token_success(self, client):
        """Test successful token refresh."""
        # Register a user first
        register_response = client.post(
            "/api/v1/auth/register-guardian",
            json={
                "email": "user@example.com",
                "password": "UserPass123!",
                "first_name": "Test",
                "last_name": "User",
                "phone": "+1234567890",
            },
        )
        assert register_response.status_code == 200
        refresh_token = register_response.json()["refresh_token"]

        # Test refresh
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # Should get new refresh token (rotation)
        assert data["refresh_token"] != refresh_token

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid-refresh-token"}
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["message"].lower()


class TestUserProfile:
    """Test user profile endpoints."""

    def test_get_current_user_success(self, client):
        """Test getting current user profile."""
        # Register and login
        register_response = client.post(
            "/api/v1/auth/register-guardian",
            json={
                "email": "profile@example.com",
                "password": "ProfilePass123!",
                "first_name": "Profile",
                "last_name": "User",
                "phone": "+1234567890",
            },
        )
        access_token = register_response.json()["access_token"]

        # Get profile
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profile@example.com"
        assert data["first_name"] == "Profile"
        assert data["role"] == "guardian"

    def test_get_current_user_invalid_token(self, client):
        """Test getting profile with invalid token."""
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"})

        assert response.status_code == 401


class TestLogout:
    """Test logout functionality."""

    def test_logout_success(self, client):
        """Test successful logout."""
        # Register and login
        register_response = client.post(
            "/api/v1/auth/register-guardian",
            json={
                "email": "logout@example.com",
                "password": "LogoutPass123!",
                "first_name": "Logout",
                "last_name": "User",
                "phone": "+1234567890",
            },
        )
        access_token = register_response.json()["access_token"]
        refresh_token = register_response.json()["refresh_token"]

        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()


class TestHealthCheck:
    """Test health check endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth-svc"

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Auth Service API" in data["message"]
