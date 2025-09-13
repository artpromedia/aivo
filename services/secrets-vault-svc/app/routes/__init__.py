"""Routes package initialization."""

from .namespaces import router as namespaces_router
from .secrets import router as secrets_router

__all__ = [
    "namespaces_router",
    "secrets_router",
]
