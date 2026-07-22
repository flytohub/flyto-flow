"""
Basic Execution Routes

Core execution endpoints: run, status, cancel, list, cleanup.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends

from gateway.local_context import get_local_actor
from api.executions.models import (
    RunWorkflowRequest,
    RunWorkflowResponse,
    ExecutionStatusResponse,
    CancelResponse,
    ExecutionListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run", response_model=RunWorkflowResponse)
async def run_workflow(
    request: RunWorkflowRequest,
    workspace_context: dict = Depends(get_local_actor),
):
    """
    Start a new workflow execution.

    The execution is scoped to the fixed local CE workspace.
    """
    try:
        from services.runtime.execution_manager import get_execution_manager
        manager = get_execution_manager()
        workspace_id = workspace_context["id"]

        execution_id = await manager.start(
            workflow_yaml=request.workflow_yaml,
            variables=request.variables,
            workflow_id=request.workflow_id,
            workspace_id=workspace_id,
            screenshot_mode=request.screenshot_mode,
        )

        return RunWorkflowResponse(
            ok=True,
            execution_id=execution_id,
            message="Workflow execution started"
        )

    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: str,
    _: dict = Depends(get_local_actor),
):
    """
    Get status of a workflow execution.

    CE scopes every execution record to its one local workspace.
    """
    from services.runtime.execution_manager import get_execution_manager
    manager = get_execution_manager()
    status = manager.get_status(execution_id)

    if not status:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    return ExecutionStatusResponse(
        ok=True,
        execution=status
    )


@router.post("/{execution_id}/cancel", response_model=CancelResponse)
async def cancel_execution(
    execution_id: str,
    _: dict = Depends(get_local_actor),
):
    """
    Cancel a running workflow execution.

    Cancel a local execution.
    """
    from services.runtime.execution_manager import get_execution_manager
    manager = get_execution_manager()

    status = manager.get_status(execution_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    success = manager.cancel(execution_id)

    if success:
        return CancelResponse(
            ok=True,
            message=f"Execution {execution_id} cancelled"
        )
    else:
        return CancelResponse(
            ok=False,
            message=f"Cannot cancel execution in status: {status['status']}"
        )


@router.get("/", response_model=ExecutionListResponse)
async def list_executions(
    _: dict = Depends(get_local_actor),
):
    """
    List workflow executions.

    List executions stored in the local CE process.
    """
    from services.runtime.execution_manager import get_execution_manager
    manager = get_execution_manager()
    all_executions = manager.get_all_executions()

    filtered = all_executions

    # Enrich each execution with status_group and display_status
    for exec_data in filtered.values():
        raw_status = (exec_data.get("status") or "unknown").lower()
        if raw_status in ("success", "completed"):
            exec_data["status_group"] = "success"
            exec_data["display_status"] = "Success"
        elif raw_status in ("failed", "failure", "error"):
            exec_data["status_group"] = "failed"
            exec_data["display_status"] = "Failed"
        elif raw_status in ("running", "pending"):
            exec_data["status_group"] = "running"
            exec_data["display_status"] = raw_status.capitalize()
        elif raw_status == "cancelled":
            exec_data["status_group"] = "cancelled"
            exec_data["display_status"] = "Cancelled"
        else:
            exec_data["status_group"] = "other"
            exec_data["display_status"] = raw_status.capitalize()

    return ExecutionListResponse(
        ok=True,
        executions=filtered
    )


@router.post("/cleanup")
async def cleanup_executions(
    max_age_seconds: int = 3600,
    _: dict = Depends(get_local_actor),
):
    """
    Clean up old completed/failed/cancelled executions.

    Remove old local execution records.
    """
    from services.runtime.execution_manager import get_execution_manager
    manager = get_execution_manager()
    removed = manager.cleanup(max_age_seconds)

    return {
        "ok": True,
        "removed": removed,
        "message": f"Cleaned up {removed} old executions"
    }
