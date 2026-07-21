"""
Execution Job Repository

Provider-backed persistence facade for the execution job queue.
Collection details live inside the active data provider implementation.
"""

from typing import Any, List, Optional

from services.device.job_models import ExecutionJob, JobStatus

COLLECTION = "execution_jobs"


def create(job: ExecutionJob) -> ExecutionJob:
    """Write a new job."""
    return _device_provider().create_job(job)


def get(job_id: str) -> Optional[ExecutionJob]:
    """Read a single job."""
    return _device_provider().get_job(job_id)


def list_by_user(user_id: str, limit: int = 20) -> List[ExecutionJob]:
    """List recent jobs for a user, newest first."""
    return _device_provider().list_jobs_by_user(user_id, limit=limit)


def find_active_by_template_id(
    template_id: str,
    user_id: str,
) -> Optional[ExecutionJob]:
    """Return the most recent non-terminal job for (template_id, user_id)."""
    return _device_provider().find_active_job_by_template_id(template_id, user_id)


def poll_pending(device_id: str, limit: int = 1) -> List[ExecutionJob]:
    """Query pending jobs for a specific device."""
    return _device_provider().poll_pending_jobs(device_id, limit=limit)


def claim(job_id: str, device_id: str) -> bool:
    """Atomically transition PENDING -> CLAIMED."""
    return _device_provider().claim_job(job_id, device_id)


def update_progress(
    job_id: str,
    current_step_index: int,
    total_steps: int,
    current_node_id: Optional[str] = None,
    status: Optional[JobStatus] = None,
    step_id: Optional[str] = None,
    step_result: Optional[dict] = None,
) -> bool:
    """Update job progress (called by desktop device)."""
    return _device_provider().update_job_progress(
        job_id,
        current_step_index,
        total_steps,
        current_node_id=current_node_id,
        status=status,
        step_id=step_id,
        step_result=step_result,
    )


def complete(
    job_id: str,
    status: JobStatus,
    error: Optional[str] = None,
    variables: Optional[dict] = None,
    node_outputs: Optional[dict] = None,
) -> bool:
    """Mark job as completed (success/failed)."""
    return _device_provider().complete_job(
        job_id,
        status,
        error=error,
        variables=variables,
        node_outputs=node_outputs,
    )


def get_next_streaming_step(job_id: str, user_id: str) -> Optional[dict]:
    """
    Get the next step for a streaming job.

    Returns the step definition + accumulated context, or None if done.
    SECURITY: Only the job owner can request steps.
    """
    return _device_provider().get_next_streaming_step(job_id, user_id)


def save_streaming_step_result(
    job_id: str,
    user_id: str,
    step_id: str,
    step_index: int,
    result: Any,
    status: str = "success",
    error: Optional[str] = None,
) -> bool:
    """
    Save the result of a streaming step and advance the index.

    Stores the step result in streaming_context so the next step can reference
    it via ${steps.step_id.result}.
    """
    return _device_provider().save_streaming_step_result(
        job_id,
        user_id,
        step_id,
        step_index,
        result,
        status=status,
        error=error,
    )


def stream_pending_for_devices(device_ids: List[str]) -> List[dict]:
    """
    Query pending jobs across multiple devices.

    Returns raw job dicts suitable for SSE streaming.
    """
    return _device_provider().stream_pending_jobs_for_devices(device_ids)


def get_raw_template_steps(template_id: str) -> Optional[list]:
    """
    Read raw template steps for streaming mode.

    Returns None if the template does not exist.
    """
    return _device_provider().get_raw_template_steps(template_id)


def cancel(job_id: str, user_id: str) -> bool:
    """Cancel a job (only if still pending or running)."""
    return _device_provider().cancel_job(job_id, user_id)


def _device_provider():
    from gateway.providers.hub import get_data_provider

    return get_data_provider().devices
