"""
Worker Job Processor

Job processing and workflow execution.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from services.cancellation_token import CancellationToken, CancelledException
from services.runtime.worker.config import WorkerConfig

logger = logging.getLogger(__name__)


def _get_queue():
    """Get queue instance and whether it is async."""
    try:
        from gateway.storage.queue_factory import get_queue
        return get_queue(), True
    except ImportError:
        from gateway.storage.job_queue import JobQueueRepository as queue
        return queue, False


async def _queue_ack(queue, is_async: bool, job_id: str, worker_id: str):
    """Acknowledge a job in the queue (async or sync)."""
    if is_async:
        await queue.ack(job_id, worker_id)
    else:
        queue.ack(job_id, worker_id)


async def _queue_nack(queue, is_async: bool, job_id: str, worker_id: str, reason: str, requeue: bool = False):
    """Negative-acknowledge a job in the queue (async or sync)."""
    if is_async:
        await queue.nack(job_id, worker_id, reason, requeue=requeue)
    else:
        queue.nack(job_id, worker_id, reason, requeue=requeue)


def _classify_error(e: Exception):
    """Classify error for retry behavior. Returns (should_requeue, error_category)."""
    try:
        from services.error_taxonomy import ErrorClassifier
        classified = ErrorClassifier.classify(e)
        logger.info(f"Error classified as {classified.category.value}, retryable={classified.retryable}")
        return classified.retryable, classified.category.value
    except Exception as classify_err:
        logger.warning(f"Failed to classify error: {classify_err}")
        return True, None


async def process_job(
    job_id: str,
    execution_id: str,
    token: CancellationToken,
    config: WorkerConfig,
    stats: Dict[str, Any],
) -> None:
    """
    Process a single job.

    Args:
        job_id: Job to process
        execution_id: Associated execution ID
        token: Cancellation token
        config: Worker configuration
        stats: Worker statistics dict (modified in place)
    """
    queue, is_async = _get_queue()
    from gateway.storage.execution_repo import ExecutionRepository

    logger.info(f"Processing job {job_id} (execution: {execution_id})")
    start_time = time.time()

    try:
        token.raise_if_cancelled()

        execution = ExecutionRepository.get_execution(execution_id, include_steps=False)
        if not execution:
            await _queue_nack(queue, is_async, job_id, config.worker_id, "Execution record not found")
            return

        ExecutionRepository.update_execution(execution_id=execution_id, status="running")

        result = await execute_workflow(
            execution_id=execution_id,
            workflow_id=execution.workflow_id,
            workflow_name=execution.workflow_name,
            workflow_snapshot=execution.workflow_snapshot,
            input_params=execution.input_params,
            token=token,
        )

        if token.is_cancelled:
            ExecutionRepository.update_execution(
                execution_id=execution_id, status="cancelled",
                error_message=token.reason, finished_at=datetime.now(timezone.utc).isoformat(),
            )
            await _queue_nack(queue, is_async, job_id, config.worker_id, token.reason)
            return

        duration_ms = int((time.time() - start_time) * 1000)
        ExecutionRepository.update_execution(
            execution_id=execution_id,
            status="success" if result.get("ok") else "failure",
            finished_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=duration_ms,
            result_data=result.get("data"),
            error_message=result.get("error"),
        )
        await _queue_ack(queue, is_async, job_id, config.worker_id)

        stats["jobs_processed"] += 1
        stats["jobs_succeeded"] += 1
        logger.info(f"Job {job_id} completed successfully (duration: {duration_ms}ms)")

    except CancelledException as e:
        logger.info(f"Job {job_id} cancelled: {e.reason}")
        ExecutionRepository.update_execution(
            execution_id=execution_id, status="cancelled",
            error_message=e.reason, finished_at=datetime.now(timezone.utc).isoformat(),
        )
        await _queue_nack(queue, is_async, job_id, config.worker_id, e.reason)

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        stats["jobs_processed"] += 1
        stats["jobs_failed"] += 1

        should_requeue, error_category = _classify_error(e)
        ExecutionRepository.update_execution(
            execution_id=execution_id, status="failure",
            error_message=str(e), error_category=error_category,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        await _queue_nack(queue, is_async, job_id, config.worker_id, str(e), requeue=should_requeue)


def _import_workflow_engine():
    """Import WorkflowEngine from the installed flyto-core package."""
    from core.engine.workflow_engine import WorkflowEngine
    return WorkflowEngine


async def _create_worker_step_hooks(execution_id: str):
    """Create step tracking hooks for worker execution. Returns hooks or None."""
    try:
        from services.step_tracking_hooks import StepTrackingHooks
        from gateway.storage.execution_repo import ExecutionRepository
        from services.runs_directory import get_runs_directory

        runs_dir = get_runs_directory()
        await runs_dir.create_run_directory(execution_id)
        return StepTrackingHooks(
            execution_id=execution_id,
            runs_directory=runs_dir,
            execution_repo=ExecutionRepository,
        )
    except Exception as e:
        logger.warning(f"Failed to create step tracking hooks: {e}")
        return None


def _create_engine(WorkflowEngine, workflow_data, input_params, step_hooks):
    """Create a WorkflowEngine instance, attaching hooks if supported."""
    import inspect
    sig = inspect.signature(WorkflowEngine.__init__)
    if step_hooks and "hooks" in sig.parameters:
        return WorkflowEngine(workflow_data, input_params, hooks=step_hooks)
    if step_hooks:
        logger.warning("WorkflowEngine does not support hooks, step tracking disabled")
    return WorkflowEngine(workflow_data, input_params)


async def execute_workflow(
    execution_id: str,
    workflow_id: str,
    workflow_name: str,
    workflow_snapshot: Optional[Dict[str, Any]],
    input_params: Optional[Dict[str, Any]],
    token: CancellationToken,
) -> Dict[str, Any]:
    """
    Execute a workflow.

    Args:
        execution_id: Execution ID
        workflow_id: Workflow ID
        workflow_name: Workflow name
        workflow_snapshot: Full workflow definition
        input_params: Runtime parameters
        token: Cancellation token

    Returns:
        Execution result dict
    """
    try:
        # Get workflow data from snapshot or reconstruct
        if workflow_snapshot:
            workflow_data = workflow_snapshot
        else:
            # Fallback: try to get from execution params
            return {
                "ok": False,
                "error": "No workflow snapshot available",
            }

        WorkflowEngine = _import_workflow_engine()

        step_hooks = await _create_worker_step_hooks(execution_id)

        engine = _create_engine(WorkflowEngine, workflow_data, input_params or {}, step_hooks)

        # Register cancellation
        def on_cancel():
            if hasattr(engine, "cancel"):
                engine.cancel()

        token.on_cancel(on_cancel)

        # Execute
        result = await engine.execute()

        return {
            "ok": True,
            "data": result,
        }

    except CancelledException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        return {
            "ok": False,
            "error": str(e),
        }
