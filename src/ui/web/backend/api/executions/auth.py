"""
Execution API Authentication Helpers

Provides optional and required authentication for execution endpoints.
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Get current user if token provided, otherwise return None.

    Allows unauthenticated access for local execution mode.
    Use this for endpoints that work with or without authentication.

    Args:
        authorization: Bearer token from header

    Returns:
        User dict if authenticated, None otherwise
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split("Bearer ")[1]

    try:
        from gateway.providers.hub import get_auth_provider
        auth_provider = get_auth_provider()
        result = await auth_provider.verify_token(token)
        if result.ok and result.user:
            return result.user.model_dump()
    except Exception as e:
        # SECURITY: Log exception type for debugging (not details)
        logger.warning(f"Execution auth: token verification failed: {type(e).__name__}")

    return None


async def get_required_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Require authenticated user.

    Use this for endpoints that require authentication.

    Args:
        authorization: Bearer token from header

    Returns:
        User dict

    Raises:
        HTTPException: 401 if not authenticated
    """
    user = await get_optional_user(authorization)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return user

