"""
Lineage Step Routes

Step-specific lineage endpoints: step lineage, dependencies, impact.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from api.lineage.models import StepLineageResponse
from api.lineage.services import (
    load_execution_evidence,
    get_value_preview,
    get_data_type,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/executions/{execution_id}/steps/{step_id}")
async def get_step_lineage(
    execution_id: str,
    step_id: str,
) -> StepLineageResponse:
    """
    Get lineage for a specific step.

    Shows inputs, outputs, and connections to other steps.
    """
    steps = load_execution_evidence(execution_id)
    if not steps:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Find the target step and its index
    target_step = None
    step_index = -1
    for i, step in enumerate(steps):
        if step.get('step_id') == step_id:
            target_step = step
            step_index = i
            break

    if target_step is None:
        raise HTTPException(status_code=404, detail="Step not found")

    before = target_step.get('context_before', {})
    after = target_step.get('context_after', {})

    # Calculate consumed and produced variables
    consumed = list(before.keys())
    produced = [k for k in after if k not in before or before.get(k) != after.get(k)]

    # Find upstream and downstream steps
    upstream = []
    downstream = []

    for i, step in enumerate(steps):
        sid = step.get('step_id', f'step_{i}')
        if i < step_index:
            # Check if this step produced something we consume
            step_after = step.get('context_after', {})
            step_before = step.get('context_before', {})
            for key in consumed:
                if key in step_after and (key not in step_before or step_before.get(key) != step_after.get(key)):
                    if sid not in upstream:
                        upstream.append(sid)
        elif i > step_index:
            # Check if this step consumes something we produce
            step_before = step.get('context_before', {})
            for key in produced:
                if key in step_before:
                    if sid not in downstream:
                        downstream.append(sid)

    return StepLineageResponse(
        step_id=step_id,
        module_id=target_step.get('module_id'),
        inputs=before,
        outputs=after,
        consumed_variables=consumed,
        produced_variables=produced,
        upstream_steps=upstream,
        downstream_steps=downstream,
    )


@router.get("/executions/{execution_id}/steps/{step_id}/dependencies")
async def get_step_dependencies(
    execution_id: str,
    step_id: str,
) -> Dict[str, Any]:
    """
    Get all dependencies for a step.

    Lists what data the step needs and where it comes from.
    """
    steps = load_execution_evidence(execution_id)
    if not steps:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Find the target step
    target_step = None
    step_index = -1
    for i, step in enumerate(steps):
        if step.get('step_id') == step_id:
            target_step = step
            step_index = i
            break

    if target_step is None:
        raise HTTPException(status_code=404, detail="Step not found")

    before = target_step.get('context_before', {})

    # For each variable in before, find which step produced it
    dependencies: List[Dict[str, Any]] = []

    for var_name, var_value in before.items():
        dependency = {
            "variable": var_name,
            "value_preview": get_value_preview(var_value),
            "data_type": get_data_type(var_value),
            "source_step": None,
            "source_type": "unknown",
        }

        # Search previous steps for the producer
        for i in range(step_index - 1, -1, -1):
            prev_step = steps[i]
            prev_before = prev_step.get('context_before', {})
            prev_after = prev_step.get('context_after', {})

            if var_name in prev_after:
                if var_name not in prev_before or prev_before.get(var_name) != prev_after.get(var_name):
                    dependency["source_step"] = prev_step.get('step_id')
                    dependency["source_type"] = "step_output"
                    break

        # If not found in any step, it might be initial input
        if dependency["source_step"] is None:
            dependency["source_type"] = "initial_input"

        dependencies.append(dependency)

    return {
        "step_id": step_id,
        "dependencies": dependencies,
        "dependency_count": len(dependencies),
    }


@router.get("/executions/{execution_id}/steps/{step_id}/impact")
async def get_step_impact(
    execution_id: str,
    step_id: str,
) -> Dict[str, Any]:
    """
    Get impact analysis for a step.

    Shows what downstream steps and variables would be affected
    if this step's output changed.
    """
    steps = load_execution_evidence(execution_id)
    if not steps:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Find the target step
    target_step = None
    step_index = -1
    for i, step in enumerate(steps):
        if step.get('step_id') == step_id:
            target_step = step
            step_index = i
            break

    if target_step is None:
        raise HTTPException(status_code=404, detail="Step not found")

    after = target_step.get('context_after', {})
    before = target_step.get('context_before', {})

    # Find produced variables
    produced = [k for k in after if k not in before or before.get(k) != after.get(k)]

    # Find downstream steps that consume these variables
    impacted_steps: List[str] = []
    impacted_variables: List[str] = list(produced)

    for i in range(step_index + 1, len(steps)):
        downstream = steps[i]
        downstream_id = downstream.get('step_id', f'step_{i}')
        downstream_before = downstream.get('context_before', {})

        # Check if any produced variable is consumed
        for var in produced:
            if var in downstream_before:
                if downstream_id not in impacted_steps:
                    impacted_steps.append(downstream_id)

    return {
        "step_id": step_id,
        "produced_variables": produced,
        "impacted_steps": impacted_steps,
        "impacted_variables": impacted_variables,
        "impact_count": len(impacted_steps),
    }
