"""
Execution Utilities

Helper functions for execution management.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# SQLite initialization state
_sqlite_initialized = False


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    Returns:
        Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def ensure_sqlite_initialized() -> None:
    """
    Initialize SQLite database for execution records.

    This is called lazily on first execution to ensure the database
    is ready. Safe to call multiple times - will only initialize once.
    """
    global _sqlite_initialized
    if _sqlite_initialized:
        return

    try:
        from gateway.storage import init_db
        init_db()
        _sqlite_initialized = True
        logger.info("SQLite execution database initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize SQLite: {e}")
