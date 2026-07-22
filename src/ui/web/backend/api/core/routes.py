"""Compatibility router for local core APIs."""

from fastapi import APIRouter

from api.core.health import router as health_router
from api.core.plugins import router as plugins_router
from api.core.updater import router as updater_router


router = APIRouter(prefix="/core", tags=["Core"])
router.include_router(health_router)
router.include_router(plugins_router)
router.include_router(updater_router)
