"""
Worker Resource Management

Resource checking and limits.
"""

import os
import logging

from services.runtime.worker.config import WorkerConfig

logger = logging.getLogger(__name__)


def check_resources(config: WorkerConfig) -> bool:
    """
    Check if worker has sufficient resources.

    Args:
        config: Worker configuration

    Returns:
        True if resources available, False otherwise
    """
    if config.max_memory_mb > 0:
        try:
            import psutil

            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024

            if memory_mb > config.max_memory_mb:
                logger.warning(
                    f"Memory limit exceeded: {memory_mb:.1f}MB "
                    f"> {config.max_memory_mb}MB"
                )
                return False
        except ImportError:
            # psutil not available, skip memory check
            pass

    return True
