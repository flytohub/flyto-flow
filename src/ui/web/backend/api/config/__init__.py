"""
Config API Routes

Platform configuration endpoints.

Split into sub-modules for maintainability.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/config", tags=["Config"])

from .general import router as general_router
from .ui import router as ui_router
from .modules import router as modules_router
from .business import router as business_router
from .features import router as features_router

router.include_router(general_router)
router.include_router(ui_router)
router.include_router(modules_router)
router.include_router(business_router)
router.include_router(features_router)


# ============================================================
# Aggregator: get_all_config
# ============================================================


@router.get("/all")
async def get_all_config():
    """
    Get all frontend configuration in a single request.

    S-Grade: Single endpoint to fetch all config at app startup.
    Reduces number of API calls needed during initialization.
    """
    from .ui import (
        get_timing_config,
        get_layout_config,
        get_theme_config,
        get_limits_config,
        get_shortcuts_config,
    )
    from .modules import (
        get_llm_config,
        get_trigger_config,
        get_http_config,
        get_param_type_config,
        get_node_design_config,
    )
    from .business import (
        get_marketplace_config,
        get_subscription_config,
        get_workflow_types_config,
        get_form_types_config,
        get_countries_config,
    )
    from .features import (
        get_quick_start_config,
        get_messaging_providers_config,
        get_breakpoints_config,
    )
    from .general import get_validation_rules

    timing = (await get_timing_config())["timing"]
    layout = (await get_layout_config())["layout"]
    theme = (await get_theme_config())["theme"]
    limits = (await get_limits_config())["limits"]
    shortcuts = (await get_shortcuts_config())["shortcuts"]
    node_design = (await get_node_design_config())["node_design"]
    llm = await get_llm_config()
    triggers = await get_trigger_config()
    http = await get_http_config()
    param_types = await get_param_type_config()
    marketplace = await get_marketplace_config()
    subscription = await get_subscription_config()
    workflow_types = await get_workflow_types_config()
    form_types = await get_form_types_config()
    countries = await get_countries_config()
    quick_start = await get_quick_start_config()
    messaging = await get_messaging_providers_config()
    breakpoints = await get_breakpoints_config()
    validation_rules = (await get_validation_rules())["rules"]

    return {
        "ok": True,
        "config": {
            "timing": timing,
            "layout": layout,
            "theme": theme,
            "limits": limits,
            "shortcuts": shortcuts,
            "llm": {
                "providers": llm["providers"],
                "defaults": llm["defaults"],
            },
            "triggers": {
                "types": triggers["trigger_types"],
                "defaults": triggers["defaults"],
            },
            "http": {
                "methods": http["methods"],
                "auth_types": http["auth_types"],
                "body_types": http["body_types"],
                "defaults": http["defaults"],
            },
            "param_types": param_types["param_type_map"],
            "output_types": param_types["output_type_map"],
            "marketplace": marketplace,
            "subscription": subscription,
            "workflow_types": workflow_types,
            "form_types": form_types,
            "countries": countries["stripe_supported"],
            "quick_start": quick_start,
            "messaging": messaging,
            "breakpoints": breakpoints,
            "node_design": node_design,
            "validation_rules": validation_rules,
        },
    }
