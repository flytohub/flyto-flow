"""
Health Check Utilities

Provides startup tracking used by main.py.
"""

import logging

logger = logging.getLogger(__name__)

_startup_complete = False


def mark_startup_complete():
    """Mark startup as complete."""
    global _startup_complete
    _startup_complete = True
    logger.info("Startup marked as complete")
