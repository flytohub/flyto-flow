"""
Shared helpers and key-access utilities used across layout phases.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Key-access helpers (frontend HTTP client converts camelCase -> snake_case)
# ---------------------------------------------------------------------------

def _get_source_handle(e: dict) -> str:
    """Extract source handle from an edge dict, handling camelCase and snake_case."""
    return str(e.get("sourceHandle") or e.get("source_handle") or "")


def _get_target_handle(e: dict) -> str:
    """Extract target handle from an edge dict, handling camelCase and snake_case."""
    return str(e.get("targetHandle") or e.get("target_handle") or "")


def _get_edge_data_type(edge_data: dict) -> str:
    """Extract edge type from edge data dict, normalized to lowercase."""
    return str(edge_data.get("edgeType") or edge_data.get("edge_type") or "").lower()


def _find_child_by_handle(
    parent_id: str,
    children: list,
    edge_handles: dict,
    keyword: str,
) -> Optional[str]:
    """Find a child connected via a handle containing keyword."""
    for child in children:
        handle = edge_handles.get((parent_id, child), "")
        if keyword in handle.lower():
            return child
    # Fallback: if keyword is "true" return first child, "false" return second
    if keyword == "true" and len(children) >= 1:
        return children[0]
    if keyword == "false" and len(children) >= 2:
        return children[1]
    return None


def _effective_case_spacing(num_cases: int, cfg: dict) -> float:
    """Dynamic case spacing: shrink when many cases, floor at min_case_spacing."""
    case_spacing = cfg["case_spacing"]
    min_cs = cfg.get("min_case_spacing", 60)
    return max(min_cs, case_spacing - max(0, num_cases - 4) * 10)
