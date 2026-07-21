"""
Auth config endpoint.
"""

from fastapi import APIRouter

from gateway.providers.hub import get_auth_provider

router = APIRouter()


@router.get("/config")
async def get_auth_config():
    """
    Return auth provider configuration for the frontend.

    Cloud-only endpoint (local desktop app proxies to cloud).
    Frontend uses this to decide which OAuth buttons to show
    and to get the client IDs needed for OAuth popups.
    """
    return get_auth_provider().get_frontend_config()
