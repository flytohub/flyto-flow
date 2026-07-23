"""
Workflow Graph Helpers

Shared helpers for building workflow dicts from request nodes/edges.
Used by the conversion endpoints (validate, layout, graph-relations, etc.).
"""

from typing import Any


def _build_workflow_dict(
    nodes,
    edges,
    *,
    node_extra_fields: tuple = (),
    edge_extra_fields: tuple = (),
    **top_level,
) -> dict:
    """Build a workflow dict from request nodes/edges.

    Args:
        nodes: Iterable of node objects with at least id, module_id, params.
        edges: Iterable of edge objects with at least id, source, target.
        node_extra_fields: Additional attribute names to include per node
            (e.g. ``("data",)`` or ``("data", "ui_state")``).
        edge_extra_fields: Additional attribute names to include per edge
            (e.g. ``("type", "data")`` or ``("type", "sourceHandle", "targetHandle", "data")``).
        **top_level: Extra top-level keys merged into the returned dict
            (e.g. ``has_loop=True``).
    """
    result: dict = {
        "nodes": [
            {
                "id": n.id,
                "module_id": n.module_id,
                "params": n.params,
                **{f: getattr(n, f) for f in node_extra_fields},
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": e.id,
                "source": e.source,
                "target": e.target,
                **{f: getattr(e, f) for f in edge_extra_fields},
            }
            for e in edges
        ],
    }
    result.update(top_level)
    return result


# Re-exported for api.workflows.routes, which mounts it onto local_router.
from api.workflows.conversion_routes import conversion_router  # noqa: E402
