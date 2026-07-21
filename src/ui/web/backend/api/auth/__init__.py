"""
Auth API package.

Re-exports key dependencies from deps.py.
Router is assembled lazily via create_auth_router() so that importing
get_current_user does NOT trigger loading cloud-only sub-routers
(e.g. desktop_oauth → firebase).
"""

from .deps import (
    get_current_user,
    get_optional_user,
    compute_is_pro,
    build_user_response,
    validate_token_format,
    mask_email,
)


def create_auth_router():
    """Assemble all auth sub-routers. Called only by _register_cloud_routes()."""
    from fastapi import APIRouter

    router = APIRouter(prefix="/auth", tags=["Auth"])

    from .config import router as config_router
    from .csrf import router as csrf_router
    from .login import router as login_router
    from .social import router as social_router
    from .password_reset import router as password_reset_router
    from .vscode import router as vscode_router
    from .desktop_oauth import router as desktop_oauth_router

    router.include_router(config_router)
    router.include_router(csrf_router)
    router.include_router(login_router)
    router.include_router(social_router)
    router.include_router(password_reset_router)
    router.include_router(vscode_router)
    router.include_router(desktop_oauth_router)

    return router


__all__ = [
    "create_auth_router",
    "get_current_user",
    "get_optional_user",
    "compute_is_pro",
    "build_user_response",
    "validate_token_format",
    "mask_email",
]
