"""
Queue Interface

Abstract interface for job queue implementations.
Allows swapping between SQLite (single instance) and Redis (distributed).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class QueueJob:
    """
    Job representation for queue operations.

    This is the interface-level job format, independent of storage backend.
    """
    id: str
    execution_id: str
    workflow_id: str
    user_id: Optional[str] = None
    org_id: Optional[str] = None

    priority: int = 0
    status: str = "pending"

    attempts: int = 0
    max_attempts: int = 3
    timeout_ms: int = 300000  # 5 minutes default

    locked_by: Optional[str] = None
    lease_until: Optional[str] = None
    heartbeat_at: Optional[str] = None

    visibility_timeout_ms: int = 30000

    error_message: Optional[str] = None

    created_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    # RACE-2: Idempotency key to prevent duplicate job execution
    # If set, queue will reject jobs with duplicate idempotency_key
    idempotency_key: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "user_id": self.user_id,
            "org_id": self.org_id,
            "priority": self.priority,
            "status": self.status,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "timeout_ms": self.timeout_ms,
            "locked_by": self.locked_by,
            "lease_until": self.lease_until,
            "heartbeat_at": self.heartbeat_at,
            "visibility_timeout_ms": self.visibility_timeout_ms,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "idempotency_key": self.idempotency_key,
            "metadata": self.metadata,
        }


@dataclass
class QueueStats:
    """Queue statistics."""
    total: int = 0
    pending: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "total": self.total,
            "pending": self.pending,
            "running": self.running,
            "completed": self.completed,
            "failed": self.failed,
            "cancelled": self.cancelled,
        }


class QueueInterface(ABC):
    """
    Abstract interface for job queue implementations.

    Implementations:
    - SQLiteQueue: Single-instance, file-based (default)
    - RedisQueue: Distributed, high-performance

    All methods are async to support both sync and async backends.
    """

    @abstractmethod
    async def enqueue(
        self,
        execution_id: str,
        workflow_id: str,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        priority: int = 0,
        max_attempts: int = 3,
        timeout_ms: int = 300000,
        visibility_timeout_ms: int = 30000,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> QueueJob:
        """
        Add a new job to the queue.

        Args:
            execution_id: Link to execution record
            workflow_id: Workflow being executed
            user_id: User who triggered execution
            org_id: Organization ID
            priority: Job priority (higher = more urgent)
            max_attempts: Maximum retry attempts
            timeout_ms: Execution timeout
            visibility_timeout_ms: Delay before retry after failure
            metadata: Additional job metadata
            idempotency_key: Optional key to prevent duplicate jobs (RACE-2)
                            If provided and a pending/running job with same key exists,
                            returns existing job instead of creating new one

        Returns:
            Created QueueJob instance (or existing one if idempotency_key matches)
        """
        pass

    @abstractmethod
    async def dequeue(
        self,
        worker_id: str,
        lease_duration_seconds: int = 300,
    ) -> Optional[QueueJob]:
        """
        Atomically dequeue and lock the highest priority pending job.

        Args:
            worker_id: Identifier of the worker claiming the job
            lease_duration_seconds: How long the worker has to complete

        Returns:
            Locked QueueJob if available, None otherwise
        """
        pass

    @abstractmethod
    async def ack(self, job_id: str, worker_id: str) -> bool:
        """
        Acknowledge successful job completion.

        Args:
            job_id: Job to acknowledge
            worker_id: Worker that processed the job

        Returns:
            True if acknowledged, False if not found or not owned
        """
        pass

    @abstractmethod
    async def nack(
        self,
        job_id: str,
        worker_id: str,
        error_message: Optional[str] = None,
        requeue: bool = True,
    ) -> bool:
        """
        Negative acknowledge - job failed.

        Args:
            job_id: Job that failed
            worker_id: Worker that processed the job
            error_message: Error description
            requeue: Whether to requeue for retry

        Returns:
            True if nacked, False if not found or not owned
        """
        pass

    @abstractmethod
    async def heartbeat(
        self,
        job_id: str,
        worker_id: str,
        extend_seconds: int = 60,
    ) -> bool:
        """
        Update job heartbeat and extend lease.

        Args:
            job_id: Job to update
            worker_id: Worker owning the job
            extend_seconds: How much to extend the lease

        Returns:
            True if heartbeat updated, False if job not owned
        """
        pass

    @abstractmethod
    async def cancel(self, job_id: str) -> bool:
        """
        Cancel a pending or running job.

        Args:
            job_id: Job to cancel

        Returns:
            True if cancelled
        """
        pass

    @abstractmethod
    async def cancel_by_execution_id(self, execution_id: str) -> bool:
        """
        Cancel job by execution ID.

        Args:
            execution_id: Execution ID to cancel

        Returns:
            True if cancelled
        """
        pass

    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[QueueJob]:
        """Get job by ID."""
        pass

    @abstractmethod
    async def get_by_execution_id(self, execution_id: str) -> Optional[QueueJob]:
        """Get job by execution ID."""
        pass

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[QueueJob]:
        """
        Get pending/running job by idempotency key (RACE-2).

        Args:
            idempotency_key: The idempotency key to search for

        Returns:
            QueueJob if found with status pending/running, None otherwise
        """
        pass

    @abstractmethod
    async def release_expired_leases(self) -> int:
        """
        Release jobs with expired leases (crashed workers).

        Returns:
            Number of jobs released
        """
        pass

    @abstractmethod
    async def list_jobs(
        self,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[QueueJob]:
        """
        List jobs with optional filters.

        Args:
            status: Filter by status
            user_id: Filter by user
            org_id: Filter by organization
            limit: Maximum results
            offset: Skip first N results

        Returns:
            List of QueueJob objects
        """
        pass

    @abstractmethod
    async def get_stats(self) -> QueueStats:
        """Get queue statistics."""
        pass

    @abstractmethod
    async def cleanup_old_jobs(self, days: int = 7) -> int:
        """
        Delete completed/failed/cancelled jobs older than specified days.

        Args:
            days: Delete jobs older than this

        Returns:
            Number of deleted jobs
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        Check queue health.

        Returns:
            Health status dict
        """
        try:
            stats = await self.get_stats()
            return {
                "healthy": True,
                "stats": stats.to_dict(),
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }
