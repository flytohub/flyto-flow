"""
Config API — General

Basic app config, platform config, shared constants, and category definitions.
"""

import logging

from fastapi import APIRouter, Query

from config.constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_VISIBILITY_CATEGORIES,
    CATEGORY_DEFAULTS,
    DEFAULT_CATEGORY_META,
)
from api.currency import (
    format_fee_percent_display,
    calculate_fee_preview,
    calculate_net_credits,
)
from gateway.providers.hub import get_data_provider

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_config():
    """Get basic configuration"""
    # Read platform fee from admin settings (graceful: works without Firebase)
    try:
        provider = get_data_provider()
        config_result = await provider.admin.get_config()
        config_data = config_result.get("config", {})
        platform_fee = config_data.get("platform_fee_percent", 0.15)
    except Exception as e:
        logger.warning(f"Failed to load admin config, using default fee: {e}")
        platform_fee = 0.15

    return {
        "ok": True,
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
        },
        "platform_fee_percent": platform_fee,
        "platform_fee_display": format_fee_percent_display(platform_fee),
        "min_price": 0,
        "max_price": 1000,  # $1000 in dollars
    }


@router.get("/platform")
async def get_platform_config():
    """Get platform configuration for marketplace"""
    # Read platform fee from admin settings (graceful: works without Firebase)
    try:
        provider = get_data_provider()
        config_result = await provider.admin.get_config()
        config_data = config_result.get("config", {})
        platform_fee = config_data.get("platform_fee_percent", 0.15)  # Default 15%
    except Exception as e:
        logger.warning(f"Failed to load admin config, using default fee: {e}")
        platform_fee = 0.15

    return {
        "ok": True,
        "platform_fee_percent": platform_fee,
        "platform_fee_display": format_fee_percent_display(platform_fee),
        "min_price": 0,
        "max_price": 1000,  # $1000 in dollars
    }


@router.get("/platform/fee-preview")
async def get_fee_preview(
    price: float = Query(..., ge=0, description="Price in dollars"),
):
    """
    Calculate fee breakdown for a given price using current platform fee.

    Used by publish forms to show creator earnings preview.
    """
    try:
        provider = get_data_provider()
        config_result = await provider.admin.get_config()
        config_data = config_result.get("config", {})
        platform_fee = config_data.get("platform_fee_percent", 0.15)
    except Exception as e:
        logger.warning(f"Failed to load admin config, using default fee: {e}")
        platform_fee = 0.15

    preview = calculate_fee_preview(price, platform_fee)
    return {"ok": True, **preview}


@router.get("/platform/net-credits")
async def get_net_credits(
    call_price: int = Query(..., ge=0, description="Credits per call"),
):
    """
    Calculate net credits after platform fee for per-call pricing.

    Used by publish forms to show per-call earnings preview.
    """
    try:
        provider = get_data_provider()
        config_result = await provider.admin.get_config()
        config_data = config_result.get("config", {})
        platform_fee = config_data.get("platform_fee_percent", 0.15)
    except Exception as e:
        logger.warning(f"Failed to load admin config, using default fee: {e}")
        platform_fee = 0.15

    result = calculate_net_credits(call_price, platform_fee)
    return {"ok": True, **result}


@router.get("/validation-rules")
async def get_validation_rules():
    """
    Expose validation rules for frontend UX mirroring.

    Frontend validators mirror these rules for instant feedback.
    Backend re-validates on every save/submit using the same constants.
    """
    from common.validation_rules import (
        PASSWORD_MIN_LENGTH,
        PASSWORD_MAX_LENGTH,
        PASSWORD_REQUIRE_UPPERCASE,
        PASSWORD_REQUIRE_LOWERCASE,
        PASSWORD_REQUIRE_NUMBER,
        EMAIL_MAX_LENGTH,
        EMAIL_PATTERN,
        TEMPLATE_NAME_MIN_LENGTH,
        TEMPLATE_NAME_MAX_LENGTH,
        TEMPLATE_DESCRIPTION_MAX_LENGTH,
        TEMPLATE_ID_MAX_LENGTH,
        TEMPLATE_ID_PATTERN,
        GRID_COLUMN_TOTAL,
        GRID_COLUMN_MIN,
        GRID_COLUMN_MAX,
        USERNAME_PATTERN,
    )

    return {
        "ok": True,
        "rules": {
            "password": {
                "minLength": PASSWORD_MIN_LENGTH,
                "maxLength": PASSWORD_MAX_LENGTH,
                "requireUppercase": PASSWORD_REQUIRE_UPPERCASE,
                "requireLowercase": PASSWORD_REQUIRE_LOWERCASE,
                "requireNumber": PASSWORD_REQUIRE_NUMBER,
            },
            "email": {
                "maxLength": EMAIL_MAX_LENGTH,
                "pattern": EMAIL_PATTERN,
            },
            "template": {
                "nameMinLength": TEMPLATE_NAME_MIN_LENGTH,
                "nameMaxLength": TEMPLATE_NAME_MAX_LENGTH,
                "descriptionMaxLength": TEMPLATE_DESCRIPTION_MAX_LENGTH,
                "idMaxLength": TEMPLATE_ID_MAX_LENGTH,
                "idPattern": TEMPLATE_ID_PATTERN,
            },
            "grid": {
                "columnTotal": GRID_COLUMN_TOTAL,
                "columnMin": GRID_COLUMN_MIN,
                "columnMax": GRID_COLUMN_MAX,
            },
            "username": {
                "pattern": USERNAME_PATTERN,
            },
        },
    }


@router.get("/constants")
async def get_shared_constants():
    """
    Get shared constants for frontend synchronization.

    Returns canonical category definitions and application metadata.
    Frontend should use this as single source of truth for categories.
    """
    return {
        "ok": True,
        "data": {
            "app": {
                "name": APP_NAME,
                "version": APP_VERSION,
            },
            "categories": {
                "defaults": CATEGORY_DEFAULTS,
                "visible": list(DEFAULT_VISIBILITY_CATEGORIES),
                "fallback": DEFAULT_CATEGORY_META,
            },
        },
    }


@router.get("/categories")
async def get_category_definitions():
    """
    Get category definitions for module display.

    Returns icon names, colors, and node types for each category.
    """
    return {
        "ok": True,
        "data": {
            "categories": CATEGORY_DEFAULTS,
            "visible": list(DEFAULT_VISIBILITY_CATEGORIES),
            "default": DEFAULT_CATEGORY_META,
        },
    }


@router.get("/categories/visible")
async def get_visible_categories():
    """
    Get list of categories visible by default in UI.

    Returns list of category slugs that should be shown by default.
    """
    return {
        "ok": True,
        "data": list(DEFAULT_VISIBILITY_CATEGORIES),
    }
