"""
Recording API Routes

POST /api/recording/start  — Start a browser recording session
POST /api/recording/stop   — Stop recording and return compiled workflow

Desktop-only — guarded by DEPLOYMENT_MODE != saas_cloud.
"""

import os
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recording", tags=["Recording"])

# Singleton service instance
_service = None
_DISABLED_DEPLOYMENT_MODES = {"saas", "cloud", "worker"}


def _get_service():
    global _service
    if _service is None:
        from services.recording import RecordingService
        _service = RecordingService()
    return _service


def _require_desktop_recording() -> None:
    """Reject browser recording in hosted runtimes."""
    deployment_mode = os.environ.get("DEPLOYMENT_MODE", "").strip().lower()
    if deployment_mode in _DISABLED_DEPLOYMENT_MODES:
        raise HTTPException(status_code=403, detail="Recording is only available in desktop mode")


class StartRequest(BaseModel):
    url: Optional[str] = ""


class StopRequest(BaseModel):
    session_id: str


@router.post("/start")
async def start_recording(req: StartRequest):
    """Start a new browser recording session."""
    _require_desktop_recording()

    service = _get_service()
    url = req.url or "about:blank"

    try:
        session = await service.start_recording(url=url)
        return {"ok": True, "session_id": session.session_id}
    except Exception as e:
        logger.error("Failed to start recording: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_recording(req: StopRequest):
    """Stop a recording session and return compiled workflow."""
    _require_desktop_recording()
    service = _get_service()

    try:
        result = await service.stop_recording(req.session_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"ok": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop recording: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
