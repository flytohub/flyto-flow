"""
Social login endpoints: Google, GitHub, link/unlink providers.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Request

from gateway.providers.hub import get_auth_provider

from .deps import (
    GoogleLoginRequest,
    GoogleLoginCodeRequest,
    GitHubLoginRequest,
    LinkGoogleRequest,
    UnlinkProviderRequest,
    AuthResponse,
    build_user_response,
    login_rate_limiter,
    mask_email,
    validate_token_format,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _request_uri(request: Request) -> str:
    return (
        request.headers.get("origin")
        or request.headers.get("referer", "").rstrip("/")
        or "http://localhost"
    )


def _check_rate_limit(rate_key: str):
    """Check rate limiter and raise 429 if locked or attempt fails."""
    if login_rate_limiter.is_locked(rate_key):
        remaining = login_rate_limiter.get_lockout_remaining(rate_key)
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Please try again in {remaining // 60} minutes.",
            headers={"Retry-After": str(remaining)},
        )
    if not login_rate_limiter.record_attempt(rate_key):
        remaining = login_rate_limiter.get_lockout_remaining(rate_key)
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Please try again in {remaining // 60} minutes.",
            headers={"Retry-After": str(remaining)},
        )


async def _ensure_user_doc(
    auth_provider,
    *,
    user_id: str,
    email: str,
    display_name: str,
    photo_url: str,
    is_new_user: bool,
    username_hint: str,
    masked: str,
    provider_label: str,
):
    """Create provider user doc if new user, or auto-create if missing."""
    if is_new_user:
        logger.info(f"New {provider_label} user registered: {masked}")
        if hasattr(auth_provider, '_create_user_document'):
            await auth_provider._create_user_document(
                user_id=user_id,
                email=email,
                username=username_hint,
                display_name=display_name or username_hint,
                avatar_url=photo_url,
            )
    else:
        logger.info(f"{provider_label} login successful for: {masked}")

    user_data = await auth_provider._get_user_data(user_id) if hasattr(auth_provider, '_get_user_data') else None

    # Auto-create user doc if Auth user exists but profile data is missing
    if not user_data and not is_new_user and hasattr(auth_provider, '_create_user_document'):
        logger.info(f"Auto-creating missing Firestore doc for {provider_label} user: {masked}")
        await auth_provider._create_user_document(
            user_id=user_id,
            email=email,
            username=username_hint,
            display_name=display_name or username_hint,
            avatar_url=photo_url,
        )
        user_data = await auth_provider._get_user_data(user_id)

    return user_data


async def _backfill_user_avatar(
    auth_provider,
    *,
    user_id: str,
    photo_url: str,
    user_data: Optional[dict],
) -> None:
    """Persist provider profile avatar when the profile has no avatar set."""
    if not user_data or user_data.get("avatar_url") or not photo_url:
        return
    backfill = getattr(auth_provider, "backfill_user_avatar", None)
    if backfill is None:
        return
    try:
        await backfill(user_id=user_id, avatar_url=photo_url)
    except NotImplementedError:
        pass
    except Exception:
        logger.warning("Failed to backfill social profile avatar", exc_info=True)


def _build_user_dict(
    user_id: str,
    email: str,
    display_name: str,
    photo_url: str,
    username_hint: str,
    user_data: Optional[dict],
) -> dict:
    """Build user response dict from provider profile data."""
    is_admin = False
    subscription_plan = None
    subscription_status = None
    allowed_languages = None
    avatar_url = None
    username = username_hint

    if user_data:
        is_admin = user_data.get("is_admin", False) or user_data.get("role") == "admin"
        subscription_plan = user_data.get("subscription_plan")
        subscription_status = user_data.get("subscription_status")
        allowed_languages = user_data.get("allowed_languages")
        avatar_url = user_data.get("avatar_url") or None
        username = user_data.get("username") or username
        display_name = user_data.get("display_name") or display_name

        if not avatar_url and photo_url:
            avatar_url = photo_url

    return {
        "id": user_id,
        "email": email,
        "username": username,
        "display_name": display_name,
        "avatar_url": avatar_url,
        "is_admin": is_admin,
        "roles": ["admin"] if is_admin else ["user"],
        "subscription_plan": subscription_plan,
        "subscription_status": subscription_status,
        "allowed_languages": allowed_languages,
    }


@router.post("/google-login", response_model=AuthResponse)
async def google_login(data: GoogleLoginRequest, request: Request):
    """
    Login or register with Google credential (from Google Identity Services).

    Authenticates the Google JWT through the configured auth provider.
    Creates provider user doc if new user.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"google:{client_ip}"
    _check_rate_limit(rate_key)

    try:
        auth_provider = get_auth_provider()
        request_uri = _request_uri(request)

        try:
            result = await auth_provider.sign_in_with_google_credential(
                data.credential,
                request_uri=request_uri,
            )
        except ValueError as ve:
            logger.warning(f"Google sign-in failed for {client_ip}: {ve}")
            raise HTTPException(status_code=401, detail="Google login failed. Please try again.")
        except NotImplementedError:
            raise HTTPException(
                status_code=501,
                detail="Google login is not supported in this deployment.",
            )

        user_id = result.get("localId")
        email = result.get("email", "")
        display_name = result.get("displayName", "")
        photo_url = result.get("photoUrl", "")
        is_new_user = result.get("isNewUser", False)
        username_hint = email.split("@")[0] if email else ""

        masked = mask_email(email)
        login_rate_limiter.reset(rate_key)

        user_data = await _ensure_user_doc(
            auth_provider, user_id=user_id, email=email, display_name=display_name,
            photo_url=photo_url, is_new_user=is_new_user, username_hint=username_hint,
            masked=masked, provider_label="Google",
        )
        await _backfill_user_avatar(
            auth_provider,
            user_id=user_id,
            photo_url=photo_url,
            user_data=user_data,
        )
        user_dict = _build_user_dict(user_id, email, display_name, photo_url, username_hint, user_data)

        id_token = result.get("idToken")
        # Debug: verify we're returning a JWT, not something else
        if id_token and not id_token.startswith("eyJ"):
            logger.error(f"[AUTH BUG] Google login returned non-JWT idToken: {id_token[:20]}...")

        return AuthResponse(
            ok=True,
            access_token=id_token,
            refresh_token=result.get("refreshToken"),
            user=build_user_response(user_dict),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/google-login-code", response_model=AuthResponse)
async def google_login_code(data: GoogleLoginCodeRequest, request: Request):
    """
    Login or register with Google authorization code (desktop OAuth flow).

    Exchanges the auth code and signs in through the configured auth provider.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"google:{client_ip}"
    _check_rate_limit(rate_key)

    try:
        auth_provider = get_auth_provider()
        try:
            result = await auth_provider.sign_in_with_google_code(
                code=data.code,
                redirect_uri=data.redirect_uri,
                code_verifier=data.code_verifier,
                use_desktop_client=True,
            )
        except ValueError as ve:
            logger.warning(f"Google code exchange failed for {client_ip}: {ve}")
            raise HTTPException(status_code=401, detail="Google login failed. Please try again.")
        except NotImplementedError:
            raise HTTPException(
                status_code=501,
                detail="Google login is not supported in this deployment.",
            )

        user_id = result.get("localId")
        email = result.get("email", "")
        display_name = result.get("displayName", "")
        photo_url = result.get("photoUrl", "")
        is_new_user = result.get("isNewUser", False)
        username_hint = email.split("@")[0] if email else ""

        masked = mask_email(email)
        login_rate_limiter.reset(rate_key)

        user_data = await _ensure_user_doc(
            auth_provider, user_id=user_id, email=email, display_name=display_name,
            photo_url=photo_url, is_new_user=is_new_user, username_hint=username_hint,
            masked=masked, provider_label="Google (desktop)",
        )
        await _backfill_user_avatar(
            auth_provider,
            user_id=user_id,
            photo_url=photo_url,
            user_data=user_data,
        )
        user_dict = _build_user_dict(user_id, email, display_name, photo_url, username_hint, user_data)

        return AuthResponse(
            ok=True,
            access_token=result.get("idToken"),
            refresh_token=result.get("refreshToken"),
            user=build_user_response(user_dict),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google login code error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/github-login", response_model=AuthResponse)
async def github_login(data: GitHubLoginRequest, request: Request):
    """
    Login or register with GitHub OAuth authorization code.

    Exchanges the GitHub code and signs in through the configured auth provider.
    Creates provider user doc if new user.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"github:{client_ip}"
    _check_rate_limit(rate_key)

    try:
        auth_provider = get_auth_provider()
        request_uri = _request_uri(request)
        redirect_uri = data.redirect_uri or f"{request_uri}/github-callback"

        try:
            result = await auth_provider.sign_in_with_github_code(
                code=data.code,
                redirect_uri=redirect_uri,
                request_uri=request_uri,
            )
        except ValueError as ve:
            logger.warning(f"GitHub sign-in failed for {client_ip}: {ve}")
            raise HTTPException(status_code=401, detail="GitHub login failed. Please try again.")
        except NotImplementedError:
            raise HTTPException(
                status_code=501,
                detail="GitHub login is not supported in this deployment.",
            )

        user_id = result.get("localId")
        email = result.get("email", "")
        display_name = result.get("displayName", "")
        screen_name = result.get("screenName", "")
        photo_url = result.get("photoUrl", "")
        is_new_user = result.get("isNewUser", False)
        username_hint = screen_name or (email.split("@")[0] if email else "")

        masked = mask_email(email)
        login_rate_limiter.reset(rate_key)

        user_data = await _ensure_user_doc(
            auth_provider, user_id=user_id, email=email,
            display_name=display_name or screen_name or username_hint,
            photo_url=photo_url, is_new_user=is_new_user, username_hint=username_hint,
            masked=masked, provider_label="GitHub",
        )
        await _backfill_user_avatar(
            auth_provider,
            user_id=user_id,
            photo_url=photo_url,
            user_data=user_data,
        )
        user_dict = _build_user_dict(user_id, email, display_name, photo_url, username_hint, user_data)

        return AuthResponse(
            ok=True,
            access_token=result.get("idToken"),
            refresh_token=result.get("refreshToken"),
            user=build_user_response(user_dict),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/linked-providers")
async def get_linked_providers(authorization: Optional[str] = Header(None)):
    """Get linked auth providers for the current user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split("Bearer ")[1]
    if not validate_token_format(token):
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        providers = await get_auth_provider().get_account_providers(token)
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Linked provider lookup is not supported in this deployment.",
        )
    if providers is None:
        raise HTTPException(status_code=500, detail="Failed to fetch providers")

    return {"ok": True, "providers": providers}


@router.post("/link-google")
async def link_google(
    data: LinkGoogleRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Link a Google account to the current user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split("Bearer ")[1]
    if not validate_token_format(token):
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        providers = await get_auth_provider().link_google_account(
            id_token=token,
            credential=data.credential,
            request_uri=_request_uri(request),
        )
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Google account linking is not supported in this deployment.",
        )
    if providers is None:
        raise HTTPException(status_code=400, detail="Failed to link Google account")

    return {"ok": True, "providers": providers}


@router.post("/unlink-provider")
async def unlink_provider(
    data: UnlinkProviderRequest,
    authorization: Optional[str] = Header(None),
):
    """Unlink a provider from the current user. At least one login method must remain."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split("Bearer ")[1]
    if not validate_token_format(token):
        raise HTTPException(status_code=401, detail="Invalid token format")

    # Check current providers first
    auth_provider = get_auth_provider()
    try:
        current_providers = await auth_provider.get_account_providers(token)
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Account provider unlinking is not supported in this deployment.",
        )
    if current_providers is None:
        raise HTTPException(status_code=500, detail="Failed to fetch providers")

    if data.provider_id not in current_providers:
        raise HTTPException(status_code=400, detail="Provider not linked")

    # Must keep at least one login method
    if len(current_providers) <= 1:
        raise HTTPException(status_code=400, detail="Cannot unlink — you need at least one login method")

    remaining = await auth_provider.unlink_account_provider(
        id_token=token,
        provider_id=data.provider_id,
    )
    if remaining is None:
        raise HTTPException(status_code=500, detail="Failed to unlink provider")

    return {"ok": True, "providers": remaining}
