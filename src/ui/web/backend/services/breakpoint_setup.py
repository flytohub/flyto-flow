"""
Breakpoint Manager Setup

Initializes the global breakpoint manager with the appropriate
store and notifier based on deployment mode.

- Local (desktop): InMemoryBreakpointStore + WebSocketBreakpointNotifier
- Cloud control plane: configured durable provider + WebSocketBreakpointNotifier
"""

import logging
import os

logger = logging.getLogger(__name__)


def setup_breakpoint_manager() -> None:
    """
    Configure the global breakpoint manager based on deployment mode.

    Call this once during server startup (in lifespan or deferred init).
    """
    from gateway.config import get_gateway_config

    config = get_gateway_config()

    # Worker uses flyto-core (HttpBreakpointStore → polls Cloud API).
    # Only the cloud control plane needs the durable provider-backed store.
    if config.is_cloud:
        _setup_cloud_manager()
    else:
        _setup_local_manager()


def _setup_cloud_manager():
    """Cloud mode: provider-backed manager, no flyto-core dependency."""
    try:
        from services.cloud.breakpoint_manager import (
            CloudBreakpointManager,
            set_cloud_breakpoint_manager,
        )
        from services.cloud.breakpoint_store import ProviderBreakpointStore

        store = ProviderBreakpointStore()
        manager = CloudBreakpointManager(store=store)
        set_cloud_breakpoint_manager(manager)
        logger.info("Breakpoint manager: durable provider store (cloud mode)")
    except Exception as e:
        logger.warning("Cloud breakpoint manager setup failed: %s", e)


def _setup_local_manager():
    """Local/worker mode: flyto-core manager with in-memory store."""
    try:
        _import_and_setup_local()
    except ImportError as e:
        logger.debug("Breakpoint manager setup skipped (flyto-core not available): %s", e)
    except Exception as e:
        logger.warning("Breakpoint manager setup failed: %s", e)


def _import_and_setup_local():
    from core.engine.breakpoints import (
        BreakpointManager,
        set_global_breakpoint_manager,
        InMemoryBreakpointStore,
    )

    from services.breakpoint_notifier import WebSocketBreakpointNotifier

    store = InMemoryBreakpointStore()
    logger.info("Breakpoint manager: in-memory store (local mode)")

    notifier = WebSocketBreakpointNotifier()
    manager = BreakpointManager(store=store, notifier=notifier)
    set_global_breakpoint_manager(manager)
    logger.info("Global breakpoint manager configured with WS notifier")
