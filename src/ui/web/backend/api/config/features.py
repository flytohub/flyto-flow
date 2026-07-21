"""
Config API — Features

Feature flags, quick start, messaging providers, and breakpoints configuration.
"""

import logging

from fastapi import APIRouter

from gateway.providers.hub import get_data_provider

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/feature-flags")
async def get_feature_flags(
    user_id: str = None,
):
    """
    Get enabled feature flags for the current user.

    Returns a map of flag_key -> enabled status.
    This endpoint is public but results may vary based on user_id.

    Query params:
        user_id: Optional user ID for targeted rollouts
    """
    try:
        provider = get_data_provider()
        result = await provider.admin.get_enabled_flags_for_user(user_id)
        if result.get("ok"):
            return {
                "ok": True,
                "flags": result.get("flags", {}),
            }
        return {"ok": True, "flags": {}}
    except Exception as e:
        logger.warning(f"Failed to get feature flags: {e}")
        return {"ok": True, "flags": {}}


@router.get("/quick-start")
async def get_quick_start_config():
    """
    Get quick start modules and onboarding configuration.
    """
    return {
        "ok": True,
        "modules": [
            "http.request",
            "llm.chat",
            "file.read",
            "flow.loop",
            "browser.goto",
            "data.json_parse",
        ],
        "onboarding_steps": [
            {"id": "create_workflow", "name": "Create your first workflow"},
            {"id": "add_module", "name": "Add a module"},
            {"id": "configure_params", "name": "Configure parameters"},
            {"id": "run_workflow", "name": "Run the workflow"},
            {"id": "view_results", "name": "View results"},
        ],
    }


@router.get("/messaging-providers")
async def get_messaging_providers_config():
    """
    Get supported messaging providers configuration.
    """
    return {
        "ok": True,
        "providers": [
            {
                "id": "line",
                "name": "LINE",
                "icon": "MessageCircle",
                "color": "#00B900",
                "config_fields": ["channel_id", "channel_secret", "access_token"],
            },
            {
                "id": "telegram",
                "name": "Telegram",
                "icon": "Send",
                "color": "#0088cc",
                "config_fields": ["bot_token"],
            },
            {
                "id": "slack",
                "name": "Slack",
                "icon": "Hash",
                "color": "#4A154B",
                "config_fields": ["bot_token", "signing_secret"],
            },
            {
                "id": "discord",
                "name": "Discord",
                "icon": "MessageSquare",
                "color": "#5865F2",
                "config_fields": ["bot_token", "application_id"],
            },
            {
                "id": "whatsapp",
                "name": "WhatsApp",
                "icon": "MessageCircle",
                "color": "#25D366",
                "config_fields": ["phone_number_id", "access_token", "verify_token"],
            },
        ],
    }


@router.get("/breakpoints")
async def get_breakpoints_config():
    """
    Get breakpoint types for debugging.
    """
    return {
        "ok": True,
        "types": [
            {"id": "step", "name": "Step", "description": "Break before step execution"},
            {"id": "condition", "name": "Conditional", "description": "Break when condition is true"},
            {"id": "error", "name": "Error", "description": "Break on error"},
            {"id": "checkpoint", "name": "Checkpoint", "description": "Save state checkpoint"},
        ],
        "actions": [
            {"id": "continue", "name": "Continue", "shortcut": "F5"},
            {"id": "step_over", "name": "Step Over", "shortcut": "F10"},
            {"id": "step_into", "name": "Step Into", "shortcut": "F11"},
            {"id": "step_out", "name": "Step Out", "shortcut": "Shift+F11"},
            {"id": "stop", "name": "Stop", "shortcut": "Shift+F5"},
        ],
    }
