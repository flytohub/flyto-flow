"""
Engine API - Variable Introspection and Autocomplete

Provides endpoints for workflow editor to:
- Introspect available variables at any node position
- Get autocomplete suggestions for expressions
- Validate expression syntax
"""

from fastapi import APIRouter
from api.engine.routes import router as engine_routes_router

router = APIRouter(tags=["Engine"])
router.include_router(engine_routes_router)

__all__ = ['router']
