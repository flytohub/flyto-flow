"""
Translation Management API Package.

Re-exports ``router`` for backward compatibility with::

    from api.translations import router
"""

from fastapi import APIRouter

from api.content.translations.routes_read import router as read_router
from api.content.translations.routes_write import router as write_router
from api.content.translations.routes_pr import router as pr_router
from api.content.translations.routes_ai import router as ai_router

router = APIRouter(prefix="/admin/translations", tags=["Translations"])
router.include_router(read_router)
router.include_router(write_router)
router.include_router(pr_router)
router.include_router(ai_router)
