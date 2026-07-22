"""
Local plugin runtime bridge for flyto-core UI notifications.

flyto-core already handles:
  - Plugin discovery, manifest parsing, security validation
  - Process lifecycle (spawn, health check, idle timeout, restart)
  - JSON-RPC communication (handshake, invoke, ping, shutdown)
  - Module catalog transformation

This bridge adds:
  - WebSocket forwarding for ui.open / ui.close notifications
  - Plugin step registration in ModuleRegistry on worker startup
  - Singleton access for the worker

Used by the local application lifecycle.
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _get_plugins_dir() -> str:
    """Resolve plugins directory from environment or default."""
    return os.environ.get(
        "FLYTO_PLUGINS_DIR",
        os.environ.get(
            "FLYTO_PLUGIN_DIR",
            str(Path.home() / ".flyto" / "plugins"),
        ),
    )


def _setup_notification_forwarding(manager) -> None:
    """
    Wire flyto-core PluginProcess notification callbacks to WebSocket broadcast.

    When a plugin sends a ui.open or ui.close notification, we forward it
    to the frontend via the execution WebSocket so PluginUIOverlay can show/hide.
    """
    original_discover = manager.discover_plugins

    async def discover_with_hooks():
        result = await original_discover()

        # After discovery, hook into each plugin's process notification callback
        for plugin_id, plugin_info in manager._plugins.items():
            proc = plugin_info.process

            def make_handler(pid):
                def on_notification(method, params):
                    if method in ("ui.open", "ui.close"):
                        try:
                            import asyncio
                            from services.websocket_manager import manager as ws_manager
                            exec_id = params.get("executionId", params.get("execution_id", ""))
                            asyncio.ensure_future(ws_manager.send_log(exec_id, {
                                "type": f"plugin_{method.replace('.', '_')}",
                                "plugin_id": pid,
                                **params,
                            }))
                        except Exception as e:
                            logger.debug(f"Failed to broadcast plugin {method}: {e}")
                return on_notification

            proc._on_message = make_handler(plugin_id)

        return result

    manager.discover_plugins = discover_with_hooks


async def init_plugins(plugins_dir: Optional[str] = None) -> int:
    """
    Initialize the plugin system using flyto-core's PluginManager.

    Returns the number of plugin steps discovered.
    """
    try:
        from core.runtime import PluginManager
    except ImportError:
        logger.debug("Plugin runtime not available (flyto-core missing core.runtime)")
        return 0

    pdir = plugins_dir or _get_plugins_dir()
    if not Path(pdir).is_dir():
        logger.debug(f"Plugins directory not found: {pdir}")
        return 0

    manager = PluginManager(plugin_dir=Path(pdir))
    _setup_notification_forwarding(manager)

    discovered = await manager.discover_plugins()
    total_steps = sum(
        len(manager.get_manifest(pid).steps)
        for pid in discovered
        if manager.get_manifest(pid)
    )

    if total_steps > 0:
        logger.info(f"Loaded {len(discovered)} plugins, {total_steps} steps")

    return total_steps


async def shutdown_plugins() -> None:
    """Shutdown all plugin processes via flyto-core's PluginManager."""
    try:
        from api.modules.catalog import get_plugin_manager
        manager = get_plugin_manager()
        if manager:
            await manager.shutdown()
    except Exception as e:
        logger.debug(f"Plugin shutdown: {e}")
