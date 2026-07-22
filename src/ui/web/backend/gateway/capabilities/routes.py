"""Static capability contract for Flyto2 Flow."""

from fastapi import APIRouter

router = APIRouter(tags=["capabilities"])

CAPABILITIES = [
    "core.workflow_run",
    "core.template_builder",
    "core.execution_history",
    "core.basic_logging",
    "storage.sqlite",
    "workflow.local_execution",
    "template.import",
    "mcp.server",
    "local.metrics",
    "local.tracing",
    "local.alerts",
]

PAGES = {
    "/": True,
    "/my-templates": True,
    "/templates/*": True,
    "/templates/builder": True,
    "/templates/builder/*": True,
    "/executions/*": True,
    "/variables": True,
    "/observability": True,
    "/observability/*": True,
}


def _response() -> dict:
    return {
        "edition": "ce",
        "deployment": "local_offline",
        "accountRequired": False,
        "capabilities": CAPABILITIES,
        "pages": PAGES,
        "network": {
            "implicitOutboundAllowed": False,
            "runtimeDependencyDownloadAllowed": False,
        },
    }


@router.get("/capabilities")
async def get_capabilities():
    return _response()


@router.post("/capabilities/reload")
async def reload_capabilities():
    return _response()
