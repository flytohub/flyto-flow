"""
Queue Integration

Worker pool management for queue-based execution (Phase 1).
"""

import logging
import os

logger = logging.getLogger(__name__)

# Queue mode configuration
# Set FLYTO_USE_QUEUE=1 to enable queue-based execution
USE_QUEUE = os.getenv("FLYTO_USE_QUEUE", "0").lower() in ("1", "true", "yes")


async def start_worker_pool(pool_size: int = 4) -> None:
    """
    Start the worker pool for queue-based execution.

    Call this at application startup when USE_QUEUE is enabled.

    Args:
        pool_size: Number of workers in the pool (default: 4)

    Raises:
        Exception: If worker pool fails to start
    """
    if not USE_QUEUE:
        logger.info("Queue mode disabled, skipping worker pool startup")
        return

    try:
        from services.runtime.worker_pool import start_worker_pool as _start_pool
        from services.runtime.worker_pool import WorkerPoolConfig
        from services.runtime.worker import WorkerConfig

        worker_config = WorkerConfig(
            poll_interval_seconds=1.0,
            heartbeat_interval_seconds=10.0,
            lease_duration_seconds=300,
            max_concurrent_jobs=1,
        )

        config = WorkerPoolConfig(
            pool_size=pool_size,
            worker_config=worker_config,
        )

        await _start_pool(config)
        logger.info(f"Worker pool started with {pool_size} workers")

    except Exception as e:
        logger.error(f"Failed to start worker pool: {e}")
        raise


async def stop_worker_pool(timeout: float = 30.0) -> None:
    """
    Stop the worker pool gracefully.

    Call this at application shutdown.

    Args:
        timeout: Maximum seconds to wait for workers to finish (default: 30)
    """
    if not USE_QUEUE:
        return

    try:
        from services.runtime.worker_pool import stop_worker_pool as _stop_pool
        await _stop_pool(timeout=timeout)
        logger.info("Worker pool stopped")

    except Exception as e:
        logger.error(f"Failed to stop worker pool: {e}")


async def get_queue_stats() -> dict:
    """
    Get queue and worker pool statistics.

    Returns:
        Dictionary with queue stats including:
        - queue_enabled: Whether queue mode is enabled
        - pending_jobs: Number of jobs waiting
        - active_workers: Number of active workers
        - error: Error message if stats retrieval failed
    """
    if not USE_QUEUE:
        return {"queue_enabled": False}

    try:
        from services.infra.queue_service import QueueService
        stats = await QueueService.get_queue_stats()
        stats["queue_enabled"] = True
        return stats

    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        return {"queue_enabled": True, "error": str(e)}


async def enqueue_execution(
    execution_id: str,
    workflow_id: str,
    workspace_id: str | None,
    priority: int = 0,
) -> bool:
    """
    Enqueue an execution job for worker pool processing.

    Args:
        execution_id: Unique execution identifier
        workflow_id: Workflow being executed
        workspace_id: User who started the execution
        priority: Job priority (higher = more urgent)

    Returns:
        True if successfully enqueued, False otherwise
    """
    try:
        from services.infra.queue_service import QueueService
        await QueueService.enqueue_execution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            priority=priority,
        )
        logger.info(f"Enqueued execution {execution_id} for workflow {workflow_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to enqueue execution: {e}")
        return False


async def cancel_queued_execution(execution_id: str, reason: str = "User cancelled") -> bool:
    """
    Cancel a queued execution.

    Args:
        execution_id: Execution to cancel
        reason: Cancellation reason

    Returns:
        True if successfully cancelled, False otherwise
    """
    try:
        from services.infra.queue_service import QueueService
        return await QueueService.cancel_execution(execution_id, reason)
    except Exception as e:
        logger.error(f"Failed to cancel queued execution: {e}")
        return False
