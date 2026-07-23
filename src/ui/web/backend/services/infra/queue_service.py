"""
Queue Service

High-level API for job queue operations.
Provides a clean interface for enqueueing executions and managing jobs.
"""

import logging
from typing import Any, Dict, Optional

from gateway.storage.queue_interface import QueueJob
from services.runtime.worker_pool import get_worker_pool

logger = logging.getLogger(__name__)


class QueueService:
    """
    High-level service for queue operations.

    Provides a facade over the job queue repository with
    additional business logic and worker pool integration.

    Usage:
        # Enqueue a new execution
        job = await QueueService.enqueue_execution(
            execution_id="exec-123",
            workflow_id="wf-456",
            workspace_id="user-789",
        )

        # Cancel an execution
        cancelled = await QueueService.cancel_execution("exec-123")

        # Get job status
        status = await QueueService.get_job_status("exec-123")
    """

    @staticmethod
    async def enqueue_execution(
        execution_id: str,
        workflow_id: str,
        workspace_id: Optional[str] = None,
        priority: int = 0,
        max_attempts: int = 3,
        timeout_ms: int = 0,
        visibility_timeout_ms: int = 30000,
    ) -> QueueJob:
        """
        Enqueue an execution for processing.

        Creates a job in the queue that will be picked up by a worker.

        Args:
            execution_id: ID of the execution record
            workflow_id: ID of the workflow being executed
            workspace_id: Optional workspace who triggered the execution
            priority: Job priority (higher = more urgent)
            max_attempts: Maximum retry attempts on failure
            timeout_ms: Execution timeout (0 = no limit)
            visibility_timeout_ms: Delay before retry after failure

        Returns:
            Created Job instance

        Raises:
            Exception: If enqueueing fails
        """
        from gateway.storage.queue_factory import get_queue

        job = await get_queue().enqueue(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            priority=priority,
            max_attempts=max_attempts,
            timeout_ms=timeout_ms,
            visibility_timeout_ms=visibility_timeout_ms,
            idempotency_key=execution_id,
        )

        logger.info(
            f"Execution {execution_id} enqueued as job {job.id} "
            f"(priority={priority})"
        )

        return job

    @staticmethod
    async def cancel_execution(
        execution_id: str,
        reason: str = "User cancelled",
    ) -> bool:
        """
        Cancel an execution.

        If the job is pending, it's cancelled immediately.
        If running, attempts graceful cancellation via worker pool.

        Args:
            execution_id: Execution to cancel
            reason: Cancellation reason

        Returns:
            True if cancelled, False if not found or already completed
        """
        # Try to cancel via worker pool first (for running jobs)
        pool = get_worker_pool()
        if pool is not None and pool.is_running:
            if await pool.cancel_execution(execution_id, reason):
                logger.info(f"Execution {execution_id} cancelled via worker pool")
                return True

        # Fall back to direct queue cancellation (for pending jobs)
        from gateway.storage.queue_factory import get_queue

        cancelled = await get_queue().cancel_by_execution_id(execution_id)

        if cancelled:
            logger.info(f"Execution {execution_id} cancelled in queue")
        else:
            logger.warning(
                f"Failed to cancel execution {execution_id} - "
                "not found or already completed"
            )

        return cancelled

    @staticmethod
    async def get_job_status(execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a job by execution ID.

        Args:
            execution_id: Execution to look up

        Returns:
            Job status dict or None if not found
        """
        from gateway.storage.queue_factory import get_queue

        job = await get_queue().get_by_execution_id(execution_id)

        if not job:
            return None

        return {
            "job_id": job.id,
            "execution_id": job.execution_id,
            "status": job.status,
            "priority": job.priority,
            "attempts": job.attempts,
            "max_attempts": job.max_attempts,
            "locked_by": job.locked_by,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
        }

    @staticmethod
    async def get_queue_stats() -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dictionary with queue statistics
        """
        from gateway.storage.queue_factory import get_queue

        stats = (await get_queue().get_stats()).to_dict()

        # Add worker pool stats if available
        pool = get_worker_pool()
        if pool is not None:
            pool_stats = pool.get_stats()
            stats["worker_pool"] = pool_stats

        return stats

    @staticmethod
    async def retry_execution(execution_id: str) -> Optional[QueueJob]:
        """
        Retry a failed execution.

        Creates a new job for a previously failed execution.

        Args:
            execution_id: Execution to retry

        Returns:
            New Job if created, None if execution not found or not failed
        """
        from gateway.storage.queue_factory import get_queue

        queue = get_queue()
        existing_job = await queue.get_by_execution_id(execution_id)

        if not existing_job:
            logger.warning(f"Cannot retry - execution {execution_id} not found")
            return None

        if existing_job.status not in ("failed", "cancelled"):
            logger.warning(
                f"Cannot retry - execution {execution_id} status is "
                f"{existing_job.status}, expected failed or cancelled"
            )
            return None

        logger.warning(
            "Retry requires a new execution record; refusing to reuse execution %s",
            execution_id,
        )
        return None

    @staticmethod
    async def cleanup_old_jobs(days: int = 7) -> int:
        """
        Clean up old completed/failed/cancelled jobs.

        Args:
            days: Delete jobs older than this many days

        Returns:
            Number of jobs deleted
        """
        from gateway.storage.queue_factory import get_queue

        deleted = await get_queue().cleanup_old_jobs(days=days)
        logger.info(f"Cleaned up {deleted} old jobs")
        return deleted

    @staticmethod
    async def release_stale_leases() -> int:
        """
        Release jobs with expired leases.

        This recovers jobs from crashed workers.

        Returns:
            Number of leases released
        """
        from gateway.storage.queue_factory import get_queue

        released = await get_queue().release_expired_leases()
        if released > 0:
            logger.info(f"Released {released} expired job leases")
        return released
