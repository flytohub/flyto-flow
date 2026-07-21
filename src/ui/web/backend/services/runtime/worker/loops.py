"""
Worker Background Loops

Polling, heartbeat, and cleanup loops.
"""

import asyncio
import logging
from typing import Any, Callable, Dict

from services.cancellation_token import CancellationToken
from services.runtime.worker.config import WorkerConfig
from services.runtime.worker.processor import process_job
from services.runtime.worker.resources import check_resources

logger = logging.getLogger(__name__)


async def poll_loop(
    config: WorkerConfig,
    running_flag: Callable[[], bool],
    shutdown_event: asyncio.Event,
    current_jobs: Dict[str, asyncio.Task],
    cancellation_tokens: Dict[str, CancellationToken],
    stats: Dict[str, Any],
    on_job_done: Callable[[str], None],
) -> None:
    """
    Main loop for polling and processing jobs.

    Args:
        config: Worker configuration
        running_flag: Function to check if worker is running
        shutdown_event: Event signaling shutdown
        current_jobs: Dict of current job tasks
        cancellation_tokens: Dict of cancellation tokens
        stats: Worker statistics dict
        on_job_done: Callback when job completes
    """
    # Use queue factory to support both SQLite and Redis
    try:
        from gateway.storage.queue_factory import get_queue
        queue = get_queue()
        use_async_queue = True
    except ImportError:
        from gateway.storage.job_queue import JobQueueRepository
        queue = JobQueueRepository
        use_async_queue = False

    while running_flag():
        try:
            # Check if shutdown requested
            if shutdown_event.is_set():
                break

            # Check resource limits
            if not check_resources(config):
                await asyncio.sleep(config.poll_interval_seconds)
                continue

            # Check concurrent job limit
            if len(current_jobs) >= config.max_concurrent_jobs:
                await asyncio.sleep(config.poll_interval_seconds)
                continue

            # Try to dequeue a job
            if use_async_queue:
                job = await queue.dequeue(
                    worker_id=config.worker_id,
                    lease_duration_seconds=config.lease_duration_seconds,
                )
            else:
                job = queue.dequeue(
                    worker_id=config.worker_id,
                    lease_duration_seconds=config.lease_duration_seconds,
                )

            if job:
                # Start job processing
                token = CancellationToken()
                cancellation_tokens[job.id] = token

                task = asyncio.create_task(
                    process_job(job.id, job.execution_id, token, config, stats),
                    name=f"job-{job.id}",
                )
                current_jobs[job.id] = task

                # Register cleanup callback
                task.add_done_callback(
                    lambda t, jid=job.id: on_job_done(jid)
                )
            else:
                await asyncio.sleep(config.poll_interval_seconds)

        except Exception as e:
            logger.error(f"Error in poll loop: {e}")
            await asyncio.sleep(config.poll_interval_seconds)


async def heartbeat_loop(
    config: WorkerConfig,
    running_flag: Callable[[], bool],
    shutdown_event: asyncio.Event,
    current_jobs: Dict[str, asyncio.Task],
) -> None:
    """
    Send heartbeats for all active jobs.

    Args:
        config: Worker configuration
        running_flag: Function to check if worker is running
        shutdown_event: Event signaling shutdown
        current_jobs: Dict of current job tasks
    """
    # Use queue factory to support both SQLite and Redis
    try:
        from gateway.storage.queue_factory import get_queue
        queue = get_queue()
        use_async_queue = True
    except ImportError:
        from gateway.storage.job_queue import JobQueueRepository as queue
        use_async_queue = False

    while running_flag():
        try:
            await asyncio.sleep(config.heartbeat_interval_seconds)

            if not current_jobs or shutdown_event.is_set():
                continue

            # Send heartbeat for each active job
            for job_id in list(current_jobs.keys()):
                try:
                    if use_async_queue:
                        await queue.heartbeat(
                            job_id,
                            config.worker_id,
                            extend_seconds=config.lease_duration_seconds,
                        )
                    else:
                        queue.heartbeat(
                            job_id,
                            config.worker_id,
                            extend_seconds=config.lease_duration_seconds,
                        )
                except Exception as e:
                    logger.warning(f"Failed to send heartbeat for {job_id}: {e}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")


async def cleanup_loop(
    config: WorkerConfig,
    running_flag: Callable[[], bool],
    shutdown_event: asyncio.Event,
) -> None:
    """
    Periodically release expired leases (cleanup crashed workers).

    Args:
        config: Worker configuration
        running_flag: Function to check if worker is running
        shutdown_event: Event signaling shutdown
    """
    # Use queue factory to support both SQLite and Redis
    try:
        from gateway.storage.queue_factory import get_queue
        queue = get_queue()
        use_async_queue = True
    except ImportError:
        from gateway.storage.job_queue import JobQueueRepository as queue
        use_async_queue = False

    while running_flag():
        try:
            # Check less frequently than heartbeat
            await asyncio.sleep(60)

            if shutdown_event.is_set():
                break

            # Release expired leases
            if use_async_queue:
                await queue.release_expired_leases()
            else:
                queue.release_expired_leases()

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in cleanup loop: {e}")
