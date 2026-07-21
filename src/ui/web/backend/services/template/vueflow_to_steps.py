"""
VueFlow to Steps Converter

Converts VueFlow nodes/edges from the frontend canvas back to
backend workflow steps format for execution.
"""

import logging
from typing import Dict, List, Any, Optional

from services.graph_helpers import (
    is_loop_module,
    is_branch_module,
    is_switch_module,
    is_container_module,
    is_breakpoint_module,
)
from services.template.converter_utils import (
    _get_source_handle,
    _is_resource_edge,
    classify_resource_edge,
)

logger = logging.getLogger(__name__)


def convert_vueflow_to_steps(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Convert VueFlow elements to backend steps format.

    Args:
        nodes: VueFlow node objects
        edges: VueFlow edge objects

    Returns:
        {"steps": [...]}
    """
    if not nodes:
        return {"steps": []}

    # Build resource edges map: agent_node_id -> { model, memory, tools }
    resource_edges_map = _build_resource_edges_map(nodes, edges)

    # Build edges-by-source map for connection extraction (exclude resource edges)
    edges_by_source = {}
    for edge in edges:
        if _is_resource_edge(edge):
            continue
        source_id = edge.get("source")
        target_id = edge.get("target")
        if not source_id or not target_id:
            continue
        edges_by_source.setdefault(source_id, []).append(edge)

    # Convert nodes to steps
    steps = []

    for index, node in enumerate(nodes):
        node_data = node.get("data", {})
        module_id = _normalize_module_id(node_data) or "unknown"

        # Handle params
        params = node_data.get("params", {})
        if isinstance(params, str):
            try:
                import json
                params = json.loads(params)
            except Exception:
                params = {}
        if not isinstance(params, dict):
            params = {}

        # Create step
        position = node.get("position", {})
        step = {
            "id": node.get("id"),
            "module": module_id,
            "label": node_data.get("label") or node.get("label") or node.get("id"),
            "params": {**params},
            "position_x": round(position.get("x", 0)),
            "position_y": round(position.get("y", 0)),
            "order_index": index
        }

        # Extract connections from edges for flow control nodes
        connections_from_edges = _extract_connections_from_edges(
            node.get("id"),
            module_id,
            params,
            edges_by_source
        )

        node_connections = node_data.get("connections")
        if connections_from_edges:
            step["connections"] = connections_from_edges
        elif node_connections and isinstance(node_connections, dict) and len(node_connections) > 0:
            step["connections"] = {**node_connections}

        # Handle AI Agent resources
        resources = resource_edges_map.get(node.get("id"))
        if resources:
            step["resources"] = resources

        # Handle Container/Sandbox nodes
        if is_container_module(module_id):
            if not step["params"].get("subflow"):
                step["params"]["subflow"] = {"nodes": [], "edges": []}
            if step["params"].get("inherit_context") is None:
                step["params"]["inherit_context"] = True

        # Add optional fields
        optional_fields = [
            "description", "output", "when", "on_error",
            "retry", "timeout", "parallel", "foreach", "as"
        ]
        for field in optional_fields:
            value = node_data.get(field)
            if value is not None:
                step[field] = value

        steps.append(step)

    return {"steps": steps}


def _build_resource_edges_map(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """Build resource edges map: agent_node_id -> { model, memory, tools }.

    Classification is based solely on targetHandle via classify_resource_edge().
    No module-name heuristic — targetHandle is always set by the frontend.
    """
    resource_edges_map: Dict[str, Dict[str, Any]] = {}
    for edge in edges:
        res_type = classify_resource_edge(edge)
        if res_type is None:
            continue

        target_id = edge["target"]  # AI Agent
        source_id = edge["source"]  # Resource node

        if target_id not in resource_edges_map:
            resource_edges_map[target_id] = {}

        if res_type == "tools":
            current = resource_edges_map[target_id].get(res_type)
            if current is None:
                resource_edges_map[target_id][res_type] = source_id
            elif isinstance(current, list):
                current.append(source_id)
            else:
                resource_edges_map[target_id][res_type] = [current, source_id]
        else:
            resource_edges_map[target_id][res_type] = source_id

    return resource_edges_map


def _normalize_module_id(node_data: Dict[str, Any]) -> str:
    """Normalize module ID from various formats."""
    candidates = [
        node_data.get("module"),
        node_data.get("module_id"),
        node_data.get("moduleId"),
    ]
    module_obj = node_data.get("module")
    if isinstance(module_obj, dict):
        candidates.extend([
            module_obj.get("module_id"),
            module_obj.get("moduleId"),
            module_obj.get("id"),
            module_obj.get("module"),
        ])
    for item in candidates:
        if not item:
            continue
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            resolved = item.get("module_id") or item.get("moduleId") or item.get("id") or item.get("module")
            if resolved:
                return resolved
    return ""


def _sanitize_params(module_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Filter params against module's registered params_schema.

    - Keys that match schema -> keep
    - Keys that don't match -> discard
    - Duplicate keys -> YAML dict already deduplicates (last wins)

    Falls back to returning params as-is if module not found in registry.
    """
    if not module_id or not params:
        return params
    try:
        from core.modules.registry import ModuleRegistry
    except ImportError:
        return params

    meta = ModuleRegistry.get_metadata(module_id)
    if not meta:
        return params

    schema = meta.get('params_schema', {})
    if not schema:
        return params

    # Support JSON Schema style: {type, properties, required}
    if isinstance(schema, dict) and 'properties' in schema:
        valid_keys = set(schema['properties'].keys())
    else:
        valid_keys = set(schema.keys())

    if not valid_keys:
        return params

    filtered = {k: v for k, v in params.items() if k in valid_keys or k == '_tvars'}
    dropped = set(params.keys()) - valid_keys
    if dropped:
        logger.info(f"[WorkflowConverter] Dropped unknown params for {module_id}: {dropped}")
    return filtered


def _extract_connections_from_edges(
    node_id: str,
    module_id: str,
    params: Dict[str, Any],
    edges_by_source: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, List[str]]:
    """Extract connections from edges for flow control nodes."""
    connections: Dict[str, List[str]] = {}
    outgoing_edges = edges_by_source.get(node_id, [])

    for edge in outgoing_edges:
        handle = _get_source_handle(edge)
        target_id = edge.get("target")

        # Error handle — applicable to any node type
        if handle == "source-error":
            connections.setdefault("error", []).append(target_id)
            continue

        if is_loop_module(module_id):
            if handle == "body_out" or "item" in handle:
                connections["iterate"] = [target_id]
            elif handle == "done_out" or "done" in handle:
                connections["done"] = [target_id]

        elif is_branch_module(module_id):
            if "true" in handle:
                connections["true"] = [target_id]
            elif "false" in handle:
                connections["false"] = [target_id]

        elif is_switch_module(module_id):
            if "default" in handle:
                connections["default"] = [target_id]
            else:
                case_key = _resolve_switch_case_key(edge, params)
                if case_key:
                    connections[case_key] = [target_id]

        elif is_breakpoint_module(module_id):
            if "approved" in handle:
                connections.setdefault("approved", []).append(target_id)
            elif "rejected" in handle:
                connections.setdefault("rejected", []).append(target_id)
            elif "timeout" in handle:
                connections.setdefault("timeout", []).append(target_id)
            else:
                connections.setdefault("approved", []).append(target_id)

    return connections


def _resolve_switch_case_key(edge: Dict[str, Any], params: Dict[str, Any]) -> Optional[str]:
    """Resolve edge to switch case key."""
    handle = _get_source_handle(edge)
    edge_case_id = None
    if isinstance(edge.get("data"), dict):
        edge_case_id = (
            edge["data"].get("caseId") or edge["data"].get("caseKey")
            or edge["data"].get("case_id") or edge["data"].get("case_key")
        )

    if handle.startswith("source-case-"):
        return f"case:{handle.replace('source-case-', '')}"

    if handle == "source-cases":
        if edge_case_id:
            return f"case:{edge_case_id}"
        cases = params.get("cases") if isinstance(params, dict) else None
        if isinstance(cases, list) and len(cases) == 1 and cases[0].get("id"):
            return f"case:{cases[0]['id']}"

    return None
