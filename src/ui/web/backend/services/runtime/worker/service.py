"""
Worker Service

Main Worker class for consuming and processing jobs.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from services.cancellation_token import CancellationToken
from services.runtime.worker.config import WorkerConfig
from services.runtime.worker.loops import cleanup_loop, heartbeat_loop, poll_loop

logger = logging.getLogger(__name__)


class Worker:
    """
    Job queue worker.

    Polls for jobs from the queue, executes workflows, and manages heartbeats.
    Supports graceful shutdown and resource limits.

    Usage:
        config = WorkerConfig(max_concurrent_jobs=2)
        worker = Worker(config)

        # Start worker (runs until stopped)
        await worker.start()

        # Stop worker gracefully
        await worker.stop()
    """

    def __init__(self, config: Optional[WorkerConfig] = None):
        """
        Initialize worker.

        Args:
            config: Worker configuration
        """
        self.config = config or WorkerConfig()
        self._running = False
        self._current_jobs: Dict[str, asyncio.Task] = {}
        self._cancellation_tokens: Dict[str, CancellationToken] = {}
        self._shutdown_event = asyncio.Event()
        self._stats = {
            "jobs_processed": 0,
            "jobs_succeeded": 0,
            "jobs_failed": 0,
            "started_at": None,
        }

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running

    @property
    def active_job_count(self) -> int:
        """Get number of currently processing jobs."""
        return len(self._current_jobs)

    @property
    def stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        return self._stats.copy()

    async def start(self) -> None:
        """
        Start the worker loop.

        Runs until stop() is called or an unrecoverable error occurs.
        """
        if self._running:
            logger.warning(f"Worker {self.config.worker_id} already running")
            return

        self._running = True
        self._stats["started_at"] = datetime.now(timezone.utc).isoformat()
        self._shutdown_event.clear()

        logger.info(f"Worker {self.config.worker_id} starting...")

        # Start background tasks
        tasks = [
            asyncio.create_task(
                poll_loop(
                    self.config,
                    lambda: self._running,
                    self._shutdown_event,
                    self._current_jobs,
                    self._cancellation_tokens,
                    self._stats,
                    self._on_job_done,
                ),
                name="poll_loop"
            ),
            asyncio.create_task(
                heartbeat_loop(
                    self.config,
                    lambda: self._running,
                    self._shutdown_event,
                    self._current_jobs,
                ),
                name="heartbeat_loop"
            ),
            asyncio.create_task(
                cleanup_loop(
                    self.config,
                    lambda: self._running,
                    self._shutdown_event,
                ),
                name="cleanup_loop"
            ),
        ]

        try:
            # Wait for shutdown or error
            await self._shutdown_event.wait()

            # Cancel background tasks
            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)

        except asyncio.CancelledError:
            logger.info(f"Worker {self.config.worker_id} cancelled")
        finally:
            self._running = False
            logger.info(f"Worker {self.config.worker_id} stopped")

    async def stop(self, timeout: float = 30.0) -> None:
        """
        Gracefully stop the worker.

        Args:
            timeout: Maximum seconds to wait for current jobs
        """
        if not self._running:
            return

        logger.info(f"Worker {self.config.worker_id} stopping...")

        # Request cancellation for all current jobs
        for job_id, token in list(self._cancellation_tokens.items()):
            token.cancel("Worker shutdown")

        # Wait for current jobs to finish
        if self._current_jobs:
            logger.info(
                f"Waiting for {len(self._current_jobs)} jobs to complete..."
            )
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        *self._current_jobs.values(),
                        return_exceptions=True,
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for jobs, forcing shutdown")

        # Signal shutdown
        self._shutdown_event.set()

    def _on_job_done(self, job_id: str) -> None:
        """Callback when job task completes."""
        self._current_jobs.pop(job_id, None)
        self._cancellation_tokens.pop(job_id, None)

    async def cancel_job(self, job_id: str, reason: str = "Cancelled") -> bool:
        """
        Cancel a specific job.

        Args:
            job_id: Job to cancel
            reason: Cancellation reason

        Returns:
            True if job was being processed and cancelled
        """
        token = self._cancellation_tokens.get(job_id)
        if token:
            token.cancel(reason)
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
        from gateway.storage.queue_factory import get_queue

        job = await get_queue().get_by_execution_id(execution_id)
        if job and job.id in self._cancellation_tokens:
            return await self.cancel_job(job.id, reason)
        return False
