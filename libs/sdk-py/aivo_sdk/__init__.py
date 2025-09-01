"""
Aivo Python SDK

A comprehensive Python SDK for the Aivo learning platform API.
Generated on: 2025-09-01T12:21:11.854Z
"""

__version__ = "1.0.0"

from .services.auth import *
from .services.tenant import *
from .services.enrollment import *
from .services.payments import *
from .services.learner import *
from .services.orchestrator import *
from .services.admin-portal import *

# Configuration class
class ApiConfig:
    def __init__(self, base_path: str = None, access_token: str = None, api_key: str = None):
        self.base_path = base_path or "https://api.aivo.com"
        self.access_token = access_token
        self.api_key = api_key

# Default configuration
default_config = ApiConfig()
