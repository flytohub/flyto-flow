"""
Basic Execution Routes

Core execution endpoints: run, status, cancel, list, cleanup.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from api.executions.auth import get_optional_user, get_required_user
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
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Start a new workflow execution.

    Authentication is optional - allows local execution without login.
    If authenticated, execution is associated with user.
    """
    try:
        from services.runtime.execution_manager import get_execution_manager
        manager = get_execution_manager()
        user_id = current_user.get("id") if current_user else None

        execution_id = await manager.start(
            workflow_yaml=request.workflow_yaml,
            variables=request.variables,
            workflow_id=request.workflow_id,
            user_id=user_id,
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
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get status of a workflow execution.

    If authenticated, only returns execution if owned by user or public.
    """
    from services.runtime.execution_manager import get_execution_manager
    manager = get_execution_manager()
    status = manager.get_status(execution_id)

    if not status:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    # SECURITY: Strict ownership check
    user_id = current_user.get("id") if current_user else None
    exec_user_id = status.get("user_id")

    # Check deployment mode for access control policy
    from gateway.config import get_gateway_config
    is_cloud_mode = get_gateway_config().is_cloud

    if is_cloud_mode:
        # Cloud mode: strict ownership required
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        if exec_user_id is None:
            logger.warning(f"Orphaned execution {execution_id} accessed by user {user_id}")
            raise HTTPException(status_code=403, detail="Execution has no owner - access denied")
        if user_id != exec_user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        # Local/offline mode: allow access to own or unowned executions
        if user_id and exec_user_id and user_id != exec_user_id:
            raise HTTPException(status_code=403, detail="Access denied")

    await _settle_per_call_if_terminal(execution_id, status)

    return ExecutionStatusResponse(
        ok=True,
        execution=status
    )


@router.post("/{execution_id}/cancel", response_model=CancelResponse)
async def cancel_execution(
    execution_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Cancel a running workflow execution.

    If authenticated, only allows cancelling own executions.
    """
    from services.runtime.execution_manager import get_execution_manager
    manager = get_execution_manager()

    # Check ownership first
    status = manager.get_status(execution_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    # SECURITY: Strict ownership check
    user_id = current_user.get("id") if current_user else None
    exec_user_id = status.get("user_id")
    from gateway.config import get_gateway_config
    is_cloud_mode = get_gateway_config().is_cloud

    if is_cloud_mode:
        # Cloud mode: strict ownership required
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        if exec_user_id is None:
            logger.warning(f"Attempt to cancel orphaned execution {execution_id} by user {user_id}")
            raise HTTPException(
                status_code=403,
                detail="Execution has no owner - cannot cancel"
            )
        if user_id != exec_user_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot cancel execution owned by another user"
            )
    else:
        # Local/offline mode: allow cancelling own or unowned executions
        if user_id and exec_user_id and user_id != exec_user_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot cancel execution owned by another user"
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
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    List workflow executions.

    If authenticated, only returns executions owned by user.
    If not authenticated, returns executions without owner.
    """
    from services.runtime.execution_manager import get_execution_manager
    manager = get_execution_manager()
    all_executions = manager.get_all_executions()

    user_id = current_user.get("id") if current_user else None

    # Filter by ownership
    if user_id:
        # Authenticated: show own executions only
        filtered = {
            k: v for k, v in all_executions.items()
            if v.get("user_id") == user_id or v.get("user_id") is None
        }
    else:
        # Unauthenticated: show public/unowned executions only
        filtered = {
            k: v for k, v in all_executions.items()
            if v.get("user_id") is None
        }

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
    current_user: dict = Depends(get_required_user)
):
    """
    Clean up old completed/failed/cancelled executions.

    Requires authentication. Only cleans executions owned by user
    (or all if user is admin).
    """
    from services.runtime.execution_manager import get_execution_manager
    manager = get_execution_manager()
    user_id = current_user.get("id")
    is_admin = current_user.get("is_admin", False)
    # Self-service cleanup stays here (user cleans own executions). The
    # admin-wide cleanup path migrated to flyto-admin BFF
    # POST /admin/cloud/executions/cleanup, which enqueues the job through
    # the same execution_manager via a worker run. Regular users keep using
    # this endpoint for personal hygiene.
    if is_admin:
        removed = manager.cleanup(max_age_seconds)
    else:
        removed = manager.cleanup(max_age_seconds, user_id=user_id)

    return {
        "ok": True,
        "removed": removed,
        "message": f"Cleaned up {removed} old executions"
    }


async def _settle_per_call_if_terminal(execution_id: str, status: dict) -> None:
    """Best-effort per-call settlement after execution reaches terminal state."""
    try:
        from services.per_call_settlement import (
            is_terminal_execution_status,
            settle_per_call_execution,
        )

        execution_status = status.get("status")
        if not is_terminal_execution_status(execution_status):
            return

        settlement = await settle_per_call_execution(
            execution_id=execution_id,
            status=execution_status,
            error_message=status.get("error") or status.get("error_message"),
        )
        if settlement.get("settled"):
            status["per_call_settlement"] = settlement
    except Exception as exc:
        logger.warning(
            "Failed to settle per-call execution %s: %s",
            execution_id,
            exc,
        )
