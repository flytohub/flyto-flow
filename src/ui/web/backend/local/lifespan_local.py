"""Flyto2 Flow startup helpers with no hosted device or job polling."""

import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def cleanup_stale_browser_locks() -> None:
    """Remove Chromium singleton files left by an interrupted local run."""
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
    """Initialize the local capability context once during application startup."""
    from capabilities import auto_init_context, has_capability_context

    if not has_capability_context():
        auto_init_context()


def init_breakpoint_manager() -> None:
    """Initialize optional breakpoint support without blocking local startup."""
    try:
        from services.breakpoint_setup import setup_breakpoint_manager

        setup_breakpoint_manager()
    except Exception as exc:
        logger.debug("Breakpoint manager setup skipped: %s", exc)


_STARTER_TEMPLATES = [
    {
        "id": "flyto2.http-get-mcp",
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
    {
        "id": "flyto2.browser-screenshot-mcp",
        "name": "Browser Screenshot Tool",
        "description": (
            "Starter template: expose a headless-browser screenshot as a callable "
            "MCP tool. Pass a URL, get back a PNG screenshot."
        ),
        "category": "general",
        "tags": ["starter", "browser", "screenshot"],
        "steps": [
            {
                "id": "trigger",
                "module": "flow.trigger",
                "label": "MCP Trigger",
                "params": {
                    "trigger_type": "mcp",
                    "tool_name": "screenshot_tool",
                    "tool_description": "Take a screenshot of a webpage.",
                    "config": {
                        "input_fields": [
                            {
                                "name": "url",
                                "type": "string",
                                "description": "The URL to screenshot",
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
                "id": "ensure",
                "module": "browser.ensure",
                "label": "Ensure Browser",
                "params": {"headless": True, "width": 1280, "height": 720},
                "position_x": 400,
                "position_y": 150,
                "order_index": 1,
            },
            {
                "id": "goto",
                "module": "browser.goto",
                "label": "Go to URL",
                "params": {
                    "url": "${url}",
                    "wait_until": "domcontentloaded",
                    "timeout_ms": 30000,
                    "ssrf_protection": True,
                },
                "position_x": 700,
                "position_y": 150,
                "order_index": 2,
            },
            {
                "id": "shot",
                "module": "browser.screenshot",
                "label": "Take Screenshot",
                "params": {"path": "screenshot.png", "full_page": False, "format": "png"},
                "position_x": 1000,
                "position_y": 150,
                "order_index": 3,
            },
            {
                "id": "close",
                "module": "browser.close",
                "label": "Close Browser",
                "params": {},
                "position_x": 1300,
                "position_y": 150,
                "order_index": 4,
            },
        ],
        "ui": {"components": [], "sections": [], "viewport": {"x": 0, "y": 0, "zoom": 1}},
    },
    {
        "id": "flyto2.json-to-csv-mcp",
        "name": "JSON to CSV Tool",
        "description": (
            "Starter template: expose a JSON-to-CSV converter as a callable "
            "MCP tool. Pass an array of records, get back a CSV file."
        ),
        "category": "general",
        "tags": ["starter", "data", "csv"],
        "steps": [
            {
                "id": "trigger",
                "module": "flow.trigger",
                "label": "MCP Trigger",
                "params": {
                    "trigger_type": "mcp",
                    "tool_name": "json_to_csv_tool",
                    "tool_description": "Convert a JSON array of records into a CSV file.",
                    "config": {
                        "input_fields": [
                            {
                                "name": "records",
                                "type": "array",
                                "description": "Array of JSON objects to convert to CSV",
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
                "id": "convert",
                "module": "data.json_to_csv",
                "label": "JSON to CSV",
                "params": {
                    "input_data": "${records}",
                    "output_path": "csv_output.csv",
                    "include_header": True,
                    "flatten_nested": True,
                },
                "position_x": 400,
                "position_y": 150,
                "order_index": 1,
            },
        ],
        "ui": {"components": [], "sections": [], "viewport": {"x": 0, "y": 0, "zoom": 1}},
    },
]


async def seed_starter_templates(extensions=()) -> None:
    """Create official starter templates on first run (empty template library only)."""
    try:
        from gateway.local_context import LOCAL_WORKSPACE
        from gateway.providers.data.offline.template import OfflineTemplateProvider
        from gateway.providers.data.models import TemplateCreateDTO
        from services.extensions.templates import load_template_packs

        provider = OfflineTemplateProvider()
        existing = await provider.list_workspace_templates(
            workspace_id=LOCAL_WORKSPACE.id, page=1, page_size=1
        )
        if existing.total > 0:
            return

        starters = [*(_STARTER_TEMPLATES)]
        starters.extend(
            {
                "id": template.id,
                **template.create_payload(),
            }
            for template in load_template_packs(extensions)
        )
        identifiers = [starter["id"] for starter in starters]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Starter template IDs must be unique")

        for starter in starters:
            await provider.create_template(
                workspace_id=LOCAL_WORKSPACE.id,
                data=TemplateCreateDTO(
                    **{key: value for key, value in starter.items() if key != "id"}
                ),
            )
        logger.info("Seeded %s starter template(s)", len(starters))
    except Exception as exc:
        logger.warning(
            "Starter template seed skipped (%s)",
            type(exc).__name__,
        )
