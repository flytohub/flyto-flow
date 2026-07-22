"""Configure the local flyto-core breakpoint manager."""

import logging


logger = logging.getLogger(__name__)


def setup_breakpoint_manager() -> None:
    try:
        from core.engine.breakpoints import (
            BreakpointManager,
            InMemoryBreakpointStore,
            set_global_breakpoint_manager,
        )
        from services.breakpoint_notifier import WebSocketBreakpointNotifier

        manager = BreakpointManager(
            store=InMemoryBreakpointStore(),
            notifier=WebSocketBreakpointNotifier(),
        )
        set_global_breakpoint_manager(manager)
        logger.info("Local in-memory breakpoint manager configured")
    except ImportError as exc:
        logger.debug("Breakpoint manager unavailable: %s", exc)
    except Exception as exc:
        logger.warning("Breakpoint manager setup failed: %s", exc)
