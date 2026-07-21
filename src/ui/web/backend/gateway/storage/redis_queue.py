"""
Redis Queue Implementation

Distributed job queue using Redis for high-availability deployments.
Uses Redis Streams for reliable message delivery with consumer groups.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from gateway.storage.queue_interface import QueueInterface, QueueJob, QueueStats

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


class RedisQueue(QueueInterface):
    """
    Redis-based job queue implementation.

    Uses:
    - Redis Streams for job queue with consumer groups
    - Sorted Sets for priority ordering
    - Hashes for job data storage
    - Sets for status tracking

    Keys:
    - flyto:queue:jobs:{job_id} - Job data hash
    - flyto:queue:pending - Sorted set of pending jobs (score=priority)
    - flyto:queue:running - Set of running job IDs
    - flyto:queue:leases - Hash of job_id -> lease_until
    - flyto:queue:stats - Queue statistics hash
    """

    KEY_PREFIX = "flyto:queue"

    def __init__(
        self,
        redis_url: Optional[str] = None,
        key_prefix: Optional[str] = None,
    ):
        """
        Initialize Redis queue.

        Args:
            redis_url: Redis connection URL (default: from REDIS_URL env)
            key_prefix: Key prefix for namespacing (default: flyto:queue)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.key_prefix = key_prefix or self.KEY_PREFIX
        self._redis = None
        self._initialized = False

    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                self._initialized = True
                logger.info(f"Connected to Redis: {self.redis_url}")
            except ImportError:
                raise ImportError(
                    "redis package required for Redis queue. "
                    "Install with: pip install redis"
                )
        return self._redis

    def _key(self, *parts: str) -> str:
        """Build a Redis key with prefix."""
        return f"{self.key_prefix}:{':'.join(parts)}"

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
    ) -> QueueJob:
        """Add a new job to the queue."""
        redis = await self._get_redis()
        job_id = str(uuid.uuid4())
        now = _utc_now()

        job = QueueJob(
            id=job_id,
            execution_id=execution_id,
            workflow_id=workflow_id,
            user_id=user_id,
            org_id=org_id,
            priority=priority,
            status="pending",
            attempts=0,
            max_attempts=max_attempts,
            timeout_ms=timeout_ms,
            visibility_timeout_ms=visibility_timeout_ms,
            created_at=now,
            metadata=metadata or {},
        )

        # Store job data
        job_key = self._key("jobs", job_id)
        await redis.hset(job_key, mapping={
            "id": job.id,
            "execution_id": job.execution_id,
            "workflow_id": job.workflow_id,
            "user_id": job.user_id or "",
            "org_id": job.org_id or "",
            "priority": str(job.priority),
            "status": job.status,
            "attempts": str(job.attempts),
            "max_attempts": str(job.max_attempts),
            "timeout_ms": str(job.timeout_ms),
            "visibility_timeout_ms": str(job.visibility_timeout_ms),
            "created_at": job.created_at,
            "metadata": json.dumps(job.metadata),
        })

        # Add to pending sorted set (score = priority, higher = more urgent)
        await redis.zadd(self._key("pending"), {job_id: priority})

        # Add to execution index
        await redis.set(self._key("exec", execution_id), job_id)

        # Update stats
        await redis.hincrby(self._key("stats"), "total", 1)
        await redis.hincrby(self._key("stats"), "pending", 1)

        logger.info(f"Job enqueued: {job_id} for execution {execution_id}")
        return job

    async def dequeue(
        self,
        worker_id: str,
        lease_duration_seconds: int = 300,
    ) -> Optional[QueueJob]:
        """Atomically dequeue and lock the highest priority pending job."""
        redis = await self._get_redis()
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        lease_until = (now + timedelta(seconds=lease_duration_seconds)).isoformat()

        # Use Lua script for atomic dequeue
        script = """
        local pending_key = KEYS[1]
        local running_key = KEYS[2]
        local leases_key = KEYS[3]
        local now_str = ARGV[1]
        local lease_until = ARGV[2]
        local worker_id = ARGV[3]

        -- Get highest priority job (highest score)
        local result = redis.call('ZREVRANGE', pending_key, 0, 0)
        if #result == 0 then
            return nil
        end

        local job_id = result[1]

        -- Move from pending to running
        redis.call('ZREM', pending_key, job_id)
        redis.call('SADD', running_key, job_id)

        -- Set lease
        redis.call('HSET', leases_key, job_id, lease_until)

        return job_id
        """

        try:
            job_id = await redis.eval(
                script,
                3,
                self._key("pending"),
                self._key("running"),
                self._key("leases"),
                now_str,
                lease_until,
                worker_id,
            )

            if not job_id:
                return None

            # Update job data
            job_key = self._key("jobs", job_id)
            await redis.hset(job_key, mapping={
                "status": "running",
                "locked_by": worker_id,
                "lease_until": lease_until,
                "heartbeat_at": now_str,
                "started_at": now_str,
            })
            await redis.hincrby(job_key, "attempts", 1)

            # Update stats
            await redis.hincrby(self._key("stats"), "pending", -1)
            await redis.hincrby(self._key("stats"), "running", 1)

            # Fetch full job data
            job_data = await redis.hgetall(job_key)
            job = self._data_to_job(job_data)

            logger.info(f"Job dequeued: {job_id} by worker {worker_id}")
            return job

        except Exception as e:
            logger.error(f"Error dequeuing job: {e}")
            raise

    async def ack(self, job_id: str, worker_id: str) -> bool:
        """Acknowledge successful job completion."""
        redis = await self._get_redis()
        now = _utc_now()

        # Verify ownership
        job_key = self._key("jobs", job_id)
        locked_by = await redis.hget(job_key, "locked_by")
        if locked_by != worker_id:
            logger.warning(f"Failed to ack job {job_id} - not owned by {worker_id}")
            return False

        # Update job
        await redis.hset(job_key, mapping={
            "status": "completed",
            "finished_at": now,
        })

        # Remove from running
        await redis.srem(self._key("running"), job_id)
        await redis.hdel(self._key("leases"), job_id)

        # Update stats
        await redis.hincrby(self._key("stats"), "running", -1)
        await redis.hincrby(self._key("stats"), "completed", 1)

        logger.info(f"Job acknowledged: {job_id}")
        return True

    async def nack(
        self,
        job_id: str,
        worker_id: str,
        error_message: Optional[str] = None,
        requeue: bool = True,
    ) -> bool:
        """Negative acknowledge - job failed."""
        redis = await self._get_redis()
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()

        # Verify ownership
        job_key = self._key("jobs", job_id)
        job_data = await redis.hgetall(job_key)
        if not job_data or job_data.get("locked_by") != worker_id:
            logger.warning(f"Failed to nack job {job_id} - not found or not owned")
            return False

        attempts = int(job_data.get("attempts", 0))
        max_attempts = int(job_data.get("max_attempts", 3))

        # Remove from running
        await redis.srem(self._key("running"), job_id)
        await redis.hdel(self._key("leases"), job_id)
        await redis.hincrby(self._key("stats"), "running", -1)

        if requeue and attempts < max_attempts:
            # Requeue with delay
            priority = int(job_data.get("priority", 0))

            await redis.hset(job_key, mapping={
                "status": "pending",
                "locked_by": "",
                "error_message": error_message or "",
            })

            # Re-add to pending (with lower priority after failure)
            await redis.zadd(
                self._key("pending"),
                {job_id: priority - 1},
            )
            await redis.hincrby(self._key("stats"), "pending", 1)

            logger.info(f"Job nacked and requeued: {job_id}")
        else:
            # Mark as failed
            await redis.hset(job_key, mapping={
                "status": "failed",
                "finished_at": now_str,
                "error_message": error_message or "",
            })
            await redis.hincrby(self._key("stats"), "failed", 1)

            logger.info(f"Job nacked and failed: {job_id}")

        return True

    async def heartbeat(
        self,
        job_id: str,
        worker_id: str,
        extend_seconds: int = 60,
    ) -> bool:
        """Update job heartbeat and extend lease."""
        redis = await self._get_redis()
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        new_lease = (now + timedelta(seconds=extend_seconds)).isoformat()

        job_key = self._key("jobs", job_id)
        locked_by = await redis.hget(job_key, "locked_by")

        if locked_by != worker_id:
            return False

        await redis.hset(job_key, mapping={
            "heartbeat_at": now_str,
            "lease_until": new_lease,
        })
        await redis.hset(self._key("leases"), job_id, new_lease)

        return True

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending or running job."""
        redis = await self._get_redis()
        now = _utc_now()

        job_key = self._key("jobs", job_id)
        status = await redis.hget(job_key, "status")

        if status not in ("pending", "running"):
            return False

        # Remove from appropriate set
        if status == "pending":
            await redis.zrem(self._key("pending"), job_id)
            await redis.hincrby(self._key("stats"), "pending", -1)
        else:
            await redis.srem(self._key("running"), job_id)
            await redis.hdel(self._key("leases"), job_id)
            await redis.hincrby(self._key("stats"), "running", -1)

        await redis.hset(job_key, mapping={
            "status": "cancelled",
            "finished_at": now,
        })
        await redis.hincrby(self._key("stats"), "cancelled", 1)

        logger.info(f"Job cancelled: {job_id}")
        return True

    async def cancel_by_execution_id(self, execution_id: str) -> bool:
        """Cancel job by execution ID."""
        redis = await self._get_redis()
        job_id = await redis.get(self._key("exec", execution_id))
        if not job_id:
            return False
        return await self.cancel(job_id)

    async def get_job(self, job_id: str) -> Optional[QueueJob]:
        """Get job by ID."""
        redis = await self._get_redis()
        job_data = await redis.hgetall(self._key("jobs", job_id))
        if not job_data:
            return None
        return self._data_to_job(job_data)

    async def get_by_execution_id(self, execution_id: str) -> Optional[QueueJob]:
        """Get job by execution ID."""
        redis = await self._get_redis()
        job_id = await redis.get(self._key("exec", execution_id))
        if not job_id:
            return None
        return await self.get_job(job_id)

    async def release_expired_leases(self) -> int:
        """Release jobs with expired leases."""
        redis = await self._get_redis()
        now = datetime.now(timezone.utc).isoformat()
        released = 0

        # Get all leases
        leases = await redis.hgetall(self._key("leases"))

        for job_id, lease_until in leases.items():
            if lease_until < now:
                # Lease expired - move back to pending
                job_key = self._key("jobs", job_id)
                job_data = await redis.hgetall(job_key)

                if job_data.get("status") == "running":
                    priority = int(job_data.get("priority", 0))

                    await redis.srem(self._key("running"), job_id)
                    await redis.hdel(self._key("leases"), job_id)
                    await redis.zadd(self._key("pending"), {job_id: priority})

                    await redis.hset(job_key, mapping={
                        "status": "pending",
                        "locked_by": "",
                    })

                    await redis.hincrby(self._key("stats"), "running", -1)
                    await redis.hincrby(self._key("stats"), "pending", 1)

                    released += 1
                    logger.info(f"Released expired lease for job: {job_id}")

        return released

    async def list_jobs(
        self,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[QueueJob]:
        """List jobs with optional filters."""
        redis = await self._get_redis()
        jobs = []

        # Get job IDs based on status
        if status == "pending":
            job_ids = await redis.zrevrange(self._key("pending"), offset, offset + limit - 1)
        elif status == "running":
            job_ids = list(await redis.smembers(self._key("running")))
            job_ids = job_ids[offset:offset + limit]
        else:
            # Scan all jobs (expensive but necessary for filtering)
            cursor = 0
            job_ids = []
            pattern = self._key("jobs", "*")

            while True:
                cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                for key in keys:
                    job_id = key.split(":")[-1]
                    job_ids.append(job_id)
                if cursor == 0:
                    break

            job_ids = job_ids[offset:offset + limit]

        # Fetch job data
        for job_id in job_ids:
            job_data = await redis.hgetall(self._key("jobs", job_id))
            if not job_data:
                continue

            # Apply filters
            if status and job_data.get("status") != status:
                continue
            if user_id and job_data.get("user_id") != user_id:
                continue
            if org_id and job_data.get("org_id") != org_id:
                continue

            jobs.append(self._data_to_job(job_data))

        return jobs[:limit]

    async def get_stats(self) -> QueueStats:
        """Get queue statistics."""
        redis = await self._get_redis()
        stats_data = await redis.hgetall(self._key("stats"))

        return QueueStats(
            total=int(stats_data.get("total", 0)),
            pending=int(stats_data.get("pending", 0)),
            running=int(stats_data.get("running", 0)),
            completed=int(stats_data.get("completed", 0)),
            failed=int(stats_data.get("failed", 0)),
            cancelled=int(stats_data.get("cancelled", 0)),
        )

    async def cleanup_old_jobs(self, days: int = 7) -> int:
        """Delete old completed/failed/cancelled jobs."""
        redis = await self._get_redis()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        deleted = 0

        # Scan all jobs
        cursor = 0
        pattern = self._key("jobs", "*")

        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)

            for key in keys:
                job_data = await redis.hgetall(key)
                status = job_data.get("status")
                finished_at = job_data.get("finished_at")

                if status in ("completed", "failed", "cancelled") and finished_at:
                    if finished_at < cutoff:
                        execution_id = job_data.get("execution_id")

                        # Delete job and index
                        await redis.delete(key)
                        if execution_id:
                            await redis.delete(self._key("exec", execution_id))

                        deleted += 1

            if cursor == 0:
                break

        if deleted > 0:
            logger.info(f"Deleted {deleted} old jobs")

        return deleted

    def _data_to_job(self, data: Dict[str, str]) -> QueueJob:
        """Convert Redis hash data to QueueJob."""
        metadata = {}
        if data.get("metadata"):
            try:
                metadata = json.loads(data["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass

        return QueueJob(
            id=data.get("id", ""),
            execution_id=data.get("execution_id", ""),
            workflow_id=data.get("workflow_id", ""),
            user_id=data.get("user_id") or None,
            org_id=data.get("org_id") or None,
            priority=int(data.get("priority", 0)),
            status=data.get("status", "pending"),
            attempts=int(data.get("attempts", 0)),
            max_attempts=int(data.get("max_attempts", 3)),
            timeout_ms=int(data.get("timeout_ms", 300000)),
            locked_by=data.get("locked_by") or None,
            lease_until=data.get("lease_until") or None,
            heartbeat_at=data.get("heartbeat_at") or None,
            visibility_timeout_ms=int(data.get("visibility_timeout_ms", 30000)),
            error_message=data.get("error_message") or None,
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            metadata=metadata,
        )

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")
