"""Flyto2 Cloud CE API assembly for the offline/self-hosted profile."""

from fastapi import APIRouter

from config.constants import APP_VERSION


def _register_local_routes(router: APIRouter) -> None:
    from api.agent import router as agent_router
    from api.ai import router as ai_router
    from api.breakpoint import breakpoint_router
    from api.breakpoint.screenshots import router as screenshots_router
    from api.browser import router as browser_router
    from api.content.i18n import router as i18n_router
    from api.core import router as core_router
    from api.debug import router as debug_router
    from api.engine import router as engine_router
    from api.evidence import router as evidence_router
    from api.executions import router as executions_router
    from api.files import router as files_router
    from api.lineage import router as lineage_router
    from api.modules import router as modules_router
    from api.observability.alerts import router as alerts_router
    from api.observability.metrics import router as metrics_router
    from api.observability.traces import router as traces_router
    from api.packages import router as packages_router
    from api.plugins import router as plugins_router
    from api.quality import router as quality_router
    from api.recording import router as recording_router
    from api.replay import router as replay_router
    from api.testing import router as testing_router
    from api.triggers import local_router as triggers_router
    from api.utils import router as utils_router
    from api.variables import router as variables_router
    from api.vector import router as vector_router
    from api.versioning import router as versioning_router
    from api.workflows import local_router as workflows_router
    from gateway.capabilities.routes import router as capabilities_router

    registrations = (
        (workflows_router, "/workflows", ["Workflows"]),
        (executions_router, "/executions", ["Executions"]),
        (modules_router, "", ["Modules"]),
        (plugins_router, "", ["Plugins"]),
        (core_router, "", ["Core"]),
        (i18n_router, "", ["i18n"]),
        (vector_router, "", ["Vector Store"]),
        (agent_router, "", ["AI Agent"]),
        (debug_router, "", ["Debug"]),
        (evidence_router, "/evidence", ["Evidence"]),
        (replay_router, "/replay", ["Replay"]),
        (breakpoint_router, "", ["Breakpoints"]),
        (files_router, "", ["Files"]),
        (screenshots_router, "", ["Screenshots"]),
        (engine_router, "/engine", ["Engine"]),
        (testing_router, "/testing", ["Testing"]),
        (variables_router, "", ["Variables"]),
        (lineage_router, "/lineage", ["Lineage"]),
        (versioning_router, "/versioning", ["Module Versioning"]),
        (triggers_router, "", ["Triggers"]),
        (capabilities_router, "", ["Capabilities"]),
        (quality_router, "", ["Quality"]),
        (recording_router, "", ["Recording"]),
        (metrics_router, "", ["Metrics"]),
        (alerts_router, "", ["Alerts"]),
        (traces_router, "", ["Traces"]),
        (browser_router, "", ["Browser"]),
        (utils_router, "", ["Utils"]),
        (packages_router, "", ["Packages"]),
    )
    if ai_router is not None:
        registrations += ((ai_router, "", ["AI"]),)
    for child, prefix, tags in registrations:
        router.include_router(child, prefix=prefix, tags=tags)


def create_offline_router() -> APIRouter:
    from api.auth.config import router as auth_config_router
    from api.auth.login import router as auth_login_router
    from api.config import router as config_router
    from api.expression import router as expression_router
    from api.mcp import router as mcp_router
    from api.recipe_bundles import router as recipe_bundles_router
    from api.runtime_config import router as runtime_config_router
    from api.templates_offline import router as templates_router
    from api.ui_config import router as ui_config_router
    from api.workflows.crud import crud_router

    router = APIRouter(prefix="/api")
    router.include_router(runtime_config_router, tags=["Runtime"])
    _register_local_routes(router)
    router.include_router(auth_login_router, prefix="/auth", tags=["Auth"])
    router.include_router(auth_config_router, prefix="/auth", tags=["Auth"])
    router.include_router(crud_router, prefix="/workflows", tags=["Workflows"])
    router.include_router(templates_router, tags=["Templates"])
    router.include_router(recipe_bundles_router, tags=["Recipe Bundles"])
    router.include_router(mcp_router, tags=["MCP"])
    router.include_router(ui_config_router, tags=["UI Config"])
    router.include_router(expression_router, tags=["Expression"])
    router.include_router(config_router, tags=["Config"])

    @router.get("/app/version")
    async def app_version():
        return {"version": APP_VERSION}

    return router


__all__ = ["create_offline_router"]
