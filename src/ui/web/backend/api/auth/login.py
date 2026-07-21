"""
Core auth endpoints: login, register, logout, /me, change-password, refresh.
"""

import logging

from fastapi import APIRouter, HTTPException, Depends, Request

from gateway.providers.hub import get_auth_provider

from .deps import (
    LoginRequest,
    RegisterRequest,
    AuthResponse,
    ChangePasswordRequest,
    RefreshTokenRequest,
    build_user_response,
    get_current_user,
    login_rate_limiter,
    mask_email,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, request: Request):
    """
    Login with email and password.

    Routes to appropriate auth provider based on deployment mode:
    - Cloud: Firebase Auth
    - Enterprise: Local JWT auth

    SECURITY: Rate limited to prevent brute force attacks.
    """
    # SECURITY: Rate limit by email and IP combination
    email_lower = data.email.lower()
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{email_lower}:{client_ip}"

    # Check rate limit
    if login_rate_limiter.is_locked(rate_key):
        remaining = login_rate_limiter.get_lockout_remaining(rate_key)
        logger.warning(f"Rate limited login attempt for {mask_email(data.email)} from {client_ip}")
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Please try again in {remaining // 60} minutes.",
            headers={"Retry-After": str(remaining)},
        )

    # Record attempt
    if not login_rate_limiter.record_attempt(rate_key):
        remaining = login_rate_limiter.get_lockout_remaining(rate_key)
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Please try again in {remaining // 60} minutes.",
            headers={"Retry-After": str(remaining)},
        )

    try:
        auth_provider = get_auth_provider()
        # SECURITY: Mask email in logs for privacy
        masked = mask_email(data.email)
        logger.info(f"Login attempt via {auth_provider.provider_name} for: {masked}")

        result = await auth_provider.authenticate({
            "email": data.email,
            "password": data.password
        })

        if not result.ok:
            logger.warning(f"Login failed for {masked}: {result.error}")
            raise HTTPException(status_code=401, detail=result.error)

        # SECURITY: Reset rate limit on successful login
        login_rate_limiter.reset(rate_key)
        logger.info(f"Login successful for: {masked}")

        # Build response
        user_dict = result.user.model_dump() if result.user else None
        must_change = False
        if user_dict and user_dict.get("metadata"):
            must_change = user_dict["metadata"].get("must_change_password", False)

        return AuthResponse(
            ok=True,
            access_token=result.token,
            refresh_token=result.refresh_token,
            user=build_user_response(user_dict),
            must_change_password=must_change
        )

    except HTTPException:
        raise
    except Exception as e:
        # SECURITY: Don't leak internal error details to client
        logger.error(f"Login error for {mask_email(data.email)}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/register", response_model=AuthResponse)
async def register(data: RegisterRequest):
    """
    Register new user (Cloud mode only).

    Enterprise mode should return 403 - users are created by admin.
    """
    from gateway.providers.hub import get_provider_hub

    hub = get_provider_hub()

    if hub.is_enterprise:
        raise HTTPException(
            status_code=403,
            detail="Self-registration is disabled. Contact your administrator."
        )

    # For Cloud mode, use Firebase to create user
    auth_provider = get_auth_provider()

    # Check if provider supports registration
    if not hasattr(auth_provider, 'register'):
        raise HTTPException(
            status_code=501,
            detail="Registration not supported by this auth provider"
        )

    result = await auth_provider.register({
        "email": data.email,
        "password": data.password,
        "username": data.username
    })

    if not result.ok:
        raise HTTPException(status_code=400, detail=result.error)

    user_dict = result.user.model_dump() if result.user else None

    return AuthResponse(
        ok=True,
        access_token=result.token,
        refresh_token=result.refresh_token,
        user=build_user_response(user_dict)
    )


@router.post("/logout")
async def logout():
    """
    Logout (client should discard token).

    For stateless JWT, this is mainly a signal to the client.
    """
    return {"ok": True, "message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user info.

    S-Grade: Returns pre-computed is_pro status via build_user_response.
    """
    return {"ok": True, "user": build_user_response(current_user)}


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change current user's password."""
    auth_provider = get_auth_provider()
    try:
        result = await auth_provider.change_password(
            user_id=current_user["id"],
            current_password=data.current_password,
            new_password=data.new_password,
        )
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Password change is not supported by this auth provider",
        )

    if not result.get("ok"):
        raise HTTPException(
            status_code=int(result.get("status_code", 400)),
            detail=result.get("error", "Password change failed"),
        )

    return result


@router.post("/refresh")
async def refresh_token(body: RefreshTokenRequest):
    """Refresh access token."""
    auth_provider = get_auth_provider()
    result = await auth_provider.refresh(body.refresh_token)

    if not result.ok:
        raise HTTPException(status_code=401, detail=result.error)

    return {
        "ok": True,
        "access_token": result.token,
        "refresh_token": result.refresh_token
    }
