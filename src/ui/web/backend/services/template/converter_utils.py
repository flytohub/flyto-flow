"""
Workflow Converter Utilities

Pure helper functions for edge classification and key-access normalization.
These are used by WorkflowConverter, validation modules, and layout engine.

No dependency on WorkflowConverter class — can be imported independently.
"""


# Layout constants
INITIAL_X = 100
INITIAL_Y = 150
HORIZONTAL_SPACING = 300
RESOURCE_SPACING = 200
RESOURCE_Y_OFFSET = 160


# ---------------------------------------------------------------------------
# Key-access helpers (frontend HTTP client converts camelCase -> snake_case)
# ---------------------------------------------------------------------------

def _get_source_handle(e: dict) -> str:
    """Get sourceHandle from edge, supporting both camelCase and snake_case."""
    return str(e.get("sourceHandle") or e.get("source_handle") or "")


def _get_target_handle_from_edge(e: dict) -> str:
    """Get targetHandle from edge, supporting both camelCase and snake_case."""
    return str(e.get("targetHandle") or e.get("target_handle") or "")


def _get_edge_data_type(e: dict) -> str:
    """Get edgeType from edge.data, supporting both camelCase and snake_case."""
    data = e.get("data") or {}
    return str(data.get("edgeType") or data.get("edge_type") or "").lower()


_RESOURCE_HANDLE_TO_TYPE = {
    "target-model": "model",
    "target-memory": "memory",
    "target-tools": "tools",
}


def _is_resource_edge(e: dict) -> bool:
    """Check if edge is a resource edge (sub-node -> AI Agent)."""
    if _get_edge_data_type(e) == "resource":
        return True
    th = _get_target_handle_from_edge(e)
    return bool(th and th in _RESOURCE_HANDLE_TO_TYPE)


def classify_resource_edge(e: dict) -> str | None:
    """Classify a resource edge by its targetHandle.

    Returns "model", "memory", or "tools" based on the edge's targetHandle.
    Returns None if the edge is not a resource edge or has no recognizable handle.
    This is the single source of truth for resource edge categorization.
    """
    if not _is_resource_edge(e):
        return None
    th = _get_target_handle_from_edge(e)
    return _RESOURCE_HANDLE_TO_TYPE.get(th)
