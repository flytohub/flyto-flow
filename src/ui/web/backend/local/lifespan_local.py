"""Flyto2 Flow startup helpers with no hosted device or job polling."""

import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def cleanup_stale_browser_locks() -> None:
    profile = Path.home() / ".flyto" / "chrome-profile"
    if not profile.exists():
        return
    for name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        lock = profile / name
        if lock.exists() or lock.is_symlink():
            try:
                lock.unlink()
            except OSError:
                logger.debug("Unable to remove stale browser lock %s", lock)


async def init_capabilities() -> None:
    from capabilities import auto_init_context, has_capability_context

    if not has_capability_context():
        auto_init_context()


def init_breakpoint_manager() -> None:
    try:
        from services.breakpoint_setup import setup_breakpoint_manager

        setup_breakpoint_manager()
    except Exception as exc:
        logger.debug("Breakpoint manager setup skipped: %s", exc)


_STARTER_TEMPLATES = [
    {
        "name": "HTTP GET Request Tool",
        "description": (
            "Starter template: expose an HTTP GET request as a callable MCP tool. "
            "Pass a URL, get back the response."
        ),
        "category": "general",
        "tags": ["starter", "http", "api"],
        "steps": [
            {
                "id": "trigger",
                "module": "flow.trigger",
                "label": "MCP Trigger",
                "params": {
                    "trigger_type": "mcp",
                    "tool_name": "http_get_tool",
                    "tool_description": "Fetch a URL via HTTP GET and return the response.",
                    "config": {
                        "input_fields": [
                            {
                                "name": "url",
                                "type": "string",
                                "description": "The URL to fetch",
                                "required": True,
                            }
                        ]
                    },
                },
                "position_x": 100,
                "position_y": 150,
                "order_index": 0,
            },
            {
                "id": "http_get",
                "module": "core.api.http_get",
                "label": "HTTP GET Request",
                "params": {
                    "url": "${url}",
                    "headers": {},
                    "params": {},
                    "timeout": 30,
                    "verify_ssl": True,
                },
                "position_x": 400,
                "position_y": 150,
                "order_index": 1,
            },
        ],
        "ui": {"components": [], "sections": [], "viewport": {"x": 0, "y": 0, "zoom": 1}},
    },
]


async def seed_starter_templates() -> None:
    """Create official starter templates on first run (empty template library only)."""
    try:
        from gateway.local_context import LOCAL_WORKSPACE
        from gateway.providers.data.offline.template import OfflineTemplateProvider
        from gateway.providers.data.models import TemplateCreateDTO

        provider = OfflineTemplateProvider()
        existing = await provider.list_workspace_templates(
            workspace_id=LOCAL_WORKSPACE.id, page=1, page_size=1
        )
        if existing.total > 0:
            return

        for starter in _STARTER_TEMPLATES:
            await provider.create_template(
                workspace_id=LOCAL_WORKSPACE.id,
                data=TemplateCreateDTO(**starter),
            )
        logger.info(f"Seeded {len(_STARTER_TEMPLATES)} starter template(s)")
    except Exception as exc:
        logger.warning(f"Starter template seed skipped: {exc}")
