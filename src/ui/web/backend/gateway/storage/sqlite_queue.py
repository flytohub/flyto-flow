"""
SQLite Queue Implementation

Wraps the existing JobQueueRepository to implement QueueInterface.
Used for single-instance deployments.
"""

import logging
from typing import Any, Dict, List, Optional

from gateway.storage.queue_interface import QueueInterface, QueueJob, QueueStats
from gateway.storage.job_queue import Job, JobQueueRepository

logger = logging.getLogger(__name__)


class SQLiteQueue(QueueInterface):
    """
    SQLite-based job queue implementation.

    Wraps JobQueueRepository to provide QueueInterface compatibility.
    Suitable for single-instance deployments.
    """

    def __init__(self):
        """Initialize SQLite queue."""
        self._repo = JobQueueRepository
        logger.info("SQLite queue initialized")

    async def enqueue(
        self,
        execution_id: str,
        workflow_id: str,
        workspace_id: Optional[str] = None,
        priority: int = 0,
        max_attempts: int = 3,
        timeout_ms: int = 300000,
        visibility_timeout_ms: int = 30000,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QueueJob:
        """Add a new job to the queue."""
        # SQLite repo is synchronous
        job = self._repo.enqueue(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            priority=priority,
            max_attempts=max_attempts,
            timeout_ms=timeout_ms,
            visibility_timeout_ms=visibility_timeout_ms,
        )

        return self._job_to_queue_job(job, metadata=metadata)

    async def dequeue(
        self,
        worker_id: str,
        lease_duration_seconds: int = 300,
    ) -> Optional[QueueJob]:
        """Atomically dequeue and lock the highest priority pending job."""
        job = self._repo.dequeue(
            worker_id=worker_id,
            lease_duration_seconds=lease_duration_seconds,
        )

        if not job:
            return None

        return self._job_to_queue_job(job)

    async def ack(self, job_id: str, worker_id: str) -> bool:
        """Acknowledge successful job completion."""
        return self._repo.ack(job_id, worker_id)

    async def nack(
        self,
        job_id: str,
        worker_id: str,
        error_message: Optional[str] = None,
        requeue: bool = True,
    ) -> bool:
        """Negative acknowledge - job failed."""
        return self._repo.nack(
            job_id=job_id,
            worker_id=worker_id,
            error_message=error_message,
            requeue=requeue,
        )

    async def heartbeat(
        self,
        job_id: str,
        worker_id: str,
        extend_seconds: int = 60,
    ) -> bool:
        """Update job heartbeat and extend lease."""
        return self._repo.heartbeat(
            job_id=job_id,
            worker_id=worker_id,
            extend_seconds=extend_seconds,
        )

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending or running job."""
        return self._repo.cancel(job_id)

    async def cancel_by_execution_id(self, execution_id: str) -> bool:
        """Cancel job by execution ID."""
        return self._repo.cancel_by_execution_id(execution_id)

    async def get_job(self, job_id: str) -> Optional[QueueJob]:
        """Get job by ID."""
        job = self._repo.get_job(job_id)
        if not job:
            return None
        return self._job_to_queue_job(job)

    async def get_by_execution_id(self, execution_id: str) -> Optional[QueueJob]:
        """Get job by execution ID."""
        job = self._repo.get_by_execution_id(execution_id)
        if not job:
            return None
        return self._job_to_queue_job(job)

    async def release_expired_leases(self) -> int:
        """Release jobs with expired leases."""
        return self._repo.release_expired_leases()

    async def list_jobs(
        self,
        status: Optional[str] = None,
        workspace_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[QueueJob]:
        """List jobs with optional filters."""
        jobs = self._repo.list_jobs(
            status=status,
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
        )
        return [self._job_to_queue_job(j) for j in jobs]

    async def get_stats(self) -> QueueStats:
        """Get queue statistics."""
        stats = self._repo.get_queue_stats()
        return QueueStats(
            total=stats.get("total", 0),
            pending=stats.get("pending", 0),
            running=stats.get("running", 0),
            completed=stats.get("completed", 0),
            failed=stats.get("failed", 0),
            cancelled=stats.get("cancelled", 0),
        )

    async def cleanup_old_jobs(self, days: int = 7) -> int:
        """Delete old completed/failed/cancelled jobs."""
        return self._repo.cleanup_old_jobs(days=days)

    def _job_to_queue_job(
        self,
        job: Job,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QueueJob:
        """Convert Job to QueueJob."""
        return QueueJob(
            id=job.id,
            execution_id=job.execution_id,
            workflow_id=job.workflow_id,
            workspace_id=job.workspace_id,
            priority=job.priority,
            status=job.status,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            timeout_ms=job.timeout_ms,
            locked_by=job.locked_by,
            lease_until=job.lease_until,
            heartbeat_at=job.heartbeat_at,
            visibility_timeout_ms=job.visibility_timeout_ms,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            metadata=metadata or {},
        )
