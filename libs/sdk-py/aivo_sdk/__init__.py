"""
Aivo Python SDK

A comprehensive Python SDK for the Aivo learning platform API.
Generated on: 2025-09-01T12:21:11.854Z
"""

from __future__ import annotations

__version__ = "1.0.0"

from .services.auth import *  # noqa: F401, F403
from .services.enrollment import *  # noqa: F401, F403
from .services.learner import *  # noqa: F401, F403
from .services.orchestrator import *  # noqa: F401, F403
from .services.payments import *  # noqa: F401, F403
from .services.tenant import *  # noqa: F401, F403

# Note: admin-portal service import commented out due to hyphen in module name
# from .services.admin-portal import *


class ApiConfig:
    """Configuration class for the Aivo Python SDK."""

    def __init__(
        self,
        base_path: str | None = None,
        access_token: str | None = None,
        api_key: str | None = None,
    ) -> None:
        """Initialize API configuration.

        Args:
            base_path: Base URL for the API (defaults to https://api.aivo.com)
            access_token: OAuth access token for authentication
            api_key: API key for authentication
        """
        self.base_path = base_path or "https://api.aivo.com"
        self.access_token = access_token
        self.api_key = api_key


# Default configuration
default_config = ApiConfig()
