"""
Execution Control Routes

Pause, resume, step, and state endpoints for execution debugging.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from api.executions.auth import get_optional_user
from api.executions.models import (
    PauseResponse,
    ResumeResponse,
    StepResponse,
    RunToEndResponse,
    ExecutionStateResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def safe_serialize(obj: Any) -> Any:
    """
    Filter out non-serializable objects like BrowserDriver.

    Args:
        obj: Object to serialize

    Returns:
        JSON-serializable version of the object
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe_serialize(item) for item in obj]
    # For non-serializable objects, return type name
    try:
        import json
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return f"<{type(obj).__name__}>"


@router.post("/{execution_id}/pause", response_model=PauseResponse)
async def pause_execution(
    execution_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Pause a running workflow execution.

    The execution will pause at the next safe checkpoint.
    """
    from services.runtime.execution_manager import get_execution_manager, ExecutionStatus
    from services.runtime.execution_control import get_controller, PauseReason

    manager = get_execution_manager()
    controller = get_controller()

    # Verify execution exists
    status = manager.get_status(execution_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    # Check ownership
    user_id = current_user.get("id") if current_user else None
    exec_user_id = status.get("user_id")

    if user_id and exec_user_id and user_id != exec_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot pause execution owned by another user"
        )

    # Check if execution is running
    exec_status = status.get("status")
    if exec_status != ExecutionStatus.RUNNING.value:
        return PauseResponse(
            ok=False,
            message=f"Cannot pause execution in status: {exec_status}"
        )

    # Register and request pause
    if not controller.is_registered(execution_id):
        controller.register_execution(execution_id)

    success = await controller.request_pause(execution_id, PauseReason.USER_REQUEST)

    if success:
        return PauseResponse(
            ok=True,
            message=f"Pause requested for execution {execution_id}"
        )
    else:
        return PauseResponse(
            ok=False,
            message=f"Failed to pause execution {execution_id}"
        )


@router.post("/{execution_id}/resume", response_model=ResumeResponse)
async def resume_execution(
    execution_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Resume a paused workflow execution.
    """
    from services.runtime.execution_manager import get_execution_manager, ExecutionStatus
    from services.runtime.execution_control import get_controller

    manager = get_execution_manager()
    controller = get_controller()

    # Verify execution exists
    status = manager.get_status(execution_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    # Check ownership
    user_id = current_user.get("id") if current_user else None
    exec_user_id = status.get("user_id")

    if user_id and exec_user_id and user_id != exec_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot resume execution owned by another user"
        )

    # Check if execution is paused (check both manager and controller state)
    exec_status = status.get("status")
    controller_state = controller.get_state(execution_id)
    controller_status = controller_state.status if controller_state else None

    # Allow resume if either manager or controller shows paused
    is_paused = (
        exec_status == ExecutionStatus.PAUSED.value or
        controller_status == "paused"
    )

    if not is_paused:
        return ResumeResponse(
            ok=False,
            message=f"Cannot resume execution in status: {exec_status} (controller: {controller_status})"
        )

    success = await controller.request_resume(execution_id)

    if success:
        return ResumeResponse(
            ok=True,
            message=f"Execution {execution_id} resumed"
        )
    else:
        return ResumeResponse(
            ok=False,
            message=f"Failed to resume execution {execution_id}"
        )


@router.post("/{execution_id}/step", response_model=StepResponse)
async def step_execution(
    execution_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Execute a single step and pause again.

    Only works when execution is paused.
    """
    from services.runtime.execution_manager import get_execution_manager, ExecutionStatus
    from services.runtime.execution_control import get_controller

    manager = get_execution_manager()
    controller = get_controller()

    # Verify execution exists
    status = manager.get_status(execution_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    # Check ownership
    user_id = current_user.get("id") if current_user else None
    exec_user_id = status.get("user_id")

    if user_id and exec_user_id and user_id != exec_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot step execution owned by another user"
        )

    # Check if execution is paused
    exec_status = status.get("status")
    if exec_status != ExecutionStatus.PAUSED.value:
        return StepResponse(
            ok=False,
            message=f"Cannot step execution in status: {exec_status}"
        )

    success = await controller.request_step(execution_id)

    if success:
        return StepResponse(
            ok=True,
            message=f"Stepping execution {execution_id}"
        )
    else:
        return StepResponse(
            ok=False,
            message=f"Failed to step execution {execution_id}"
        )


@router.post("/{execution_id}/run-to-end", response_model=RunToEndResponse)
async def run_to_end(
    execution_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Resume a paused execution and ignore all breakpoints.

    Runs to completion without stopping at any human checkpoints.
    """
    from services.runtime.execution_manager import get_execution_manager, ExecutionStatus
    from services.runtime.execution_control import get_controller

    manager = get_execution_manager()
    controller = get_controller()

    # Verify execution exists
    status = manager.get_status(execution_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    # Check ownership
    user_id = current_user.get("id") if current_user else None
    exec_user_id = status.get("user_id")

    if user_id and exec_user_id and user_id != exec_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot control execution owned by another user"
        )

    # Check if execution is paused
    exec_status = status.get("status")
    controller_state = controller.get_state(execution_id)
    controller_status = controller_state.status if controller_state else None

    is_paused = (
        exec_status == ExecutionStatus.PAUSED.value or
        controller_status == "paused"
    )

    if not is_paused:
        return RunToEndResponse(
            ok=False,
            message=f"Cannot run-to-end in status: {exec_status}"
        )

    success = await controller.run_to_end(execution_id)

    if success:
        return RunToEndResponse(
            ok=True,
            message=f"Execution {execution_id} running to completion"
        )
    else:
        return RunToEndResponse(
            ok=False,
            message=f"Failed to run-to-end execution {execution_id}"
        )


@router.get("/{execution_id}/state", response_model=ExecutionStateResponse)
async def get_execution_state(
    execution_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get detailed state of a paused or running execution.

    Returns current variables, node outputs, and control state.
    """
    from services.runtime.execution_manager import get_execution_manager, ExecutionStatus
    from services.runtime.execution_control import get_controller

    manager = get_execution_manager()
    controller = get_controller()

    # Verify execution exists
    status = manager.get_status(execution_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    # Check ownership
    user_id = current_user.get("id") if current_user else None
    exec_user_id = status.get("user_id")

    if user_id and exec_user_id and user_id != exec_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot view state of execution owned by another user"
        )

    # Get state from controller if registered
    state = controller.get_state(execution_id)

    if state:
        return ExecutionStateResponse(
            ok=True,
            execution_id=state.execution_id,
            status=state.status,
            current_node_id=state.current_node_id,
            current_step_index=state.current_step_index,
            total_steps=state.total_steps,
            paused_at=state.paused_at,
            pause_reason=state.pause_reason,
            variables=safe_serialize(state.variables),
            node_outputs=safe_serialize(state.node_outputs),
            can_resume=state.can_resume,
            can_step=state.can_step,
            error_message=state.error_message
        )
    else:
        # Return state from execution manager (includes node outputs for completed executions)
        return ExecutionStateResponse(
            ok=True,
            execution_id=execution_id,
            status=status.get("status", "unknown"),
            current_node_id=status.get("active_node_id"),
            current_step_index=status.get("current_step", 0),
            total_steps=status.get("total_steps", 0),
            node_outputs=safe_serialize(status.get("node_outputs", {})),
            can_resume=status.get("status") == ExecutionStatus.PAUSED.value,
            can_step=status.get("status") == ExecutionStatus.PAUSED.value
        )


@router.post("/{execution_id}/continue-checkpoint")
async def continue_checkpoint(
    execution_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Continue execution from a human checkpoint.

    When workflow hits a human checkpoint, this endpoint
    resumes execution with any provided modifications.
    """
    from services.runtime.execution_manager import get_execution_manager, ExecutionStatus
    from services.runtime.execution_control import get_controller

    manager = get_execution_manager()
    controller = get_controller()

    # Verify execution exists
    status = manager.get_status(execution_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    # Check ownership
    user_id = current_user.get("id") if current_user else None
    exec_user_id = status.get("user_id")

    if user_id and exec_user_id and user_id != exec_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot continue execution owned by another user"
        )

    # Check if execution is paused (at checkpoint)
    exec_status = status.get("status")
    controller_state = controller.get_state(execution_id)
    controller_status = controller_state.status if controller_state else None

    is_paused = (
        exec_status == ExecutionStatus.PAUSED.value or
        controller_status == "paused"
    )

    if not is_paused:
        return {
            "ok": False,
            "message": f"Execution is not at a checkpoint. Status: {exec_status}"
        }

    # Resume execution
    success = await controller.request_resume(execution_id)

    if success:
        return {
            "ok": True,
            "message": f"Checkpoint continued for execution {execution_id}"
        }
    else:
        return {
            "ok": False,
            "message": "Failed to continue from checkpoint"
        }


class BypassCheckpointRequest(BaseModel):
    """Request model for bypassing checkpoint."""
    checkpoint_id: Optional[str] = None
    scope: str = "this_run"  # 'this_run' | 'this_version'


@router.post("/{execution_id}/bypass-checkpoint")
async def bypass_checkpoint(
    execution_id: str,
    request: Optional[BypassCheckpointRequest] = None,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Bypass a human checkpoint and continue to completion.

    Args:
        checkpoint_id: Optional checkpoint ID to bypass
        scope: 'this_run' bypasses for current execution only,
               'this_version' bypasses for all future runs of this version

    Skips the current checkpoint and continues execution
    without waiting for human review.
    """
    from services.runtime.execution_manager import get_execution_manager, ExecutionStatus
    from services.runtime.execution_control import get_controller

    manager = get_execution_manager()
    controller = get_controller()

    # Parse request parameters
    checkpoint_id = request.checkpoint_id if request else None
    scope = request.scope if request else "this_run"

    # Verify execution exists
    status = manager.get_status(execution_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    # Check ownership
    user_id = current_user.get("id") if current_user else None
    exec_user_id = status.get("user_id")

    if user_id and exec_user_id and user_id != exec_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot bypass checkpoint for execution owned by another user"
        )

    # Check if execution is paused
    exec_status = status.get("status")
    controller_state = controller.get_state(execution_id)
    controller_status = controller_state.status if controller_state else None

    is_paused = (
        exec_status == ExecutionStatus.PAUSED.value or
        controller_status == "paused"
    )

    if not is_paused:
        return {
            "ok": False,
            "message": f"Execution is not at a checkpoint. Status: {exec_status}"
        }

    # Use run_to_end to bypass all checkpoints
    success = await controller.run_to_end(execution_id)

    if success:
        return {
            "ok": True,
            "message": "Checkpoint bypassed, execution running to completion",
            "checkpoint_id": checkpoint_id,
            "scope": scope,
        }
    else:
        return {
            "ok": False,
            "message": "Failed to bypass checkpoint"
        }
