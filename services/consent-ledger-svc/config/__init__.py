"""Config module initialization with helper functions for clean imports."""

__all__ = [
    "settings",
    "database",
    "celery",
    "get_settings",
    "get_database_config",
    "get_celery_config",
    "get_external_services_config",
    "get_compliance_config",
]

from .database import DatabaseManager, get_db
from .settings import (
    get_celery_config,
    get_compliance_config,
    get_database_config,
    get_external_services_config,
    get_settings,
)

# Convenience imports
settings = get_settings()
database = get_database_config()
celery = get_celery_config()
