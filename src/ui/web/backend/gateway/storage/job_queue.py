"""
Job Queue Repository

SQLite-based job queue with lease management for worker coordination.
Implements atomic enqueue/dequeue/ack/nack operations.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from gateway.storage.database import get_cursor, get_db

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    """Get current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def _parse_timestamp(ts: Optional[str]) -> Optional[datetime]:
    """Parse ISO timestamp string to datetime."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


@dataclass
class Job:
    """Job queue entry for workflow execution."""

    id: str
    execution_id: str
    workflow_id: str
    workspace_id: Optional[str] = None

    priority: int = 0
    status: str = "pending"

    attempts: int = 0
    max_attempts: int = 3
    timeout_ms: int = 0

    locked_by: Optional[str] = None
    lease_until: Optional[str] = None
    heartbeat_at: Optional[str] = None

    visibility_timeout_ms: int = 30000

    error_message: Optional[str] = None

    created_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "workspace_id": self.workspace_id,
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
        }

    @classmethod
    def from_row(cls, row) -> "Job":
        """Create from SQLite row."""
        return cls(
            id=row["id"],
            execution_id=row["execution_id"],
            workflow_id=row["workflow_id"],
            workspace_id=row["workspace_id"],
            priority=row["priority"] or 0,
            status=row["status"] or "pending",
            attempts=row["attempts"] or 0,
            max_attempts=row["max_attempts"] or 3,
            timeout_ms=row["timeout_ms"] or 0,
            locked_by=row["locked_by"],
            lease_until=row["lease_until"],
            heartbeat_at=row["heartbeat_at"],
            visibility_timeout_ms=row["visibility_timeout_ms"] or 30000,
            error_message=row["error_message"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
        )


class JobQueueRepository:
    """Repository for job queue operations with lease management."""

    @staticmethod
    def enqueue(
        execution_id: str,
        workflow_id: str,
        workspace_id: Optional[str] = None,
        priority: int = 0,
        max_attempts: int = 3,
        timeout_ms: int = 0,
        visibility_timeout_ms: int = 30000,
    ) -> Job:
        """
        Add a new job to the queue.

        Args:
            execution_id: Link to execution record
            workflow_id: Workflow being executed
            workspace_id: Workspace that triggered execution
            priority: Job priority (higher = more urgent)
            max_attempts: Maximum retry attempts
            timeout_ms: Execution timeout (0 = no limit)
            visibility_timeout_ms: Delay before retry after failure

        Returns:
            Created Job instance
        """
        job_id = str(uuid.uuid4())
        now = _utc_now()

        with get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO jobs (
                    id, execution_id, workflow_id, workspace_id,
                    priority, status, attempts, max_attempts,
                    timeout_ms, visibility_timeout_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    execution_id,
                    workflow_id,
                    workspace_id,
                    priority,
                    "pending",
                    0,
                    max_attempts,
                    timeout_ms,
                    visibility_timeout_ms,
                    now,
                ),
            )

        logger.info(f"Job enqueued: {job_id} for execution {execution_id}")

        return Job(
            id=job_id,
            execution_id=execution_id,
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            priority=priority,
            status="pending",
            attempts=0,
            max_attempts=max_attempts,
            timeout_ms=timeout_ms,
            visibility_timeout_ms=visibility_timeout_ms,
            created_at=now,
        )

    @staticmethod
    def dequeue(
        worker_id: str,
        lease_duration_seconds: int = 300,
    ) -> Optional[Job]:
        """
        Atomically dequeue and lock the highest priority pending job.

        Uses BEGIN IMMEDIATE for atomic read-modify-write in SQLite.

        Args:
            worker_id: Identifier of the worker claiming the job
            lease_duration_seconds: How long the worker has to complete

        Returns:
            Locked Job if available, None otherwise
        """
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        lease_until = (now + timedelta(seconds=lease_duration_seconds)).isoformat()

        db = get_db()

        try:
            # Use BEGIN IMMEDIATE for write lock
            db.execute("BEGIN IMMEDIATE")

            cursor = db.cursor()

            # Find pending jobs or jobs with expired leases
            cursor.execute(
                """
                SELECT * FROM jobs
                WHERE status = 'pending'
                   OR (status = 'running' AND lease_until < ?)
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
                """,
                (now_str,),
            )

            row = cursor.fetchone()

            if not row:
                db.rollback()
                cursor.close()
                return None

            job = Job.from_row(row)

            # Lock the job
            cursor.execute(
                """
                UPDATE jobs
                SET status = 'running',
                    locked_by = ?,
                    lease_until = ?,
                    heartbeat_at = ?,
                    attempts = attempts + 1,
                    started_at = COALESCE(started_at, ?)
                WHERE id = ?
                """,
                (worker_id, lease_until, now_str, now_str, job.id),
            )

            db.commit()
            cursor.close()

            # Update local job object
            job.status = "running"
            job.locked_by = worker_id
            job.lease_until = lease_until
            job.heartbeat_at = now_str
            job.attempts += 1
            job.started_at = job.started_at or now_str

            logger.info(f"Job dequeued: {job.id} by worker {worker_id}")
            return job

        except Exception as e:
            db.rollback()
            logger.error(f"Error dequeuing job: {e}")
            raise

    @staticmethod
    def ack(job_id: str, worker_id: str) -> bool:
        """
        Acknowledge successful job completion.

        Args:
            job_id: Job to acknowledge
            worker_id: Worker that processed the job

        Returns:
            True if acknowledged, False if not found or not owned
        """
        now = _utc_now()

        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET status = 'completed',
                    finished_at = ?
                WHERE id = ? AND locked_by = ?
                """,
                (now, job_id, worker_id),
            )
            acknowledged = cursor.rowcount > 0

        if acknowledged:
            logger.info(f"Job acknowledged: {job_id}")
        else:
            logger.warning(f"Failed to ack job {job_id} - not owned by {worker_id}")

        return acknowledged

    @staticmethod
    def nack(
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
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()

        with get_cursor() as cursor:
            # Get the job first to check attempts
            cursor.execute(
                "SELECT * FROM jobs WHERE id = ? AND locked_by = ?",
                (job_id, worker_id),
            )
            row = cursor.fetchone()

            if not row:
                logger.warning(f"Failed to nack job {job_id} - not found or not owned")
                return False

            job = Job.from_row(row)

            if requeue and job.attempts < job.max_attempts:
                # Requeue with visibility timeout
                visibility_until = (
                    now + timedelta(milliseconds=job.visibility_timeout_ms)
                ).isoformat()

                cursor.execute(
                    """
                    UPDATE jobs
                    SET status = 'pending',
                        locked_by = NULL,
                        lease_until = ?,
                        error_message = ?
                    WHERE id = ?
                    """,
                    (visibility_until, error_message, job_id),
                )
                new_status = "pending"
            else:
                # Max attempts reached or no requeue
                cursor.execute(
                    """
                    UPDATE jobs
                    SET status = 'failed',
                        finished_at = ?,
                        error_message = ?
                    WHERE id = ?
                    """,
                    (now_str, error_message, job_id),
                )
                new_status = "failed"

        logger.info(f"Job nacked: {job_id}, status={new_status}")
        return True

    @staticmethod
    def heartbeat(
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
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        new_lease = (now + timedelta(seconds=extend_seconds)).isoformat()

        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET heartbeat_at = ?,
                    lease_until = ?
                WHERE id = ? AND locked_by = ? AND status = 'running'
                """,
                (now_str, new_lease, job_id, worker_id),
            )
            updated = cursor.rowcount > 0

        return updated

    @staticmethod
    def cancel(job_id: str) -> bool:
        """
        Cancel a pending or running job.

        Args:
            job_id: Job to cancel

        Returns:
            True if cancelled
        """
        now = _utc_now()

        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET status = 'cancelled',
                    finished_at = ?
                WHERE id = ? AND status IN ('pending', 'running')
                """,
                (now, job_id),
            )
            cancelled = cursor.rowcount > 0

        if cancelled:
            logger.info(f"Job cancelled: {job_id}")
        return cancelled

    @staticmethod
    def cancel_by_execution_id(execution_id: str) -> bool:
        """
        Cancel job by execution ID.

        Args:
            execution_id: Execution ID to cancel

        Returns:
            True if cancelled
        """
        now = _utc_now()

        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET status = 'cancelled',
                    finished_at = ?
                WHERE execution_id = ? AND status IN ('pending', 'running')
                """,
                (now, execution_id),
            )
            cancelled = cursor.rowcount > 0

        if cancelled:
            logger.info(f"Job cancelled for execution: {execution_id}")
        return cancelled

    @staticmethod
    def get_job(job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return Job.from_row(row)

    @staticmethod
    def get_by_execution_id(execution_id: str) -> Optional[Job]:
        """Get job by execution ID."""
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM jobs WHERE execution_id = ?",
                (execution_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return Job.from_row(row)

    @staticmethod
    def release_expired_leases() -> int:
        """
        Release jobs with expired leases (crashed workers).

        Returns:
            Number of jobs released
        """
        now = _utc_now()

        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET status = 'pending',
                    locked_by = NULL
                WHERE status = 'running' AND lease_until < ?
                """,
                (now,),
            )
            released = cursor.rowcount

        if released > 0:
            logger.info(f"Released {released} expired job leases")

        return released

    @staticmethod
    def list_jobs(
        status: Optional[str] = None,
        workspace_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Job]:
        """
        List jobs with optional filters.

        Args:
            status: Filter by status
            workspace_id: Filter by workspace
            limit: Maximum results
            offset: Skip first N results

        Returns:
            List of Job objects
        """
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status)

        if workspace_id:
            conditions.append("workspace_id = ?")
            params.append(workspace_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        params.extend([limit, offset])

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM jobs
                {where_clause}
                ORDER BY priority DESC, created_at ASC
                LIMIT ? OFFSET ?
                """,
                params,
            )
            return [Job.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def get_queue_stats() -> Dict[str, Any]:
        """Get queue statistics."""
        with get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
                FROM jobs
                """
            )
            row = cursor.fetchone()

            return {
                "total": row["total"] or 0,
                "pending": row["pending"] or 0,
                "running": row["running"] or 0,
                "completed": row["completed"] or 0,
                "failed": row["failed"] or 0,
                "cancelled": row["cancelled"] or 0,
            }

    @staticmethod
    def cleanup_old_jobs(days: int = 7) -> int:
        """
        Delete completed/failed/cancelled jobs older than specified days.

        Args:
            days: Delete jobs older than this

        Returns:
            Number of deleted jobs
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        with get_cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM jobs
                WHERE status IN ('completed', 'failed', 'cancelled')
                  AND finished_at < ?
                """,
                (cutoff,),
            )
            deleted = cursor.rowcount

        if deleted > 0:
            logger.info(f"Deleted {deleted} old jobs")

        return deleted
