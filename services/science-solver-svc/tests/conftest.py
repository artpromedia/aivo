"""Test configuration."""

import pytest

from app.config import Settings


@pytest.fixture()
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        debug=True,
        host="127.0.0.1",
        port=8001,  # Different port for tests
        log_level="DEBUG",
    )
