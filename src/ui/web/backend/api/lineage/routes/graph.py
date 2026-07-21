"""
Lineage Graph Routes

Full lineage graph endpoint for visualizing execution data flow.
"""

import logging
from typing import Dict, List, Set

from fastapi import APIRouter, HTTPException, Query

from api.lineage.models import (
    LineageNode,
    LineageEdge,
    LineageGraphResponse,
)
from api.lineage.services import (
    load_execution_evidence,
    get_value_preview,
    get_data_type,
    classify_module,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/executions/{execution_id}/graph")
async def get_lineage_graph(
    execution_id: str,
    include_variables: bool = Query(default=True),
) -> LineageGraphResponse:
    """
    Get full data lineage graph for an execution.

    Returns nodes (steps and variables) and edges (data flow).
    """
    steps = load_execution_evidence(execution_id)
    if not steps:
        raise HTTPException(status_code=404, detail="Execution not found")

    nodes: List[LineageNode] = []
    edges: List[LineageEdge] = []
    variables_seen: Set[str] = set()

    # Track variable origins
    variable_origins: Dict[str, str] = {}  # variable -> step that produced it

    # First pass: identify all steps and what they produce
    for i, step in enumerate(steps):
        step_id = step.get('step_id', f'step_{i}')
        module_id = step.get('module_id', 'unknown')

        # Classify module for category and lane
        classification = classify_module(module_id)

        # Add step node with category
        nodes.append(LineageNode(
            id=f"step_{step_id}",
            type="step",
            label=f"{module_id}",
            step_id=step_id,
            module_id=module_id,
            category=classification["category"],
            lane=classification["lane"],
            is_control_flow=classification["is_control_flow"],
            order=i,
        ))

        # Find produced variables (in after but not in before, or changed)
        before = step.get('context_before', {})
        after = step.get('context_after', {})

        for key in after:
            if key not in before or before.get(key) != after.get(key):
                variable_origins[key] = step_id
                variables_seen.add(key)

    # Add variable nodes if requested
    if include_variables:
        # Get final context from last step
        final_context = steps[-1].get('context_after', {}) if steps else {}

        for var_name in variables_seen:
            value = final_context.get(var_name)
            nodes.append(LineageNode(
                id=f"var_{var_name}",
                type="variable",
                label=var_name,
                variable_name=var_name,
                data_type=get_data_type(value),
                value_preview=get_value_preview(value),
            ))

    # Second pass: create edges
    for i, step in enumerate(steps):
        step_id = step.get('step_id', f'step_{i}')
        before = step.get('context_before', {})
        after = step.get('context_after', {})

        if include_variables:
            # Edges from variables to step (consumption)
            for key in before:
                if key in variables_seen:
                    edges.append(LineageEdge(
                        source=f"var_{key}",
                        target=f"step_{step_id}",
                        edge_type="consumes",
                        label="reads",
                    ))

            # Edges from step to variables (production)
            for key in after:
                if key not in before or before.get(key) != after.get(key):
                    edges.append(LineageEdge(
                        source=f"step_{step_id}",
                        target=f"var_{key}",
                        edge_type="produces",
                        label="writes",
                    ))

        # Step to step edges (sequential flow)
        if i > 0:
            prev_step_id = steps[i - 1].get('step_id', f'step_{i - 1}')
            edges.append(LineageEdge(
                source=f"step_{prev_step_id}",
                target=f"step_{step_id}",
                edge_type="data_flow",
                label="next",
            ))

    return LineageGraphResponse(
        execution_id=execution_id,
        nodes=nodes,
        edges=edges,
        step_count=len(steps),
        variable_count=len(variables_seen),
    )
