"""
Workflow Execution Endpoints

Execute workflows and manage execution history.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from api.workflows.models import WorkflowRunRequest
from gateway.local_context import get_local_actor

logger = logging.getLogger(__name__)

run_router = APIRouter()
router = run_router


def _extract_step_ids(workflow: Dict[str, Any]) -> set[str]:
    """Return explicit step IDs from a parsed workflow definition."""
    step_ids: set[str] = set()
    for step in workflow.get("steps") or []:
        if isinstance(step, dict):
            step_id = step.get("id")
            if isinstance(step_id, str) and step_id:
                step_ids.add(step_id)
    return step_ids


def _validate_run_preflight(request: WorkflowRunRequest, workflow: Dict[str, Any]) -> None:
    """Validate run controls that depend on parsed workflow structure."""
    steps = workflow.get("steps") or []
    step_count = len(steps)

    start_step = getattr(request, "start_step", None)
    end_step = getattr(request, "end_step", None)

    if start_step is not None and start_step >= step_count:
        raise HTTPException(status_code=400, detail="startStep must reference an existing workflow step")
    if end_step is not None and end_step >= step_count:
        raise HTTPException(status_code=400, detail="endStep must reference an existing workflow step")

    breakpoints = getattr(request, "breakpoints", None) or []
    if breakpoints:
        step_ids = _extract_step_ids(workflow)
        unknown_breakpoints = [breakpoint for breakpoint in breakpoints if breakpoint not in step_ids]
        if unknown_breakpoints:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown breakpoint node IDs: {', '.join(unknown_breakpoints)}",
            )


@run_router.post("/run")
async def run_workflow_direct(
    request: WorkflowRunRequest,
    workspace_context: dict = Depends(get_local_actor),
):
    """
    Run workflow directly using Core engine.
    Accepts workflow as YAML string and executes immediately.
    Returns execution_id for tracking.

    CE always associates execution state with its fixed local workspace actor.
    """
    import yaml
    from services.runtime.execution_manager import get_execution_manager

    workspace_id = workspace_context["id"]
    logger.debug("Direct local workflow request workspace=%s", workspace_id)

    try:
        workflow = yaml.safe_load(request.workflow_yaml)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")

    if not workflow:
        raise HTTPException(status_code=400, detail="Empty workflow")
    if not workflow.get("steps"):
        raise HTTPException(status_code=400, detail="Workflow must have steps")
    _validate_run_preflight(request, workflow)

    # Note: Skipping pre-execution validation for /run endpoint.
    # The execution engine validates at runtime with better context.
    # Pre-validation produces false positives for loop workflows
    # (INVALID_START_NODE, PORT_NOT_FOUND, MODULE_NOT_FOUND for type-based nodes).

    try:
        exec_manager = get_execution_manager()
        execution_id = await exec_manager.start(
            workflow_yaml=request.workflow_yaml,
            variables=request.params or {},
            workflow_id="local",
            start_step=request.start_step,
            end_step=request.end_step,
            breakpoints=request.breakpoints,
            screenshot_mode=request.screenshot_mode,
            workspace_id=workspace_id,
        )

        return {
            "ok": True,
            "execution_id": execution_id,
            "message": "Workflow execution started"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as exc:
        logger.exception("Direct workflow execution failed")
        raise HTTPException(status_code=500, detail="Workflow execution failed") from exc
