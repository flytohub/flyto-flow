"""
Public Translations API

Public endpoints for translation information.
"""

import logging
from typing import Dict, Any, List

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/translations", tags=["Translations"])


@router.get("/languages")
async def list_languages() -> Dict[str, Any]:
    """List available languages."""
    return {
        "ok": True,
        "languages": [
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "zh-TW", "name": "Chinese (Traditional)", "native_name": "繁體中文"},
            {"code": "zh-CN", "name": "Chinese (Simplified)", "native_name": "简体中文"},
            {"code": "ja", "name": "Japanese", "native_name": "日本語"},
        ],
        "default": "en",
    }


@router.get("/")
async def translations_status() -> Dict[str, Any]:
    """Get translations system status."""
    return {
        "ok": True,
        "status": "active",
        "service": "translations",
        "supported_languages": ["en", "zh-TW", "zh-CN", "ja"],
    }
