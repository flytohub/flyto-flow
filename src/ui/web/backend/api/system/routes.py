"""
System API Routes

Handles:
- System-level configuration and status
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter

from config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """
    Get system status including deployment mode, etc.
    """
    settings = get_settings()

    return {
        "deployment_mode": settings.deployment_mode,
        "debug": settings.debug
    }
