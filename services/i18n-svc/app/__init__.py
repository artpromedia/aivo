"""
AIVO i18n Service Package.

Internationalization service with accessibility compliance.
"""

from .main import app
from .models import *
from .schemas import *
from .services import *
from .cli import *

__version__ = "1.0.0"
__all__ = [
    "app",
    "models", 
    "schemas",
    "services",
    "cli"
]
