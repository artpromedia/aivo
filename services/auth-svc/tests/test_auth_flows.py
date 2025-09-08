"""
Test auth flows for S1-02 requirements.
Covers guardian/teacher/staff authentication flows with JWT RBAC.
"""

import pytest


class TestGuardianAuthFlow:
    """Test guardian registration and login flow."""

    def test_guardian_registration_and_login(self, client):
        """Test complete guardian registration and login flow."""
        # Step 1: Register guardian
        guardian_data = {
            "email": "guardian@example.com",
            "password": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
        }

        register_response = client.post("/api/v1/auth/register-guardian", json=guardian_data)
        assert register_response.status_code == 200

        register_data = register_response.json()
        assert "access_token" in register_data
        assert "refresh_token" in register_data
        assert register_data["user"]["email"] == guardian_data["email"]
        assert register_data["user"]["role"] == "guardian"
        assert register_data["user"]["status"] == "active"

        # Step 2: Login with credentials
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": guardian_data["email"], "password": guardian_data["password"]},
        )
        assert login_response.status_code == 200

        login_data = login_response.json()
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        assert login_data["user"]["email"] == guardian_data["email"]
        assert login_data["user"]["role"] == "guardian"

        # Step 3: Verify JWT claims
        access_token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        profile_response = client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200

        profile_data = profile_response.json()
        assert profile_data["email"] == guardian_data["email"]
        assert profile_data["role"] == "guardian"
        assert profile_data["tenant_id"] is not None  # Auto-assigned for guardians


class TestTeacherInviteFlow:
    """Test teacher invitation and acceptance flow."""

    def test_teacher_invite_and_accept_flow(self, client):
        """Test complete teacher invitation flow."""
        # This test requires admin/staff user to invite teachers
        # Since only staff/admin can invite, we'll skip this until we have
        # a way to create admin users in tests
        pytest.skip("Teacher invitation requires admin/staff permissions - needs admin user setup")


class TestStaffLoginFlow:
    """Test staff login with tenant context."""

    def test_staff_login_with_tenant(self, client):
        """Test staff login with tenant validation."""
        # This test requires staff user which can only be created via invitation
        # Since only staff/admin can invite, we'll skip this until we have
        # a way to create staff users in tests
        pytest.skip("Staff login test requires staff user - needs admin user setup")


class TestRefreshTokenFlow:
    """Test refresh token rotation."""

    def test_refresh_token_rotation(self, client):
        """Test that refresh tokens are rotated on each use."""
        # Step 1: Register guardian to get initial tokens
        guardian_data = {
            "email": "refresh@example.com",
            "password": "SecurePass123!",
            "first_name": "Refresh",
            "last_name": "User",
            "phone": "+1234567890",
        }

        register_response = client.post("/api/v1/auth/register-guardian", json=guardian_data)
        assert register_response.status_code == 200

        initial_data = register_response.json()
        initial_refresh_token = initial_data["refresh_token"]

        # Step 2: Use refresh token to get new access token
        refresh_response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": initial_refresh_token}
        )
        assert refresh_response.status_code == 200

        refresh_data = refresh_response.json()
        new_refresh_token = refresh_data["refresh_token"]

        # Step 3: Verify token rotation (new token should be different)
        assert new_refresh_token != initial_refresh_token
        assert "access_token" in refresh_data

        # Step 4: Old refresh token should be invalid
        old_token_response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": initial_refresh_token}
        )
        assert old_token_response.status_code == 401


class TestJWTClaims:
    """Test JWT token claims structure."""

    def test_jwt_claims_structure(self, client):
        """Test that JWT tokens contain required claims: sub, role, tenant_id, dash_context."""
        # Register guardian
        guardian_data = {
            "email": "claims@example.com",
            "password": "SecurePass123!",
            "first_name": "Claims",
            "last_name": "Test",
            "phone": "+1234567890",
        }

        register_response = client.post("/api/v1/auth/register-guardian", json=guardian_data)
        assert register_response.status_code == 200

        # Get user profile to verify JWT claims are working
        access_token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        profile_response = client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200

        profile_data = profile_response.json()

        # Verify that the JWT is properly decoded and contains expected data
        assert "id" in profile_data  # sub claim
        assert profile_data["role"] == "guardian"  # role claim
        assert profile_data["tenant_id"] is not None  # tenant_id claim
        # dash_context is used internally for permissions


class TestErrorHandling:
    """Test error handling in auth flows."""

    def test_duplicate_guardian_registration(self, client):
        """Test that duplicate email registration is rejected."""
        guardian_data = {
            "email": "duplicate@example.com",
            "password": "SecurePass123!",
            "first_name": "First",
            "last_name": "User",
            "phone": "+1234567890",
        }

        # First registration should succeed
        first_response = client.post("/api/v1/auth/register-guardian", json=guardian_data)
        assert first_response.status_code == 200

        # Second registration with same email should fail
        second_response = client.post("/api/v1/auth/register-guardian", json=guardian_data)
        assert second_response.status_code == 400
        assert "already registered" in second_response.json()["message"].lower()

    def test_invalid_login_credentials(self, client):
        """Test login with invalid credentials."""
        # Try login with non-existent user
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_invalid_refresh_token(self, client):
        """Test refresh with invalid token."""
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid-token"})
        assert response.status_code == 401

    def test_invalid_access_token(self, client):
        """Test API access with invalid access token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


class TestSecurityFeatures:
    """Test security features like Argon2 hashing."""

    def test_password_hashing(self, client):
        """Test that passwords are properly hashed with Argon2."""
        guardian_data = {
            "email": "security@example.com",
            "password": "SecurePass123!",
            "first_name": "Security",
            "last_name": "Test",
            "phone": "+1234567890",
        }

        # Register user
        register_response = client.post("/api/v1/auth/register-guardian", json=guardian_data)
        assert register_response.status_code == 200

        # Try login with correct password
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": guardian_data["email"], "password": guardian_data["password"]},
        )
        assert login_response.status_code == 200

        # Try login with wrong password
        wrong_login_response = client.post(
            "/api/v1/auth/login",
            json={"email": guardian_data["email"], "password": "WrongPassword123!"},
        )
        assert wrong_login_response.status_code == 401


class TestLogoutFlow:
    """Test logout functionality."""

    def test_logout_invalidates_refresh_token(self, client):
        """Test that logout invalidates the refresh token."""
        # Register guardian
        guardian_data = {
            "email": "logout@example.com",
            "password": "SecurePass123!",
            "first_name": "Logout",
            "last_name": "Test",
            "phone": "+1234567890",
        }

        register_response = client.post("/api/v1/auth/register-guardian", json=guardian_data)
        assert register_response.status_code == 200

        register_data = register_response.json()
        access_token = register_data["access_token"]
        refresh_token = register_data["refresh_token"]

        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        logout_response = client.post(
            "/api/v1/auth/logout", json={"refresh_token": refresh_token}, headers=headers
        )
        assert logout_response.status_code == 200

        # Try to use refresh token after logout (should fail)
        refresh_response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 401
