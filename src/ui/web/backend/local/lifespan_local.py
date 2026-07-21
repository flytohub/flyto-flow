"""Cloud CE startup helpers with no hosted device or job polling."""

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
