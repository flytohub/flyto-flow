"""
Translation API — Shared dependencies.

Authentication/authorization helpers used across all route modules.
"""

from fastapi import Depends, HTTPException, Query

from api.auth import get_current_user
from api.validators import require_admin as validate_admin


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role for endpoint access."""
    validate_admin(current_user)
    return current_user


async def require_translator(
    current_user: dict = Depends(get_current_user),
    locale: str = Query(...)
) -> dict:
    """
    Require translator role for the specific locale.
    Admins can access all locales.
    """
    if current_user.get("is_admin"):
        return current_user

    allowed_languages = current_user.get("allowed_languages") or current_user.get("allowedLanguages") or []
    if locale not in allowed_languages:
        raise HTTPException(
            status_code=403,
            detail=f"Not authorized to edit {locale} translations"
        )
    return current_user
