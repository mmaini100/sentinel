"""
API routers package.

Mounts all route groups under /api/v1.
"""

from app.api.services import router as services_router
from app.api.incidents import router as incidents_router

__all__ = ["services_router", "incidents_router"]
