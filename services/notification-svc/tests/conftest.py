"""
Pytest configuration for notification service tests.
"""

import asyncio
import shutil
import tempfile
from unittest.mock import patch

import pytest
from app.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def email_storage_dir():
    """Create a temporary directory for email storage during tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(autouse=True)
def mock_settings(email_storage_dir):  # pylint: disable=redefined-outer-name
    """Mock settings for testing."""
    test_settings = Settings(
        dev_mode=True,
        dev_email_dump_path=email_storage_dir,
        app_name="TestApp",
        templates_path="templates",
        smtp_server="localhost",
        smtp_port=587,
        smtp_username="test@example.com",
        smtp_password="testpass",
        from_email="noreply@testapp.com",
        from_name="Test App",
        allowed_origins=["*"],
        max_recipients_per_request=100,
    )

    with patch("app.config.get_settings", return_value=test_settings):
        with patch("app.main.get_settings", return_value=test_settings):
            with patch("app.template_service.get_settings",
                       return_value=test_settings):
                with patch("app.email_service.get_settings",
                           return_value=test_settings):
                    yield test_settings


# Configure pytest async
pytest_plugins = ("pytest_asyncio",)
