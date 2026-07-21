"""
Workflow Graph Analysis

Topological sort, layout computation, and graph relation analysis.
"""

import logging
from typing import Dict, List, Any

from services.template.workflow_converter import (
    _is_resource_edge,
    _get_edge_data_type,
)

from .validation_connections import _convert_steps_to_nodes_edges

logger = logging.getLogger(__name__)


def topological_sort_workflow(workflow_dict: dict) -> dict:
    """
    Perform topological sort on workflow steps.

    S-Grade: All graph computation on backend, frontend just renders.

    Args:
        workflow_dict: Workflow with nodes/edges or steps

    Returns:
        {
            "valid": bool,
            "sorted_steps": [...],
            "step_order": [step_ids...],
            "has_cycle": bool
        }
    """
    nodes = workflow_dict.get("nodes", [])
    edges = workflow_dict.get("edges", [])

    # Convert steps to nodes/edges if needed
    if not nodes and workflow_dict.get("steps"):
        nodes, edges = _convert_steps_to_nodes_edges(workflow_dict.get("steps", []))

    # Filter out loop and resource edges
    normal_edges = [
        e for e in edges
        if e.get("type") not in ("loop", "iterate")
        and _get_edge_data_type(e) not in ("iterate", "resource")
        and not _is_resource_edge(e)
    ]

    # Build adjacency and in-degree maps
    adjacency = {n.get("id"): [] for n in nodes}
    in_degree = {n.get("id"): 0 for n in nodes}

    for edge in normal_edges:
        source = edge.get("source")
        target = edge.get("target")
        if source in adjacency and target in in_degree:
            adjacency[source].append(target)
            in_degree[target] = in_degree.get(target, 0) + 1

    # Kahn's algorithm for topological sort
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    sorted_ids = []

    while queue:
        current = queue.pop(0)
        sorted_ids.append(current)

        for neighbor in adjacency.get(current, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Check for cycle (not all nodes processed)
    has_cycle = len(sorted_ids) != len(nodes)

    # Build sorted steps/nodes
    node_map = {n.get("id"): n for n in nodes}
    sorted_nodes = [node_map[nid] for nid in sorted_ids if nid in node_map]

    return {
        "valid": not has_cycle,
        "sorted_steps": sorted_nodes,
        "step_order": sorted_ids,
        "has_cycle": has_cycle
    }


def compute_layout_positions(
    workflow_dict: dict,
    preset: str = "default",
    direction: str = "RIGHT",
) -> dict:
    """
    Compute auto layout positions for workflow nodes.

    Delegates to the smart layout engine (Sugiyama-style).

    Args:
        workflow_dict: Workflow with nodes/edges
        preset: Layout preset (default | compact | spacious)
        direction: Layout direction (RIGHT | DOWN)

    Returns:
        {
            "positions": { node_id: { "x": int, "y": int }, ... }
        }
    """
    from services.template.layout_engine import compute_layout_positions as _engine

    nodes = workflow_dict.get("nodes", [])
    edges = workflow_dict.get("edges", [])

    # Convert steps to nodes/edges if needed
    if not nodes and workflow_dict.get("steps"):
        nodes, edges = _convert_steps_to_nodes_edges(workflow_dict.get("steps", []))
        workflow_dict = {**workflow_dict, "nodes": nodes, "edges": edges}

    return _engine(workflow_dict, preset=preset, direction=direction)


def compute_graph_relations(workflow_dict: dict) -> dict:
    """
    Pre-compute graph relations (predecessors/successors) for all nodes.

    S-Grade: All graph traversal on backend, frontend just looks up.

    Args:
        workflow_dict: Workflow with nodes/edges

    Returns:
        {
            "relations": {
                node_id: {
                    "predecessors": [{ id, label, module }, ...],
                    "successors": [{ id, label, module }, ...]
                },
                ...
            }
        }
    """
    nodes = workflow_dict.get("nodes", [])
    edges = workflow_dict.get("edges", [])

    if not nodes and workflow_dict.get("steps"):
        nodes, edges = _convert_steps_to_nodes_edges(workflow_dict.get("steps", []))

    loop_node_ids = _identify_loop_nodes(nodes)
    normal_edges = [e for e in edges if not _is_excluded_edge(e, loop_node_ids)]

    node_map = {n.get("id"): n for n in nodes}
    incoming, outgoing = _build_adjacency(nodes, normal_edges)

    # Compute relations for all nodes
    relations = {}
    for node in nodes:
        node_id = node.get("id")
        relations[node_id] = {
            "predecessors": _bfs_predecessors(node_id, incoming, node_map),
            "successors": _bfs_successors(node_id, outgoing, node_map),
        }

    # Add loopContext for nodes inside a loop body
    _attach_loop_contexts(relations, loop_node_ids, node_map)

    return {"relations": relations}


# ---------------------------------------------------------------------------
# compute_graph_relations helpers
# ---------------------------------------------------------------------------

def _identify_loop_nodes(nodes: List[Dict]) -> set:
    """Return IDs of loop/foreach nodes."""
    ids = set()
    for n in nodes:
        module = (n.get("data", {}).get("module") or n.get("module_id") or "").lower()
        if "loop" in module or "foreach" in module:
            ids.add(n.get("id"))
    return ids


def _is_excluded_edge(e: Dict, loop_node_ids: set) -> bool:
    """Determine if an edge should be excluded from relation computation."""
    if _get_edge_data_type(e) == "resource" or _is_resource_edge(e):
        return True
    data_type = _get_edge_data_type(e)
    edge_type = (e.get("type") or "").lower()
    if data_type in ("iterate", "loop") or edge_type in ("loop", "iterate"):
        return e.get("target") in loop_node_ids
    return False


def _build_adjacency(nodes: List[Dict], edges: List[Dict]):
    """Build incoming and outgoing adjacency lists."""
    incoming: Dict[str, List[str]] = {n.get("id"): [] for n in nodes}
    outgoing: Dict[str, List[str]] = {n.get("id"): [] for n in nodes}

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source in outgoing and target in incoming:
            outgoing[source].append(target)
            incoming[target].append(source)

    return incoming, outgoing


def _node_info(node_id: str, node_map: Dict) -> dict:
    """Get node info for response."""
    node = node_map.get(node_id, {})
    return {
        "id": node_id,
        "label": node.get("data", {}).get("label") or node.get("label") or node_id,
        "module": node.get("data", {}).get("module") or node.get("module_id"),
    }


def _bfs_predecessors(node_id: str, incoming: Dict, node_map: Dict) -> list:
    """BFS to find all upstream nodes (root-first order)."""
    visited: set = set()
    queue = incoming.get(node_id, [])[:]
    result = []

    while queue:
        nid = queue.pop(0)
        if nid in visited:
            continue
        visited.add(nid)

        node = node_map.get(nid)
        if node:
            module = node.get("data", {}).get("module") or node.get("module_id") or ""
            if not module.startswith("form."):
                result.append(_node_info(nid, node_map))

        for pred in incoming.get(nid, []):
            if pred not in visited:
                queue.append(pred)

    return list(reversed(result))


def _bfs_successors(node_id: str, outgoing: Dict, node_map: Dict) -> list:
    """BFS to find all downstream nodes."""
    visited: set = set()
    queue = outgoing.get(node_id, [])[:]
    result = []

    while queue:
        nid = queue.pop(0)
        if nid in visited:
            continue
        visited.add(nid)

        node = node_map.get(nid)
        if node:
            result.append(_node_info(nid, node_map))

        for succ in outgoing.get(nid, []):
            if succ not in visited:
                queue.append(succ)

    return result


def _attach_loop_contexts(relations: Dict, loop_node_ids: set, node_map: Dict):
    """Add loopContext to nodes whose predecessors include a loop node."""
    for node_id, rel in relations.items():
        for pred in rel["predecessors"]:
            if pred["id"] not in loop_node_ids:
                continue
            loop_node = node_map.get(pred["id"], {})
            loop_params = loop_node.get("data", {}).get("params") or loop_node.get("params") or {}
            item_alias = loop_params.get("as", "item")
            index_alias = loop_params.get("indexAs", "index")
            rel["loopContext"] = {
                "loopNodeId": pred["id"],
                "variables": [
                    {
                        "path": f"loop.{item_alias}",
                        "label": f"Loop {item_alias.title()}",
                        "expression": f"${{loop.{item_alias}}}",
                    },
                    {
                        "path": f"loop.{index_alias}",
                        "label": f"Loop {index_alias.title()}",
                        "expression": f"${{loop.{index_alias}}}",
                    },
                ],
            }
            break
