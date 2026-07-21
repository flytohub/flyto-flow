"""
VSCode extension auth: browser-based OAuth-like flow.
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from gateway.providers.hub import get_auth_provider

from .deps import (
    VscodeCodeRequest,
    ExchangeCodeRequest,
    AuthResponse,
    build_user_response,
    mask_email,
)

logger = logging.getLogger(__name__)

router = APIRouter()


_AUTH_CODE_TTL = 60


def _auth_code_provider():
    """Return the provider responsible for VSCode auth-code persistence."""
    from gateway.providers.hub import get_data_provider

    return get_data_provider().vscode_auth_codes


def _create_auth_code(user_data: dict, token: str, refresh_token: str | None) -> str:
    """Create a one-time auth code through the active data provider."""
    return _auth_code_provider().create_code(
        user_data=user_data,
        token=token,
        refresh_token=refresh_token,
        ttl_seconds=_AUTH_CODE_TTL,
    )


def _consume_auth_code(code: str) -> dict | None:
    """Consume a one-time auth code through the active data provider."""
    return _auth_code_provider().consume_code(code)


@router.post("/vscode-code")
async def create_vscode_auth_code(data: VscodeCodeRequest, request: Request):
    """
    Exchange a Firebase ID token for a one-time auth code.

    Called by flyto2.com/auth/vscode after the user logs in via Firebase.
    The auth code is short-lived (60s) and can only be used once.
    """
    try:
        auth_provider = get_auth_provider()
        result = await auth_provider.verify_token(data.firebase_token)

        if not result.ok:
            raise HTTPException(status_code=401, detail=result.error or "Invalid Firebase token")

        user_dict = result.user.model_dump() if result.user else {}
        code = _create_auth_code(
            user_data=user_dict,
            token=result.token or data.firebase_token,
            refresh_token=result.refresh_token,
        )

        logger.info(f"VSCode auth code created for: {mask_email(user_dict.get('email', ''))}")
        return {"ok": True, "code": code}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VSCode auth code error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/exchange")
async def exchange_auth_code(data: ExchangeCodeRequest):
    """
    Exchange a one-time auth code for access/refresh tokens.

    Called by the VSCode extension after receiving the code via URI callback.
    The code can only be used once and expires after 60 seconds.
    """
    entry = _consume_auth_code(data.code)
    if not entry:
        raise HTTPException(status_code=401, detail="Invalid or expired auth code")

    user_dict = entry["user"]
    logger.info(f"VSCode auth code exchanged for: {mask_email(user_dict.get('email', ''))}")

    return AuthResponse(
        ok=True,
        access_token=entry["token"],
        refresh_token=entry["refresh_token"],
        user=build_user_response(user_dict),
    )
