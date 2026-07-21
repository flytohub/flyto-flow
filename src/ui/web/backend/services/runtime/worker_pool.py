"""
Worker Pool Manager

Manages a pool of workers for parallel job processing.
Provides startup, shutdown, and monitoring capabilities.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.runtime.worker import Worker, WorkerConfig

logger = logging.getLogger(__name__)


@dataclass
class WorkerPoolConfig:
    """Worker pool configuration."""

    pool_size: int = 4
    worker_config: Optional[WorkerConfig] = None

    def __post_init__(self):
        """Initialize default worker config if not provided."""
        if self.worker_config is None:
            self.worker_config = WorkerConfig()


class WorkerPool:
    """
    Manages a pool of workers.

    Provides:
    - Parallel job processing across multiple workers
    - Graceful startup and shutdown
    - Health monitoring and statistics
    - Dynamic scaling (future)

    Usage:
        config = WorkerPoolConfig(pool_size=4)
        pool = WorkerPool(config)

        # Start pool (non-blocking)
        await pool.start()

        # ... application running ...

        # Stop pool gracefully
        await pool.stop()
    """

    def __init__(self, config: Optional[WorkerPoolConfig] = None):
        """
        Initialize worker pool.

        Args:
            config: Pool configuration
        """
        self.config = config or WorkerPoolConfig()
        self._workers: List[Worker] = []
        self._tasks: List[asyncio.Task] = []
        self._running = False
        self._started_at: Optional[str] = None

    @property
    def is_running(self) -> bool:
        """Check if pool is running."""
        return self._running

    @property
    def worker_count(self) -> int:
        """Get number of workers in pool."""
        return len(self._workers)

    @property
    def active_job_count(self) -> int:
        """Get total number of active jobs across all workers."""
        return sum(w.active_job_count for w in self._workers)

    async def start(self) -> None:
        """
        Start all workers in the pool.

        This method returns immediately after starting workers.
        Workers run in background tasks.
        """
        if self._running:
            logger.warning("Worker pool already running")
            return

        self._running = True
        self._started_at = datetime.now(timezone.utc).isoformat()

        logger.info(f"Starting worker pool with {self.config.pool_size} workers...")

        # Create and start workers
        for i in range(self.config.pool_size):
            # Create unique worker ID
            base_id = self.config.worker_config.worker_id
            worker_config = WorkerConfig(
                worker_id=f"{base_id}-{i}",
                poll_interval_seconds=self.config.worker_config.poll_interval_seconds,
                heartbeat_interval_seconds=self.config.worker_config.heartbeat_interval_seconds,
                lease_duration_seconds=self.config.worker_config.lease_duration_seconds,
                max_concurrent_jobs=self.config.worker_config.max_concurrent_jobs,
                max_memory_mb=self.config.worker_config.max_memory_mb,
                max_execution_time_ms=self.config.worker_config.max_execution_time_ms,
            )

            worker = Worker(worker_config)
            self._workers.append(worker)

            # Start worker in background task
            task = asyncio.create_task(
                worker.start(),
                name=f"worker-{i}",
            )
            self._tasks.append(task)

        logger.info(f"Worker pool started with {len(self._workers)} workers")

    async def stop(self, timeout: float = 30.0) -> None:
        """
        Stop all workers gracefully.

        Args:
            timeout: Maximum seconds to wait per worker
        """
        if not self._running:
            return

        logger.info("Stopping worker pool...")
        self._running = False

        # Stop all workers gracefully
        stop_tasks = [
            worker.stop(timeout=timeout)
            for worker in self._workers
        ]

        try:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error stopping workers: {e}")

        # Cancel any remaining background tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._workers.clear()
        self._tasks.clear()

        logger.info("Worker pool stopped")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get pool statistics.

        Returns:
            Dictionary with pool stats
        """
        worker_stats = [
            {
                "worker_id": w.config.worker_id,
                "is_running": w.is_running,
                "active_jobs": w.active_job_count,
                **w.stats,
            }
            for w in self._workers
        ]

        total_processed = sum(w.stats.get("jobs_processed", 0) for w in self._workers)
        total_succeeded = sum(w.stats.get("jobs_succeeded", 0) for w in self._workers)
        total_failed = sum(w.stats.get("jobs_failed", 0) for w in self._workers)

        return {
            "is_running": self._running,
            "started_at": self._started_at,
            "pool_size": self.config.pool_size,
            "active_workers": len([w for w in self._workers if w.is_running]),
            "total_active_jobs": self.active_job_count,
            "total_jobs_processed": total_processed,
            "total_jobs_succeeded": total_succeeded,
            "total_jobs_failed": total_failed,
            "workers": worker_stats,
        }

    async def cancel_job(self, job_id: str, reason: str = "Cancelled") -> bool:
        """
        Cancel a specific job across all workers.

        Args:
            job_id: Job to cancel
            reason: Cancellation reason

        Returns:
            True if job was found and cancelled
        """
        for worker in self._workers:
            if await worker.cancel_job(job_id, reason):
                return True
        return False

    async def cancel_execution(
        self,
        execution_id: str,
        reason: str = "Cancelled",
    ) -> bool:
        """
        Cancel job by execution ID.

        Args:
            execution_id: Execution to cancel
            reason: Cancellation reason

        Returns:
            True if found and cancelled
        """
        for worker in self._workers:
            if await worker.cancel_execution(execution_id, reason):
                return True
        return False


# Global worker pool instance
_worker_pool: Optional[WorkerPool] = None


def get_worker_pool() -> Optional[WorkerPool]:
    """Get the global worker pool instance."""
    return _worker_pool


async def start_worker_pool(config: Optional[WorkerPoolConfig] = None) -> WorkerPool:
    """
    Start the global worker pool.

    Args:
        config: Pool configuration

    Returns:
        Started WorkerPool instance
    """
    global _worker_pool

    if _worker_pool is not None and _worker_pool.is_running:
        logger.warning("Worker pool already started")
        return _worker_pool

    _worker_pool = WorkerPool(config)
    await _worker_pool.start()

    return _worker_pool


async def stop_worker_pool(timeout: float = 30.0) -> None:
    """
    Stop the global worker pool.

    Args:
        timeout: Maximum seconds to wait
    """
    global _worker_pool

    if _worker_pool is not None:
        await _worker_pool.stop(timeout=timeout)
        _worker_pool = None
