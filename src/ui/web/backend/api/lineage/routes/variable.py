"""
Lineage Variable Routes

Variable tracing endpoint for tracking variable origins and changes.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from api.lineage.models import VariableLineageResponse
from api.lineage.services import (
    load_execution_evidence,
    get_value_preview,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/executions/{execution_id}/variables/{variable_name}")
async def get_variable_lineage(
    execution_id: str,
    variable_name: str,
) -> VariableLineageResponse:
    """
    Trace a variable through the execution.

    Shows where the variable originated and how it changed.
    """
    steps = load_execution_evidence(execution_id)
    if not steps:
        raise HTTPException(status_code=404, detail="Execution not found")

    history: List[Dict[str, Any]] = []
    origin_step = None
    consumed_by: List[str] = []
    current_value = None

    for step in steps:
        step_id = step.get('step_id', 'unknown')
        before = step.get('context_before', {})
        after = step.get('context_after', {})

        # Check if variable was consumed (present in before)
        if variable_name in before:
            if step_id not in consumed_by:
                consumed_by.append(step_id)

        # Check if variable was produced or modified
        if variable_name in after:
            current_value = after[variable_name]

            if variable_name not in before:
                # Variable was created
                if origin_step is None:
                    origin_step = step_id
                history.append({
                    "step_id": step_id,
                    "action": "created",
                    "value": get_value_preview(current_value),
                    "timestamp": step.get('timestamp'),
                })
            elif before.get(variable_name) != after.get(variable_name):
                # Variable was modified
                history.append({
                    "step_id": step_id,
                    "action": "modified",
                    "before": get_value_preview(before.get(variable_name)),
                    "after": get_value_preview(current_value),
                    "timestamp": step.get('timestamp'),
                })

    if not history and current_value is None:
        raise HTTPException(status_code=404, detail="Variable not found in execution")

    return VariableLineageResponse(
        variable_name=variable_name,
        origin_step=origin_step,
        current_value=current_value,
        history=history,
        consumed_by=consumed_by,
    )
