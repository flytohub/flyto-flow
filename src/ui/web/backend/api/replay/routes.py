"""
Replay API Routes

Provides REST endpoints for workflow replay operations:
- Validate replay feasibility
- Execute replay from specific step (with actual workflow engine execution)
- Compare original vs replay results
- View replay history

This is a capability n8n lacks - step-level replay with context modification.

Integration with Workflow Engine:
- Uses ExecutionManager to run workflows
- Supports initial_context injection for resume
- Stores evidence for replayed executions
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from api.replay.models import (
    ReplayValidateRequest,
    ReplayExecuteRequest,
    SingleStepReplayRequest,
    CompareRequest,
)
from api.replay.services import get_replay_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/validate")
async def validate_replay(
    request: ReplayValidateRequest,
) -> Dict[str, Any]:
    """
    Validate that a replay is possible.

    Checks:
    - Evidence exists for execution
    - Step exists in execution
    - State can be loaded
    - Modified context keys are valid
    """
    manager = get_replay_manager()

    result = await manager.validate_replay(
        execution_id=request.execution_id,
        step_id=request.step_id,
    )

    return result


def _save_replay_metadata(evidence_path, replay_id: str, metadata: dict):
    """Save replay metadata JSON to the evidence directory."""
    replay_path = evidence_path / replay_id
    replay_path.mkdir(parents=True, exist_ok=True)
    with open(replay_path / "replay_metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, default=str)


def _handle_dry_run(manager, request, context, start_step_index):
    """Handle dry-run replay: save metadata and return prepared context."""
    replay_id = str(uuid.uuid4())
    _save_replay_metadata(manager.evidence_path, replay_id, {
        "type": "replay_dry_run",
        "original_execution_id": request.execution_id,
        "from_step": request.step_id,
        "from_step_index": start_step_index,
        "modified_context": request.modified_context,
        "prepared_context": manager._sanitize_context(context),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {
        "ok": True,
        "replay_id": replay_id,
        "dry_run": True,
        "message": "Dry run prepared - workflow will not be executed",
        "from_step": request.step_id or "start",
        "from_step_index": start_step_index,
        "context_keys": list(context.keys()),
    }


async def _handle_replay_execution(manager, request, context, start_step_index, end_step_index):
    """Execute the actual replay via workflow engine."""
    workflow_yaml = await manager.load_workflow_yaml(request.execution_id)
    if not workflow_yaml:
        return {
            "ok": False,
            "error": "Could not load workflow definition. Original workflow data not available.",
            "suggestion": "Try using dry_run mode to see prepared context.",
        }

    try:
        from services.runtime.execution_manager import get_execution_manager
        exec_manager = get_execution_manager()

        workspace_id = None
        try:
            original_status = exec_manager.get_status(request.execution_id)
            if original_status:
                workspace_id = original_status.get("workspace_id")
        except Exception as e:
            logger.warning(f"Could not get workspace_id from original execution: {e}")

        replay_execution_id = await exec_manager.start(
            workflow_yaml=workflow_yaml,
            workflow_id=f"replay_{request.execution_id[:8]}",
            start_step=start_step_index,
            end_step=end_step_index,
            breakpoints=request.breakpoints if request.breakpoints else None,
            workflow_name=f"Replay from {request.step_id or 'start'}",
            workspace_id=workspace_id,
            initial_context=context,
        )

        _save_replay_metadata(manager.evidence_path, replay_execution_id, {
            "type": "replay",
            "original_execution_id": request.execution_id,
            "from_step": request.step_id,
            "from_step_index": start_step_index,
            "end_step_index": end_step_index,
            "modified_context": request.modified_context,
            "skip_steps": request.skip_steps,
            "breakpoints": request.breakpoints,
            "executed": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        manager.add_to_history(
            original_execution_id=request.execution_id,
            replay_execution_id=replay_execution_id,
            from_step=request.step_id,
            replay_type="partial" if request.step_id else "full",
        )

        return {
            "ok": True,
            "replay_id": replay_execution_id,
            "executed": True,
            "message": "Replay execution started successfully",
            "from_step": request.step_id or "start",
            "from_step_index": start_step_index,
            "original_execution_id": request.execution_id,
            "context_keys": list(context.keys()),
        }
    except Exception as e:
        logger.error(f"Failed to execute replay: {e}")
        return {
            "ok": False,
            "error": f"Failed to execute replay: {str(e)}",
            "original_execution_id": request.execution_id,
            "from_step": request.step_id,
        }


@router.post("/execute")
async def execute_replay(
    request: ReplayExecuteRequest,
) -> Dict[str, Any]:
    """
    Execute workflow replay from a specific step.

    Full workflow engine integration:
    1. Validate the replay is possible
    2. Load the original workflow YAML
    3. Load context from the target step
    4. Apply modifications
    5. Execute workflow from that step using ExecutionManager
    6. Return the new execution ID for comparison
    """
    manager = get_replay_manager()

    if request.step_id:
        validation = await manager.validate_replay(
            execution_id=request.execution_id, step_id=request.step_id,
        )
        if not validation.get('can_replay'):
            return {
                "ok": False,
                "error": validation.get('reason', 'Replay validation failed'),
                "validation": validation,
            }

    steps = manager._load_evidence(request.execution_id)
    if not steps:
        return {"ok": False, "error": "Execution not found"}

    # Build starting context
    start_step_index = None
    end_step_index = None
    context = {}

    if request.step_id:
        start_step = manager._find_step(steps, request.step_id)
        if not start_step:
            return {"ok": False, "error": f"Step {request.step_id} not found"}
        context = start_step.get('context_before', {}).copy()
        start_step_index = start_step.get('step_index', 0)

    if request.end_step_id:
        end_step_index = manager.get_step_index(request.execution_id, request.end_step_id)

    context.update(request.modified_context)

    if request.dry_run:
        return _handle_dry_run(manager, request, context, start_step_index)

    return await _handle_replay_execution(manager, request, context, start_step_index, end_step_index)


@router.get("/status/{replay_id}")
async def get_replay_status(
    replay_id: str,
) -> Dict[str, Any]:
    """
    Get the status of a replay execution.

    Returns current execution status, result, or error.
    """
    try:
        from services.runtime.execution_manager import get_execution_manager

        exec_manager = get_execution_manager()
        status = exec_manager.get_status(replay_id)

        if not status:
            return {
                "ok": False,
                "error": "Replay execution not found",
                "replay_id": replay_id
            }

        # Map status to simpler format
        exec_status = status.get('status', 'unknown')
        is_completed = exec_status in ('completed', 'success')
        is_failed = exec_status in ('failed', 'failure')
        is_running = exec_status == 'running'

        # Load replay metadata if available
        manager = get_replay_manager()
        metadata_file = manager.evidence_path / replay_id / "replay_metadata.json"
        replay_metadata = None

        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    replay_metadata = json.load(f)
            except Exception:
                pass

        return {
            "ok": True,
            "replay_id": replay_id,
            "status": exec_status,
            "is_running": is_running,
            "is_completed": is_completed,
            "is_failed": is_failed,
            "current_step": status.get('current_step'),
            "total_steps": status.get('total_steps'),
            "result": status.get('result') if is_completed else None,
            "error": status.get('error') if is_failed else None,
            "start_time": status.get('start_time'),
            "end_time": status.get('end_time'),
            "original_execution_id": replay_metadata.get('original_execution_id') if replay_metadata else None,
            "from_step": replay_metadata.get('from_step') if replay_metadata else None,
        }

    except Exception:
        logger.exception("Failed to get replay status")
        return {
            "ok": False,
            "error": "Failed to get replay status",
            "replay_id": replay_id
        }


@router.post("/step")
async def replay_single_step(
    request: SingleStepReplayRequest,
) -> Dict[str, Any]:
    """
    Re-execute a single step with modified parameters.

    Uses the same ExecutionManager pattern as /execute, but constrains
    start_step and end_step to the target step index so only that
    single step is run through the real workflow engine.
    """
    manager = get_replay_manager()

    # Load step state
    state = await manager.load_execution_state(
        request.execution_id,
        request.step_id
    )

    if not state:
        return {"ok": False, "error": f"Step {request.step_id} not found"}

    # Load workflow YAML (required for execution)
    workflow_yaml = await manager.load_workflow_yaml(request.execution_id)
    if not workflow_yaml:
        return {
            "ok": False,
            "error": "Could not load workflow definition. Original workflow data not available.",
        }

    # Build context: start from context_before, apply user modifications
    context = state.get('context_before', {}).copy()
    context.update(request.modified_context)

    # If user provided modified params, inject them into context so the
    # engine picks them up as overrides for this step's parameters.
    if request.modified_params:
        context["__replay_param_overrides__"] = {
            request.step_id: request.modified_params,
        }

    # Determine the step index to constrain execution to this single step
    step_index = state.get('step_index', 0)

    try:
        from services.runtime.execution_manager import get_execution_manager
        exec_manager = get_execution_manager()

        workspace_id = None
        try:
            original_status = exec_manager.get_status(request.execution_id)
            if original_status:
                workspace_id = original_status.get("workspace_id")
        except Exception as e:
            logger.warning(f"Could not get workspace_id from original execution: {e}")

        replay_execution_id = await exec_manager.start(
            workflow_yaml=workflow_yaml,
            workflow_id=f"replay_step_{request.execution_id[:8]}",
            start_step=step_index,
            end_step=step_index,
            workflow_name=f"Replay step {request.step_id}",
            workspace_id=workspace_id,
            initial_context=context,
        )

        _save_replay_metadata(manager.evidence_path, replay_execution_id, {
            "type": "single_step_replay",
            "original_execution_id": request.execution_id,
            "step_id": request.step_id,
            "step_index": step_index,
            "module_id": state.get('module_id'),
            "modified_params": request.modified_params,
            "modified_context": request.modified_context,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        manager.add_to_history(
            original_execution_id=request.execution_id,
            replay_execution_id=replay_execution_id,
            from_step=request.step_id,
            replay_type="single_step",
        )

        return {
            "ok": True,
            "replay_id": replay_execution_id,
            "executed": True,
            "message": "Single step replay started",
            "step_id": request.step_id,
            "step_index": step_index,
            "module_id": state.get('module_id'),
            "original_execution_id": request.execution_id,
        }

    except Exception:
        logger.exception("Failed to execute single step replay")
        return {
            "ok": False,
            "error": "Failed to execute single step replay",
            "step_id": request.step_id,
        }


@router.get("/{execution_id}/state/{step_id}")
async def get_step_state(
    execution_id: str,
    step_id: str,
) -> Dict[str, Any]:
    """
    Get execution state at a specific step.

    Returns context before and after the step, along with step metadata.
    """
    manager = get_replay_manager()

    state = await manager.load_execution_state(execution_id, step_id)

    if not state:
        raise HTTPException(status_code=404, detail="Step state not found")

    return {
        "execution_id": execution_id,
        **state,
    }


@router.get("/{execution_id}/steps")
async def list_execution_steps(
    execution_id: str,
) -> Dict[str, Any]:
    """
    List all steps from an execution with their state.

    Returns step IDs, status, and timing information.
    """
    manager = get_replay_manager()

    steps = await manager.load_execution_steps(execution_id)

    if not steps:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Calculate summary stats
    total_duration = sum(s.get('duration_ms', 0) or 0 for s in steps)
    failed_count = sum(1 for s in steps if s.get('status') == 'failed')

    return {
        "execution_id": execution_id,
        "step_count": len(steps),
        "total_duration_ms": total_duration,
        "failed_count": failed_count,
        "steps": steps,
    }


@router.post("/compare")
async def compare_executions(
    request: CompareRequest,
) -> Dict[str, Any]:
    """
    Compare original execution with replay.

    Shows differences in:
    - Step outcomes
    - Output values
    - Execution paths
    """
    manager = get_replay_manager()

    result = await manager.compare_replay(
        original_execution_id=request.original_execution_id,
        replay_execution_id=request.replay_execution_id,
    )

    return result


@router.get("/history")
async def get_replay_history(
    execution_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
) -> Dict[str, Any]:
    """
    Get replay history.

    Optionally filter by original execution ID.
    """
    manager = get_replay_manager()

    history = manager.get_replay_history(execution_id)

    # Apply limit and reverse for newest first
    history = list(reversed(history[-limit:]))

    return {
        "history": history,
        "total": len(history),
    }


@router.get("/{execution_id}/context-at/{step_id}")
async def get_context_at_step(
    execution_id: str,
    step_id: str,
    before: bool = Query(default=True),
) -> Dict[str, Any]:
    """
    Get context at a specific step.

    Args:
        before: If True, return context_before; otherwise context_after
    """
    manager = get_replay_manager()

    state = await manager.load_execution_state(execution_id, step_id)

    if not state:
        raise HTTPException(status_code=404, detail="Step not found")

    context_key = 'context_before' if before else 'context_after'

    return {
        "execution_id": execution_id,
        "step_id": step_id,
        "position": "before" if before else "after",
        "context": state.get(context_key, {}),
    }


@router.get("/{execution_id}/summary")
async def get_execution_summary(
    execution_id: str,
) -> Dict[str, Any]:
    """
    Get execution summary for replay panel.

    Returns a high-level overview suitable for UI display.
    """
    manager = get_replay_manager()

    steps = await manager.load_execution_steps(execution_id)

    if not steps:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Group by status
    status_counts = {}
    for s in steps:
        status = s.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1

    # Find failed steps
    failed_steps = [s for s in steps if s.get('status') == 'failed']

    # Calculate timing
    total_duration = sum(s.get('duration_ms', 0) or 0 for s in steps)

    return {
        "execution_id": execution_id,
        "step_count": len(steps),
        "status_counts": status_counts,
        "total_duration_ms": total_duration,
        "failed_steps": [
            {
                "step_id": s.get('step_id'),
                "module_id": s.get('module_id'),
                "error": s.get('error')
            }
            for s in failed_steps
        ],
        "replayable": len(steps) > 0,
        "has_failures": len(failed_steps) > 0
    }
