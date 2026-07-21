"""
Lineage Swimlane Routes

Swimlane view endpoint for visualizing execution flow in lanes.
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query

from api.lineage.models import (
    LineageNode,
    LineageEdge,
    SwimlaneViewResponse,
)
from api.lineage.services import (
    load_execution_evidence,
    classify_module,
    detect_state_nodes,
    group_related_steps,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _classify_nodes(steps, include_control_flow: bool):
    """First pass: classify steps into lane buckets, deduplicate, track variable production."""
    sources: List[LineageNode] = []
    transforms: List[LineageNode] = []
    sinks: List[LineageNode] = []
    seen_steps: Dict[str, LineageNode] = {}
    step_counts: Dict[str, int] = {}

    for i, step in enumerate(steps):
        step_id = step.get('step_id', f'step_{i}')
        module_id = step.get('module_id', 'unknown')
        classification = classify_module(module_id)

        if classification['is_control_flow'] and not include_control_flow:
            continue

        step_counts[step_id] = step_counts.get(step_id, 0) + 1

        if step_id not in seen_steps:
            before = step.get('context_before', {})
            after = step.get('context_after', {})
            node = LineageNode(
                id=f"step_{step_id}",
                type="step",
                label=step_id,
                step_id=step_id,
                module_id=module_id,
                category=classification['category'],
                lane=classification['lane'],
                is_control_flow=classification['is_control_flow'],
                order=len(seen_steps),
                loop_count=1,
                consumed_variables=list(before.keys()),
                produced_variables=[k for k in after if k not in before or before.get(k) != after.get(k)],
                status=step.get('status', 'success'),
                error=step.get('error') or step.get('error_message'),
            )
            seen_steps[step_id] = node

            if classification['lane'] == 'source':
                sources.append(node)
            elif classification['lane'] == 'sink':
                sinks.append(node)
            else:
                transforms.append(node)

    for step_id, count in step_counts.items():
        if step_id in seen_steps:
            seen_steps[step_id].loop_count = count

    return sources, transforms, sinks


def _build_visible_steps(steps, include_control_flow: bool) -> List[dict]:
    """Build the visible step info list for edge construction."""
    visible = []
    for i, step in enumerate(steps):
        step_id = step.get('step_id', f'step_{i}')
        module_id = step.get('module_id', '')
        classification = classify_module(module_id)
        if classification['is_control_flow'] and not include_control_flow:
            continue
        visible.append({
            'step_id': step_id,
            'before': step.get('context_before', {}),
            'after': step.get('context_after', {}),
        })
    return visible


def _build_data_edges(visible_steps: List[dict]) -> List[LineageEdge]:
    """Second pass: create data dependency edges between steps with shared variables."""
    edges: List[LineageEdge] = []
    for i, step_info in enumerate(visible_steps):
        step_id = step_info['step_id']
        relevant_vars = set(step_info['before'].keys()) | set(step_info['after'].keys())

        for j in range(i - 1, -1, -1):
            prev = visible_steps[j]
            prev_vars = set(prev['before'].keys()) | set(prev['after'].keys())
            shared_vars = relevant_vars & prev_vars

            if shared_vars:
                edge_exists = any(
                    e.source == f"step_{prev['step_id']}" and e.target == f"step_{step_id}"
                    for e in edges
                )
                if not edge_exists:
                    shared_var = next(iter(shared_vars))
                    edges.append(LineageEdge(
                        source=f"step_{prev['step_id']}",
                        target=f"step_{step_id}",
                        edge_type="data_dependency",
                        label=shared_var if len(shared_vars) == 1 else f"{len(shared_vars)} vars",
                        is_control_flow=False,
                    ))
                break
    return edges


@router.get("/executions/{execution_id}/swimlane")
async def get_swimlane_view(
    execution_id: str,
    include_control_flow: bool = Query(default=False),
    group_loops: bool = Query(default=True),
) -> SwimlaneViewResponse:
    """
    Get swimlane view for lineage visualization.

    Returns nodes organized into Sources | Transforms | Sinks lanes.
    Control flow nodes (loop/if) are excluded by default.
    """
    steps = load_execution_evidence(execution_id)
    if not steps:
        raise HTTPException(status_code=404, detail="Execution not found")

    sources, transforms, sinks = _classify_nodes(steps, include_control_flow)
    visible_steps = _build_visible_steps(steps, include_control_flow)
    data_edges = _build_data_edges(visible_steps)

    return SwimlaneViewResponse(
        execution_id=execution_id,
        sources=sources,
        transforms=transforms,
        sinks=sinks,
        data_edges=data_edges,
        state_nodes=detect_state_nodes(steps),
        groups=group_related_steps(steps) if group_loops else [],
    )
