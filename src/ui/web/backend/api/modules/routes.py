"""
Modules API Routes - Dynamic module catalog for frontend

All functionality has been split into:
- api/modules/catalog.py - Core catalog: tiered, atomic, environment, shared helpers
- api/modules/composite.py - Composite module catalog, detail, execution
- api/modules/plugins.py - Plugin catalog, status, community registry
- api/modules/agent_tools.py - Agent tools listing and pattern resolution
- api/modules/validation.py - Connection validation endpoints
- api/modules/version.py - Version info and reload endpoints
"""

from fastapi import APIRouter

from api.modules.catalog import router as catalog_router
from api.modules.composite import router as composite_router
from api.modules.plugins import router as plugins_router
from api.modules.agent_tools import router as agent_tools_router
from api.modules.validation import router as validation_router
from api.modules.version import router as version_router

# Combined router
router = APIRouter(prefix="/modules", tags=["Modules"])
router.include_router(catalog_router)
router.include_router(composite_router)
router.include_router(plugins_router)
router.include_router(agent_tools_router)
router.include_router(validation_router)
router.include_router(version_router)
