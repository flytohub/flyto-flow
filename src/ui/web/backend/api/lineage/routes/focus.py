"""
Lineage Focus Routes

Focused node view for click-to-focus interaction.
"""

import logging
from typing import Any, Dict, List, Set

from fastapi import APIRouter, HTTPException, Query

from api.lineage.services import load_execution_evidence

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/executions/{execution_id}/focus/{node_id}")
async def get_node_focus(
    execution_id: str,
    node_id: str,
    hops: int = Query(default=2, le=5),
) -> Dict[str, Any]:
    """
    Get focused lineage for a specific node.

    Returns only upstream and downstream nodes within N hops.
    This is for the "click to focus" interaction.
    """
    steps = load_execution_evidence(execution_id)
    if not steps:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Find the target step
    target_step = None
    step_index = -1

    # Remove step_ prefix if present
    clean_node_id = node_id.replace('step_', '')

    for i, step in enumerate(steps):
        if step.get('step_id') == clean_node_id:
            target_step = step
            step_index = i
            break

    if target_step is None:
        raise HTTPException(status_code=404, detail="Node not found")

    # Collect upstream and downstream within hops
    upstream_ids: Set[str] = set()
    downstream_ids: Set[str] = set()
    highlight_edges: List[Dict[str, str]] = []

    # Track variable dependencies
    before = target_step.get('context_before', {})
    after = target_step.get('context_after', {})
    consumed = set(before.keys())
    produced = set(k for k in after if k not in before or before.get(k) != after.get(k))

    # Find upstream (who produced what we consume)
    for i in range(step_index - 1, max(-1, step_index - 1 - hops * 3), -1):
        step = steps[i]
        sid = step.get('step_id')
        step_before = step.get('context_before', {})
        step_after = step.get('context_after', {})

        for var in consumed:
            if var in step_after and (var not in step_before or step_before.get(var) != step_after.get(var)):
                upstream_ids.add(sid)
                highlight_edges.append({
                    "source": f"step_{sid}",
                    "target": f"step_{clean_node_id}",
                    "variable": var
                })

    # Find downstream (who consumes what we produce)
    for i in range(step_index + 1, min(len(steps), step_index + 1 + hops * 3)):
        step = steps[i]
        sid = step.get('step_id')
        step_before = step.get('context_before', {})

        for var in produced:
            if var in step_before:
                downstream_ids.add(sid)
                highlight_edges.append({
                    "source": f"step_{clean_node_id}",
                    "target": f"step_{sid}",
                    "variable": var
                })

    return {
        "node_id": node_id,
        "step_id": clean_node_id,
        "module_id": target_step.get('module_id'),
        "consumed_variables": list(consumed),
        "produced_variables": list(produced),
        "upstream": list(upstream_ids),
        "downstream": list(downstream_ids),
        "highlight_edges": highlight_edges,
        "inputs": before,
        "outputs": after
    }
