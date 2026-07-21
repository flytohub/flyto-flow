"""
Debug Timeline

Timeline operations for execution debugging.
"""

import logging
from typing import Any, Dict, Optional

from services.debug.models import ExecutionTimeline, TimelineEvent

logger = logging.getLogger(__name__)


async def get_timeline(execution_id: str) -> Optional[ExecutionTimeline]:
    """
    Get execution timeline for visualization.

    Args:
        execution_id: Execution to get timeline for

    Returns:
        ExecutionTimeline or None if not found
    """
    from gateway.storage.execution_repo import ExecutionRepository

    # Get execution with steps
    execution = ExecutionRepository.get_execution(
        execution_id,
        include_steps=True,
    )

    if not execution:
        return None

    # Build timeline
    timeline = ExecutionTimeline(
        execution_id=execution.id,
        workflow_id=execution.workflow_id,
        workflow_name=execution.workflow_name or "Unknown",
        status=execution.status,
        started_at=execution.started_at,
        finished_at=execution.finished_at,
        duration_ms=execution.duration_ms,
        total_steps=len(execution.steps) if execution.steps else 0,
    )

    # Add events from steps
    completed = 0
    if execution.steps:
        for step in execution.steps:
            # Started event
            if step.started_at:
                timeline.events.append(
                    TimelineEvent(
                        timestamp=step.started_at,
                        event_type="started",
                        node_id=step.step_id,
                        node_run_id=str(step.id) if step.id else None,
                        step_index=step.step_index or 0,
                        module_id=step.module_id,
                        inputs=step.input_params,
                    )
                )

            # Completion event
            if step.finished_at:
                event_type = step.status or "unknown"
                if event_type == "success":
                    event_type = "succeeded"
                    completed += 1

                timeline.events.append(
                    TimelineEvent(
                        timestamp=step.finished_at,
                        event_type=event_type,
                        node_id=step.step_id,
                        node_run_id=str(step.id) if step.id else None,
                        step_index=step.step_index or 0,
                        module_id=step.module_id,
                        duration_ms=step.duration_ms,
                        outputs=step.output_data,
                        error=step.error_message,
                    )
                )

                if event_type == "failed":
                    timeline.failed_step = step.step_id

            # Build context snapshot
            if step.output_data and step.status == "success":
                timeline.context_snapshots[f"step_{step.step_index}"] = {
                    "node_id": step.step_id,
                    "outputs": step.output_data,
                }

    timeline.completed_steps = completed

    # Sort events by timestamp
    timeline.events.sort(key=lambda e: e.timestamp)

    return timeline


async def get_node_detail(
    execution_id: str,
    node_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific node execution.

    Args:
        execution_id: Execution ID
        node_id: Node/step ID to get details for

    Returns:
        Node detail dict or None
    """
    from gateway.storage.execution_repo import ExecutionRepository

    execution = ExecutionRepository.get_execution(
        execution_id,
        include_steps=True,
    )

    if not execution or not execution.steps:
        return None

    # Find the step
    step = None
    for s in execution.steps:
        if s.step_id == node_id:
            step = s
            break

    if not step:
        return None

    # Get context from previous steps
    context = {}
    for s in execution.steps:
        if s.step_index is not None and step.step_index is not None:
            if s.step_index < step.step_index and s.output_data:
                context[f"step_{s.step_index}"] = s.output_data

    return {
        "node_id": step.step_id,
        "module_id": step.module_id,
        "step_index": step.step_index,
        "status": step.status,
        "started_at": step.started_at,
        "finished_at": step.finished_at,
        "duration_ms": step.duration_ms,
        "inputs": step.input_params,
        "outputs": step.output_data,
        "error": step.error_message,
        "context_from_previous": context,
    }


async def get_variables_at_step(
    execution_id: str,
    step_index: int,
) -> Dict[str, Any]:
    """
    Get all variables/context at a specific step.

    Args:
        execution_id: Execution ID
        step_index: Step index to get variables at

    Returns:
        Dictionary of variable name -> value
    """
    timeline = await get_timeline(execution_id)

    if not timeline:
        return {}

    return timeline.get_context_at_step(step_index)
