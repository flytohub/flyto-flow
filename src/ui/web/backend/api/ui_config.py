"""
UI Config API

Endpoints for frontend UI configuration.
"""

import logging
from typing import Dict, Any, List

from fastapi import APIRouter

from api.responses import success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ui-config", tags=["UI Config"])

_UI_CONFIG = {
    "theme": "light",
    "sidebar_collapsed": False,
    "show_tutorials": True,
}

_UI_PAGES = [
    {"id": "dashboard", "name": "Dashboard", "icon": "Home", "path": "/"},
    {"id": "workflows", "name": "Workflows", "icon": "GitBranch", "path": "/workflows"},
    {"id": "templates", "name": "Templates", "icon": "FileCode", "path": "/templates"},
    {"id": "executions", "name": "Executions", "icon": "Play", "path": "/executions"},
    {"id": "settings", "name": "Settings", "icon": "Settings", "path": "/settings"},
]


@router.get("")
async def get_ui_config() -> Dict[str, Any]:
    """Get UI configuration."""
    return success_response(config=_UI_CONFIG)


@router.get("/")
async def get_ui_config_slash() -> Dict[str, Any]:
    """Get UI configuration (with trailing slash)."""
    return success_response(config=_UI_CONFIG)


@router.get("/pages")
async def get_ui_pages() -> Dict[str, Any]:
    """Get UI page configurations."""
    return success_response(pages=_UI_PAGES)
