"""
Queue Factory

Factory for creating queue implementations based on configuration.
Supports SQLite (default) and Redis (distributed) backends.
"""

import logging
import os
from typing import Optional

from gateway.storage.queue_interface import QueueInterface

logger = logging.getLogger(__name__)

# Environment variable for queue backend selection
QUEUE_BACKEND_ENV = "FLYTO_QUEUE_BACKEND"
REDIS_URL_ENV = "REDIS_URL"

# Supported backends
BACKEND_SQLITE = "sqlite"
BACKEND_REDIS = "redis"

# Global queue instance (singleton)
_queue_instance: Optional[QueueInterface] = None


def get_queue_backend() -> str:
    """
    Get the configured queue backend.

    Environment variable FLYTO_QUEUE_BACKEND:
    - "sqlite" (default): SQLite-based queue for single instance
    - "redis": Redis-based queue for distributed deployment

    Returns:
        Backend name string
    """
    backend = os.getenv(QUEUE_BACKEND_ENV, BACKEND_SQLITE).lower()

    if backend not in (BACKEND_SQLITE, BACKEND_REDIS):
        logger.warning(f"Unknown queue backend '{backend}', falling back to SQLite")
        return BACKEND_SQLITE

    return backend


def create_queue(backend: Optional[str] = None) -> QueueInterface:
    """
    Create a new queue instance.

    Args:
        backend: Backend to use (default: from environment)

    Returns:
        QueueInterface implementation
    """
    backend = backend or get_queue_backend()

    if backend == BACKEND_REDIS:
        redis_url = os.getenv(REDIS_URL_ENV, "redis://localhost:6379")
        logger.info(f"Creating Redis queue with URL: {redis_url}")

        from gateway.storage.redis_queue import RedisQueue
        return RedisQueue(redis_url=redis_url)

    else:
        logger.info("Creating SQLite queue")
        from gateway.storage.sqlite_queue import SQLiteQueue
        return SQLiteQueue()


def get_queue() -> QueueInterface:
    """
    Get or create the singleton queue instance.

    Returns:
        QueueInterface implementation
    """
    global _queue_instance

    if _queue_instance is None:
        _queue_instance = create_queue()
        logger.info(f"Created queue instance: {type(_queue_instance).__name__}")

    return _queue_instance


def reset_queue() -> None:
    """
    Reset the queue instance.

    Useful for testing or configuration changes.
    """
    global _queue_instance
    _queue_instance = None
    logger.info("Queue instance reset")


async def get_queue_health() -> dict:
    """
    Get queue health status.

    Returns:
        Health status dict
    """
    try:
        queue = get_queue()
        return await queue.health_check()
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
        }
