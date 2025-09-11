"""API module initialization with router exports and helper functions."""

__all__ = [
    "consent_router",
    "parental_router",
    "export_router", 
    "deletion_router",
    "health_router",
]

# Import routers for clean access
from .consent import router as consent_router
from .parental import router as parental_router
from .export import router as export_router
from .deletion import router as deletion_router
from .health import router as health_router
