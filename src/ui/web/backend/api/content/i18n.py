# Copyright 2026 Flyto2. Licensed under Apache-2.0. See LICENSE.

"""
i18n Sync API

Receives module translations from the frontend after CDN hot-update.
This avoids the backend needing its own CDN fetch for module labels.
"""

import json
import logging
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.i18n_service import sync_translations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/i18n", tags=["i18n"])


class I18nSyncRequest(BaseModel):
    """Request body for syncing module translations from the frontend."""
    locale: str = Field(..., description="Locale code (e.g., 'zh-TW', 'ja')")
    translations: Dict[str, str] = Field(..., description="module.* translation keys")


@router.post("/sync")
async def sync_i18n(req: I18nSyncRequest):
    """
    Accept module translations pushed from the frontend.

    Frontend filters to modules.* keys only before sending.
    Called after CDN hot-update or locale change.
    """
    if not req.translations:
        return {"ok": True, "synced": 0}

    count = sync_translations(req.locale, req.translations)
    return {"ok": True, "synced": count}


@router.get("/app/{locale}")
async def get_app_translations(locale: str):
    """
    Serve flyto-app translations for OTA i18n updates.

    Looks for flyto-i18n dist/app/{locale}.json in the monorepo,
    or falls back to a pre-built copy deployed alongside the backend.
    """
    # Try monorepo path (dev) then deployed path (production)
    candidates = [
        Path(__file__).parent.parent.parent.parent.parent.parent / "flyto-i18n" / "dist" / "app" / f"{locale}.json",
        Path(__file__).parent.parent / "i18n" / "app" / f"{locale}.json",
    ]

    for path in candidates:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return JSONResponse(
                content=data,
                headers={"Cache-Control": "public, max-age=300"},
            )

    raise HTTPException(status_code=404, detail=f"Locale '{locale}' not found")
