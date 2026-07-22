"""
Auth config endpoint.
"""

from fastapi import APIRouter

from gateway.providers.hub import get_auth_provider
from gateway.config import get_gateway_config

router = APIRouter()


@router.get("/config")
async def get_auth_config():
    """
    Return auth provider configuration for the frontend.

    Return provider capabilities for the frontend.

    Provider implementations own their auth configuration. The gateway mode
    is an additional fail-closed boundary for offline and enterprise editions.
    """
    config = get_auth_provider().get_frontend_config()
    deployment_mode = get_gateway_config()

    if not deployment_mode.is_cloud:
        for provider in ("google", "github"):
            config.setdefault(provider, {})["enabled"] = False
            if provider == "google":
                config[provider]["clientId"] = None
                config[provider]["desktopClientId"] = None
            else:
                config[provider]["clientId"] = None

    if deployment_mode.is_enterprise:
        config["allowSelfSignup"] = False

    return config
