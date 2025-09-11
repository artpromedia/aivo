"""
Tests for notification service template rendering and email functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.email_service import EmailService
from app.main import app
from app.template_service import TemplateService


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def template_service():
    """Template service instance."""
    return TemplateService()


@pytest.fixture
def email_service():
    """Email service instance."""
    return EmailService()


@pytest.fixture
def sample_teacher_data():
    """Sample data for teacher invite template."""
    return {
        "teacher_name": "Sarah Johnson",
        "school_name": "Lincoln Elementary School",
        "invite_url": "https://platform.edu/invite/abc123",
        "expires_at": datetime.now() + timedelta(days=7),
        "inviter_name": "Principal Smith",
        "school_description": "A welcoming community focused on student success",
        "app_name": "EduPlatform",
    }


@pytest.fixture
def sample_approval_data():
    """Sample data for approval request template."""
    return {
        "approver_name": "Dr. Williams",
        "requester_name": "Ms. Anderson",
        "student_name": "Emma Davis",
        "document_type": "IEP Modification",
        "approval_url": "https://platform.edu/approve/xyz789",
        "due_date": datetime.now() + timedelta(days=3),
        "school_name": "Riverside High School",
        "document_description": "Updated accommodations for mathematics courses",
        "priority_level": "high",
        "student_id": "RHS-2024-0156",
        "app_name": "EduPlatform",
    }


@pytest.fixture
def sample_enrollment_data():
    """Sample data for enrollment decision template."""
    return {
        "parent_name": "Jennifer Martinez",
        "student_name": "Carlos Martinez",
        "school_name": "Oak Valley Academy",
        "decision": "approved",
        "decision_date": datetime.now(),
        "enrollment_date": datetime.now() + timedelta(days=30),
        "contact_person": "Maria Rodriguez",
        "contact_email": "registrar@oakvalley.edu",
        "contact_phone": "(555) 123-4567",
        "next_steps": "Please complete enrollment forms by August 15th.",
        "portal_url": "https://portal.oakvalley.edu",
    }


class TestTemplateService:
    """Test template service functionality."""

    def test_list_templates(self, template_service):
        """Test listing available templates."""
        templates = template_service.list_templates()

        assert len(templates) >= 3
        template_ids = [t["id"] for t in templates]
        assert "teacher_invite" in template_ids
        assert "approval_request" in template_ids
        assert "enrollment_decision" in template_ids

    def test_get_template_config(self, template_service):
        """Test getting template configuration."""
        config = template_service.get_template_config("teacher_invite")

        assert config["name"] == "Teacher Invitation"
        assert "teacher_name" in config["required_data"]
        assert "school_name" in config["required_data"]

    def test_get_nonexistent_template_config(self, template_service):
        """Test getting config for non-existent template."""
        config = template_service.get_template_config("nonexistent")
        assert config is None

    def test_render_teacher_invite_template(self, template_service, sample_teacher_data):
        """Test rendering teacher invite template."""
        html_content = template_service.render_template("teacher_invite", sample_teacher_data)

        assert html_content is not None
        assert sample_teacher_data["teacher_name"] in html_content
        assert sample_teacher_data["school_name"] in html_content
        assert sample_teacher_data["invite_url"] in html_content
        assert "Accept Invitation" in html_content

    def test_render_approval_request_template(self, template_service, sample_approval_data):
        """Test rendering approval request template."""
        html_content = template_service.render_template("approval_request", sample_approval_data)

        assert html_content is not None
        assert sample_approval_data["approver_name"] in html_content
        assert sample_approval_data["student_name"] in html_content
        assert sample_approval_data["document_type"] in html_content
        assert "HIGH PRIORITY" in html_content  # Priority level indication

    def test_render_enrollment_decision_template(self, template_service, sample_enrollment_data):
        """Test rendering enrollment decision template."""
        html_content = template_service.render_template(
            "enrollment_decision", sample_enrollment_data
        )

        assert html_content is not None
        assert sample_enrollment_data["parent_name"] in html_content
        assert sample_enrollment_data["student_name"] in html_content
        assert "Enrollment Approved!" in html_content
        assert "Access Parent Portal" in html_content

    def test_render_enrollment_denied_template(self, template_service):
        """Test rendering enrollment decision template for denied case."""
        data = {
            "parent_name": "John Smith",
            "student_name": "Alex Smith",
            "school_name": "Test School",
            "decision": "denied",
            "decision_date": datetime.now(),
            "appeal_process": "Contact registrar within 30 days to appeal.",
        }

        html_content = template_service.render_template("enrollment_decision", data)

        assert html_content is not None
        assert "unable to approve enrollment" in html_content
        assert "Appeal Process" in html_content

    def test_render_template_with_missing_data(self, template_service):
        """Test rendering template with missing required data."""
        incomplete_data = {
            "teacher_name": "John Doe"
            # Missing school_name, invite_url, expires_at
        }

        # Should handle missing data gracefully or raise appropriate error
        with pytest.raises(Exception):
            template_service.render_template("teacher_invite", incomplete_data)

    def test_render_nonexistent_template(self, template_service):
        """Test rendering non-existent template."""
        with pytest.raises(Exception):
            template_service.render_template("nonexistent", {})


class TestEmailService:
    """Test email service functionality."""

    @patch("app.email_service.aiofiles.open", new_callable=AsyncMock)
    async def test_send_email_dev_mode(self, mock_file, email_service, sample_teacher_data):
        """Test sending email in development mode."""
        settings = get_settings()
        settings.development_mode = True

        mock_file.return_value.__aenter__.return_value.write = AsyncMock()

        result = await email_service.send_email(
            to_email="teacher@school.edu",
            subject="Test Subject",
            html_content="<h1>Test Content</h1>",
            template_id="teacher_invite",
            data=sample_teacher_data,
        )

        assert result["status"] == "sent"
        assert result["delivery_method"] == "file"
        assert "email_file" in result
        mock_file.assert_called_once()

    async def test_send_bulk_emails_dev_mode(self, email_service):
        """Test sending bulk emails in development mode."""
        notifications = [
            {
                "to_email": "user1@example.com",
                "template_id": "teacher_invite",
                "data": {
                    "teacher_name": "User 1",
                    "school_name": "School",
                    "invite_url": "http://test",
                    "expires_at": datetime.now(),
                },
            },
            {
                "to_email": "user2@example.com",
                "template_id": "teacher_invite",
                "data": {
                    "teacher_name": "User 2",
                    "school_name": "School",
                    "invite_url": "http://test",
                    "expires_at": datetime.now(),
                },
            },
        ]

        with patch("app.email_service.aiofiles.open", new_callable=AsyncMock) as mock_file:
            mock_file.return_value.__aenter__.return_value.write = AsyncMock()

            results = await email_service.send_bulk_emails(notifications)

            assert len(results) == 2
            assert all(r["status"] == "sent" for r in results)

    @patch("smtplib.SMTP")
    async def test_send_email_production_mode(self, mock_smtp, email_service):
        """Test sending email in production mode."""
        settings = get_settings()
        settings.development_mode = False

        mock_server = Mock()
        mock_smtp.return_value = mock_server
        mock_server.starttls.return_value = None
        mock_server.login.return_value = None
        mock_server.send_message.return_value = {}

        result = await email_service.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<h1>Test Content</h1>",
        )

        assert result["status"] == "sent"
        assert result["delivery_method"] == "smtp"
        mock_server.send_message.assert_called_once()


class TestNotificationAPI:
    """Test notification API endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_list_templates_endpoint(self, client):
        """Test list templates endpoint."""
        response = client.get("/templates")
        assert response.status_code == 200

        templates = response.json()["templates"]
        assert len(templates) >= 3
        template_ids = [t["id"] for t in templates]
        assert "teacher_invite" in template_ids

    def test_get_template_config_endpoint(self, client):
        """Test get template config endpoint."""
        response = client.get("/templates/teacher_invite")
        assert response.status_code == 200

        config = response.json()
        assert config["name"] == "Teacher Invitation"
        assert "required_data" in config

    def test_render_template_endpoint(self, client, sample_teacher_data):
        """Test render template endpoint."""
        response = client.post(
            "/render",
            json={
                "template_id": "teacher_invite",
                "data": {
                    **sample_teacher_data,
                    "expires_at": sample_teacher_data["expires_at"].isoformat(),
                },
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert "html" in result
        assert sample_teacher_data["teacher_name"] in result["html"]

    @patch("app.email_service.aiofiles.open", new_callable=AsyncMock)
    def test_send_notification_endpoint(self, mock_file, client, sample_teacher_data):
        """Test send notification endpoint."""
        mock_file.return_value.__aenter__.return_value.write = AsyncMock()

        response = client.post(
            "/notify",
            json={
                "to_email": "teacher@school.edu",
                "template_id": "teacher_invite",
                "data": {
                    **sample_teacher_data,
                    "expires_at": sample_teacher_data["expires_at"].isoformat(),
                },
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "sent"

    @patch("app.email_service.aiofiles.open", new_callable=AsyncMock)
    def test_send_bulk_notifications_endpoint(self, mock_file, client):
        """Test send bulk notifications endpoint."""
        mock_file.return_value.__aenter__.return_value.write = AsyncMock()

        notifications = [
            {
                "to_email": "user1@example.com",
                "template_id": "teacher_invite",
                "data": {
                    "teacher_name": "User 1",
                    "school_name": "School",
                    "invite_url": "http://test",
                    "expires_at": datetime.now().isoformat(),
                },
            }
        ]

        response = client.post("/notify/bulk", json={"notifications": notifications})

        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["status"] == "sent"

    def test_send_notification_invalid_template(self, client):
        """Test send notification with invalid template."""
        response = client.post(
            "/notify",
            json={"to_email": "test@example.com", "template_id": "nonexistent", "data": {}},
        )

        assert response.status_code == 400

    def test_send_notification_invalid_email(self, client):
        """Test send notification with invalid email."""
        response = client.post(
            "/notify",
            json={"to_email": "invalid-email", "template_id": "teacher_invite", "data": {}},
        )

        assert response.status_code == 422  # Validation error


class TestTemplateValidation:
    """Test template data validation."""

    def test_teacher_invite_required_fields(self, template_service):
        """Test teacher invite template requires all fields."""
        incomplete_data = {
            "teacher_name": "John Doe",
            "school_name": "Test School",
            # Missing invite_url and expires_at
        }

        with pytest.raises(Exception):
            template_service.render_template("teacher_invite", incomplete_data)

    def test_approval_request_priority_levels(self, template_service):
        """Test approval request template with different priority levels."""
        base_data = {
            "approver_name": "Dr. Smith",
            "requester_name": "Ms. Johnson",
            "student_name": "Test Student",
            "document_type": "IEP",
            "approval_url": "http://test.com",
            "due_date": datetime.now(),
        }

        # Test normal priority
        normal_data = {**base_data, "priority_level": "normal"}
        html = template_service.render_template("approval_request", normal_data)
        assert "URGENT" not in html

        # Test high priority
        high_data = {**base_data, "priority_level": "high"}
        html = template_service.render_template("approval_request", high_data)
        assert "HIGH PRIORITY" in html

        # Test urgent priority
        urgent_data = {**base_data, "priority_level": "urgent"}
        html = template_service.render_template("approval_request", urgent_data)
        assert "URGENT" in html

    def test_enrollment_decision_types(self, template_service):
        """Test enrollment decision template with different decisions."""
        base_data = {
            "parent_name": "Parent Name",
            "student_name": "Student Name",
            "school_name": "Test School",
            "decision_date": datetime.now(),
        }

        # Test approved
        approved_data = {**base_data, "decision": "approved"}
        html = template_service.render_template("enrollment_decision", approved_data)
        assert "Enrollment Approved!" in html

        # Test denied
        denied_data = {**base_data, "decision": "denied"}
        html = template_service.render_template("enrollment_decision", denied_data)
        assert "unable to approve" in html

        # Test waitlisted
        waitlisted_data = {**base_data, "decision": "waitlisted"}
        html = template_service.render_template("enrollment_decision", waitlisted_data)
        assert "Waitlisted" in html


class TestEmailFileStorage:
    """Test email file storage in development mode."""

    @patch("app.email_service.aiofiles.open", new_callable=AsyncMock)
    async def test_email_file_structure(self, mock_file, email_service):
        """Test email file structure in development mode."""
        mock_file.return_value.__aenter__.return_value.write = AsyncMock()

        result = await email_service.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<h1>Test</h1>",
            template_id="teacher_invite",
            data={"test": "data"},
        )

        assert result["status"] == "sent"
        assert result["delivery_method"] == "file"
        assert "email_file" in result

        # Verify file was opened for writing
        mock_file.assert_called_once()
        args, kwargs = mock_file.call_args
        assert args[0].endswith(".json")  # Email file should be JSON
        assert "w" in args[1]  # Write mode


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async operations in the notification service."""

    async def test_concurrent_notifications(self, email_service):
        """Test sending multiple notifications concurrently."""
        notifications = [
            {
                "to_email": f"user{i}@example.com",
                "template_id": "teacher_invite",
                "data": {
                    "teacher_name": f"User {i}",
                    "school_name": "Test School",
                    "invite_url": "http://test.com",
                    "expires_at": datetime.now(),
                },
            }
            for i in range(5)
        ]

        with patch("app.email_service.aiofiles.open", new_callable=AsyncMock) as mock_file:
            mock_file.return_value.__aenter__.return_value.write = AsyncMock()

            results = await email_service.send_bulk_emails(notifications)

            assert len(results) == 5
            assert all(r["status"] == "sent" for r in results)

    async def test_template_rendering_performance(self, template_service):
        """Test template rendering performance with large data sets."""
        large_features_list = [f"Feature {i}" for i in range(100)]

        data = {
            "teacher_name": "Test Teacher",
            "school_name": "Test School",
            "invite_url": "http://test.com",
            "expires_at": datetime.now(),
            "platform_features": large_features_list,
        }

        html = template_service.render_template("teacher_invite", data)
        assert html is not None
        assert len(html) > 1000  # Should be substantial content
