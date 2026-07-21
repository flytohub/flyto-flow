"""FastAPI authentication dependencies for Cloud CE local JWT auth."""

from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, status

from gateway.providers.base import AuthResult, UserInfo
from gateway.providers.hub import get_auth_provider


TRIAL_EXEMPT_ROLE = "trial_exempt"


async def get_current_user(authorization: Optional[str] = Header(None)) -> UserInfo:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result: AuthResult = await get_auth_provider().verify_token(authorization[7:])
    if not result.ok or result.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error or "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result.user


async def get_current_active_user(authorization: Optional[str] = Header(None)) -> UserInfo:
    user = await get_current_user(authorization)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")
    return user


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[UserInfo]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    result: AuthResult = await get_auth_provider().verify_token(authorization[7:])
    return result.user if result.ok else None


async def get_admin_user(authorization: Optional[str] = Header(None)) -> UserInfo:
    user = await get_current_active_user(authorization)
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user


def get_user_dict(user: UserInfo) -> Dict[str, Any]:
    return {
        "id": user.id,
        "uid": user.id,
        "email": user.email,
        "username": user.username,
        "display_name": user.display_name,
        "roles": user.roles,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "subscription_plan": user.subscription_plan,
        "subscription_status": user.subscription_status,
    }


async def require_active_trial(
    user: UserInfo = Depends(get_current_active_user),
) -> UserInfo:
    return user


async def require_active_trial_or_subscription(
    user: UserInfo = Depends(get_current_active_user),
) -> UserInfo:
    return user


get_current_user_dict = get_current_active_user


__all__ = [
    "TRIAL_EXEMPT_ROLE",
    "get_admin_user",
    "get_current_active_user",
    "get_current_user",
    "get_current_user_dict",
    "get_optional_user",
    "get_user_dict",
    "require_active_trial",
    "require_active_trial_or_subscription",
]
