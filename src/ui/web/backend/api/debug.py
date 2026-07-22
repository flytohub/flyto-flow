"""
Debug API

REST endpoints for debugging workflow executions.

Debug endpoints are scoped to the fixed local workspace.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from capabilities import Feature, require_feature
from gateway.local_context import get_local_actor

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    dependencies=[
        Depends(require_feature(Feature.EXECUTION_DEBUG)),
        Depends(get_local_actor),
    ],
)


# ============================================================================
# Request/Response Models
# ============================================================================


class ReplayRequest(BaseModel):
    """Request to replay an execution."""

    override_inputs: Optional[Dict[str, Any]] = None


class RerunRequest(BaseModel):
    """Request to rerun from a specific node."""

    node_id: str
    mode: str = "rehydrate"  # rehydrate, recompute
    override_inputs: Optional[Dict[str, Any]] = None


class CompareRequest(BaseModel):
    """Request to compare executions."""

    execution_id_1: str
    execution_id_2: str


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/timeline/{execution_id}")
async def get_execution_timeline(execution_id: str) -> Dict[str, Any]:
    """
    Get execution timeline for visualization.

    Returns timeline events, context snapshots, and status summary.
    """
    from services.debug import DebugService

    timeline = await DebugService.get_timeline(execution_id)

    if not timeline:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found",
        )

    return timeline.to_dict()


@router.get("/timeline/{execution_id}/node/{node_id}")
async def get_node_detail(
    execution_id: str,
    node_id: str,
) -> Dict[str, Any]:
    """
    Get detailed information about a specific node execution.

    Includes inputs, outputs, error details, and context from previous steps.
    """
    from services.debug import DebugService

    detail = await DebugService.get_node_detail(execution_id, node_id)

    if not detail:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found in execution {execution_id}",
        )

    return detail


@router.get("/timeline/{execution_id}/variables")
async def get_variables_at_step(
    execution_id: str,
    step_index: int = Query(..., description="Step index to get variables at"),
) -> Dict[str, Any]:
    """
    Get all variables/context at a specific step.

    Returns accumulated outputs from all previous steps.
    """
    from services.debug import DebugService

    variables = await DebugService.get_variables_at_step(execution_id, step_index)

    return {
        "execution_id": execution_id,
        "step_index": step_index,
        "variables": variables,
    }


@router.post("/replay/{execution_id}")
async def replay_execution(
    execution_id: str,
    request: Optional[ReplayRequest] = None,
) -> Dict[str, Any]:
    """
    Replay an entire execution with same (or overridden) inputs.

    Creates a new execution using the original workflow snapshot.
    """
    from services.debug import DebugService

    override_inputs = request.override_inputs if request else None

    result = await DebugService.replay_execution(
        execution_id=execution_id,
        override_inputs=override_inputs,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=result.error or "Failed to replay execution",
        )

    return result.to_dict()


@router.post("/rerun/{execution_id}")
async def rerun_from_node(
    execution_id: str,
    request: RerunRequest,
) -> Dict[str, Any]:
    """
    Rerun execution starting from a specific node.

    Modes:
    - rehydrate: Inject outputs from previous steps, run from specified node
    - recompute: Rerun all dependencies of specified node
    """
    from services.debug import DebugService, RerunMode

    try:
        mode = RerunMode(request.mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rerun mode: {request.mode}. Use 'rehydrate' or 'recompute'",
        )

    result = await DebugService.rerun_from_node(
        execution_id=execution_id,
        node_id=request.node_id,
        mode=mode,
        override_inputs=request.override_inputs,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=result.error or "Failed to rerun from node",
        )

    return result.to_dict()


@router.post("/compare")
async def compare_executions(request: CompareRequest) -> Dict[str, Any]:
    """
    Compare two executions.

    Returns differences in status, duration, and step outcomes.
    """
    from services.debug import DebugService

    comparison = await DebugService.compare_executions(
        exec_id_1=request.execution_id_1,
        exec_id_2=request.execution_id_2,
    )

    if "error" in comparison:
        raise HTTPException(
            status_code=404,
            detail=comparison["error"],
        )

    return comparison


@router.get("/error-analysis/{execution_id}")
async def get_error_analysis(execution_id: str) -> Dict[str, Any]:
    """
    Get detailed error analysis for a failed execution.

    Includes error classification, failed step details, and fix suggestions.
    """
    from services.debug import DebugService

    analysis = await DebugService.get_error_analysis(execution_id)

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found",
        )

    return analysis


@router.get("/history/{workflow_id}")
async def get_execution_history(
    workflow_id: str,
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
) -> Dict[str, Any]:
    """
    Get execution history for a workflow.

    Returns list of recent executions with summary info.
    """
    from gateway.storage.execution_repo import ExecutionRepository

    executions = ExecutionRepository.list_executions(
        workflow_id=workflow_id,
        limit=limit,
    )

    # Filter by status if specified
    if status:
        executions = [e for e in executions if e.status == status]

    return {
        "workflow_id": workflow_id,
        "total": len(executions),
        "executions": [
            {
                "id": e.id,
                "status": e.status,
                "started_at": e.started_at,
                "finished_at": e.finished_at,
                "duration_ms": e.duration_ms,
                "error_message": e.error_message[:100] if e.error_message else None,
            }
            for e in executions
        ],
    }


@router.get("/stats/{workflow_id}")
async def get_workflow_stats(workflow_id: str) -> Dict[str, Any]:
    """
    Get execution statistics for a workflow.

    Returns success rate, average duration, common errors, etc.
    """
    from gateway.storage.execution_repo import ExecutionRepository

    executions = ExecutionRepository.list_executions(
        workflow_id=workflow_id,
        limit=100,
    )

    if not executions:
        return {
            "workflow_id": workflow_id,
            "total_executions": 0,
        }

    # Calculate stats
    total = len(executions)
    succeeded = sum(1 for e in executions if e.status == "success")
    failed = sum(1 for e in executions if e.status in ("failure", "failed"))
    cancelled = sum(1 for e in executions if e.status == "cancelled")

    durations = [e.duration_ms for e in executions if e.duration_ms]
    avg_duration = sum(durations) / len(durations) if durations else None

    # Count error categories
    error_counts: Dict[str, int] = {}
    for e in executions:
        if e.error_category:
            error_counts[e.error_category] = error_counts.get(e.error_category, 0) + 1

    return {
        "workflow_id": workflow_id,
        "total_executions": total,
        "success_count": succeeded,
        "failure_count": failed,
        "cancelled_count": cancelled,
        "success_rate": round(succeeded / total * 100, 1) if total > 0 else 0,
        "average_duration_ms": round(avg_duration) if avg_duration else None,
        "error_categories": error_counts,
    }
