"""
API Routes Package
"""

# This file makes the routes directory a Python package
# and allows for easy importing of all route modules.

from . import banners, incidents, subscriptions

__all__ = ["banners", "incidents", "subscriptions"]
