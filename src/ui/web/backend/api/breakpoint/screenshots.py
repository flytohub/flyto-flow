"""
Screenshot Serving Routes

Serves uploaded breakpoint screenshots from ~/.flyto/screenshots/
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/screenshots", tags=["screenshots"])

SCREENSHOTS_DIR = Path.home() / ".flyto" / "screenshots"


@router.get("/{filename}")
async def serve_screenshot(filename: str):
    """Serve a breakpoint screenshot file."""
    # Sanitize filename
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(400, "Invalid filename")

    filepath = SCREENSHOTS_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, "Screenshot not found")

    # Determine content type
    suffix = filepath.suffix.lower()
    content_type = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"

    return FileResponse(str(filepath), media_type=content_type)
