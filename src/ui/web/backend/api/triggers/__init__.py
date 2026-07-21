"""CE trigger routes exclude hosted scheduler and job-plane handlers."""

from .local_routes import local_router

router = local_router

__all__ = ["local_router", "router"]
