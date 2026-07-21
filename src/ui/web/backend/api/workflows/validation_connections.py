"""
Workflow Connection Validation

Validates workflow connections before save/execute.
Uses core.validation API as single source of truth.
"""

import logging
from typing import Dict, List, Any

from fastapi import HTTPException

from services.graph_helpers import (
    is_loop_module,
    is_branch_module,
    is_switch_module,
    is_container_module,
    get_target_handle,
)
from services.helpers.workflow_helpers import (
    build_step_node_data,
    generate_edges_from_steps,
    resolve_switch_case_handle,
)
from services.template.workflow_converter import (
    _is_resource_edge,
    _get_source_handle,
    _get_target_handle_from_edge,
    _get_edge_data_type,
)

logger = logging.getLogger(__name__)

# Alias for internal use — _get_target_handle_from_edge was renamed to avoid
# collision with the graph_helpers.get_target_handle (module-based).
_get_target_handle = _get_target_handle_from_edge


def _is_loop_edge(edge: Dict[str, Any]) -> bool:
    """Check if an edge represents a loop connection (iterate/loop-back)."""
    edge_type = (edge.get("type") or "").lower()
    edge_data_type = _get_edge_data_type(edge)
    source_handle = _get_source_handle(edge)
    target_handle = _get_target_handle(edge)
    return (
        edge_type == "loop"
        or edge_data_type in ("loop", "iterate")
        or "loop" in source_handle
        or "loop" in target_handle
    )


def _prepare_nodes_and_edges(workflow_dict: dict):
    """Convert steps to nodes/edges, detect loops, and separate control-flow edges.

    Returns (nodes_for_validation, control_flow_edges, has_loop, resource_source_node_ids).
    """
    nodes = workflow_dict.get("nodes", [])
    edges = workflow_dict.get("edges", [])
    has_loop = workflow_dict.get("has_loop", False)

    # Convert steps format to nodes/edges if needed
    if not nodes and workflow_dict.get("steps"):
        generated_nodes, generated_edges = _convert_steps_to_nodes_edges(workflow_dict.get("steps", []))
        nodes = generated_nodes
        if not edges:
            edges = generated_edges

    # Compute loop presence from nodes (single source of truth)
    if not has_loop:
        for n in nodes:
            module_id = (n.get("module_id") or "").lower()
            if "loop" in module_id or "foreach" in module_id:
                has_loop = True
                break

    # Identify resource nodes by node data (isSubNode flag)
    # Note: HTTP client converts camelCase -> snake_case, so check both
    resource_source_node_ids = set()
    for n in nodes:
        data = n.get("data") or {}
        if data.get("isSubNode") or data.get("is_sub_node"):
            resource_source_node_ids.add(n.get("id"))

    # Filter out special edges that don't affect control flow.
    # Resource edges are identified by their edgeType (from edge.data),
    # not by node metadata — this works regardless of module type.
    control_flow_edges = [
        e for e in edges
        if not _is_loop_edge(e)
        and not _is_resource_edge(e)
        and e.get("source") not in resource_source_node_ids
        and e.get("target") not in resource_source_node_ids
    ]

    # Filter out resource source nodes and normalize module IDs
    from api.workflows.utils import normalize_template_module

    def normalize_node_module(node):
        module_id = (
            node.get("module_id") or
            node.get("moduleId") or
            node.get("data", {}).get("module") or
            node.get("data", {}).get("module_id") or
            node.get("data", {}).get("moduleId") or
            ""
        )
        if not module_id:
            return node
        if not node.get("module_id"):
            node = {**node, "module_id": module_id}
        params = dict(node.get("params") or node.get("data", {}).get("params") or {})
        new_module_id, new_params = normalize_template_module(module_id, {"params": params})
        if new_module_id != module_id or new_params.get("params") != params:
            return {**node, "module_id": new_module_id, "params": new_params.get("params", params)}
        return node

    nodes_for_validation = [
        normalize_node_module(n)
        for n in nodes
        if n.get("id") not in resource_source_node_ids
    ]

    return nodes_for_validation, control_flow_edges, edges, has_loop


def _detect_loop_targets(workflow_dict: dict, all_edges: list, has_loop: bool) -> set:
    """Collect node IDs reachable via loop edges to suppress false-positive errors.

    These nodes appear orphaned because their incoming loop edges are filtered
    from control_flow_edges.
    """
    if not has_loop:
        return set()

    loop_edge_target_ids = set()

    # Source 1: ALL targets of loop edges (iterate + loop-back)
    for edge in all_edges:
        if _is_loop_edge(edge):
            target_id = edge.get("target")
            if target_id:
                loop_edge_target_ids.add(target_id)

    # Source 2: Iterate targets from step data directly (fallback when
    # edges lack proper loop metadata or connections weren't serialized)
    for step in (workflow_dict.get("steps") or []):
        if is_loop_module(step.get("module", "")):
            connections = step.get("connections") or {}
            iterate_raw = connections.get("iterate", [])
            if isinstance(iterate_raw, str):
                iterate_raw = [iterate_raw]
            loop_edge_target_ids.update(t for t in iterate_raw if t)
            target = (step.get("params") or {}).get("target")
            if target:
                loop_edge_target_ids.add(target)

    return loop_edge_target_ids


def _filter_false_positives(result, has_loop: bool):
    """Remove false-positive validation errors caused by loop edge filtering.

    Returns a (possibly new) result with false positives removed.
    """
    if result.valid:
        return result

    NON_BLOCKING_CODES = set()

    def _is_false_positive(err):
        if err.code in NON_BLOCKING_CODES:
            return True
        if has_loop:
            if err.code == "NO_START_NODE":
                return True
            if err.code == "INVALID_START_NODE":
                # Loop body nodes always appear as orphan start nodes because
                # their incoming iterate edges are filtered from control_flow_edges.
                # Suppress all INVALID_START_NODE in loop workflows.
                return True
        return False

    filtered_errors = [
        err for err in result.errors
        if not _is_false_positive(err)
    ]
    if len(filtered_errors) < len(result.errors):
        result = type(result)(
            valid=len(filtered_errors) == 0,
            errors=filtered_errors,
            warnings=result.warnings,
        )

    return result


def _format_validation_result(result) -> dict:
    """Convert core validation result to API response dict."""
    def _fmt_issues(issues):
        return [
            {"code": i.code, "path": i.path, "message": i.message, "meta": i.meta}
            for i in issues
        ]

    if not result.valid:
        return {
            "valid": False,
            "errors": _fmt_issues(result.errors),
            "warnings": _fmt_issues(result.warnings),
        }

    return {
        "valid": True,
        "warnings": _fmt_issues(result.warnings) if result.warnings else [],
    }


def validate_workflow_connections_for_api(workflow_dict: dict) -> dict:
    """
    Validate workflow connections before save/execute.

    Uses core.validation.validate_workflow as single source of truth.
    Cloud does NOT implement validation logic - only calls core API.

    Args:
        workflow_dict: Workflow data with nodes and edges (or steps)

    Returns:
        {"valid": True} or {"valid": False, "errors": [...]}

    Raises:
        HTTPException: If validation service is unavailable in cloud mode
    """
    # Ensure module registry is fully loaded before validation
    try:
        from services.registry_loader import get_module_registry
        get_module_registry()
    except Exception:
        pass

    try:
        from core.validation import validate_workflow
    except ImportError:
        logger.info("Workflow validation deferred to execution worker (core.validation unavailable)")
        return {"valid": True, "warning": "Validation deferred to execution worker"}

    nodes_for_validation, control_flow_edges, all_edges, has_loop = _prepare_nodes_and_edges(workflow_dict)
    # _detect_loop_targets is called for completeness; the false-positive filter
    # uses has_loop flag directly (all INVALID_START_NODE suppressed in loop workflows).
    _detect_loop_targets(workflow_dict, all_edges, has_loop)

    result = validate_workflow(nodes_for_validation, control_flow_edges)
    result = _filter_false_positives(result, has_loop)

    return _format_validation_result(result)


def _normalize_step_node(step: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Normalize a single step dict into a node dict.

    Handles template module pre-normalization (library_id injection)
    and returns a node with id, module_id, params, and data.
    """
    node_id = step.get("id", f"step_{index}")
    module_id = step.get("module", "")
    step_params = step.get("params", {})

    # Pre-normalize template modules in step conversion
    if module_id == "template.invoke" or module_id.startswith("template."):
        if isinstance(step_params, dict):
            template_id = step_params.get("template_id") or step_params.get("templateId")
            if template_id and not step_params.get("library_id"):
                step_params = dict(step_params)
                step_params["library_id"] = template_id

    return {
        "id": node_id,
        "module_id": module_id,
        "params": step_params,
        "data": {"module_id": module_id},
    }


def _build_edge_from_connection(
    source: str, target: str, edge_type: str, module_id: str = "",
) -> Dict[str, Any]:
    """Build one edge dict from a connection specification.

    Args:
        source: Source node ID.
        target: Target node ID.
        edge_type: Connection type — 'iterate', 'done', or any other (default output).
        module_id: Module ID of the source node (used for loop detection).
    """
    if edge_type == "iterate" and is_loop_module(module_id):
        return {
            "id": f"edge_iterate_{source}_{target}",
            "source": source,
            "target": target,
            "type": "loop",
            "sourceHandle": "body_out",
            "targetHandle": "target-top",
            "data": {"edgeType": "iterate"},
        }
    elif edge_type == "done" and is_loop_module(module_id):
        return {
            "id": f"edge_done_{source}_{target}",
            "source": source,
            "target": target,
            "sourceHandle": "done_out",
        }
    else:
        return {
            "id": f"edge_{source}_{target}",
            "source": source,
            "target": target,
            "sourceHandle": "output",
        }


def _convert_steps_to_nodes_edges(steps: List[Dict[str, Any]]) -> tuple:
    """Convert steps format to nodes/edges format"""
    nodes = []
    edges = []

    # First pass: create all nodes
    step_ids = set()
    for i, step in enumerate(steps):
        node = _normalize_step_node(step, i)
        step_ids.add(node["id"])
        nodes.append(node)

    # Collect loop body node IDs (iterate targets) — these should NOT get implicit sequential edges
    loop_body_node_ids = set()
    for step in steps:
        module_id = step.get("module", "")
        if is_loop_module(module_id) and step.get("connections"):
            for conn_type, targets in step["connections"].items():
                if conn_type == "iterate":
                    target_list = targets if isinstance(targets, list) else [targets] if isinstance(targets, str) else []
                    loop_body_node_ids.update(target_list)
        # Also check params.target for backward compat
        if is_loop_module(module_id) and step.get("params", {}).get("target"):
            loop_body_node_ids.add(step["params"]["target"])

    # Second pass: create edges
    for i, step in enumerate(steps):
        node_id = step.get("id", f"step_{i}")
        module_id = step.get("module", "")
        params = step.get("params", {})

        # Create edges from connections or implicit order
        if step.get("connections"):
            for conn_type, targets in step["connections"].items():
                target_list = targets if isinstance(targets, list) else [targets] if isinstance(targets, str) else []

                for target in target_list:
                    edges.append(
                        _build_edge_from_connection(node_id, target, conn_type, module_id)
                    )
        else:
            # Check for loop module with params.target (backward compatibility)
            has_loop_target = False
            if is_loop_module(module_id) and params.get("target"):
                loop_target = params.get("target")
                if loop_target in step_ids:
                    has_loop_target = True
                    # Loop node connects to its body start node via iterate port
                    edges.append({
                        "id": f"edge_loop_{node_id}_{loop_target}",
                        "source": node_id,
                        "target": loop_target,
                        "type": "loop",
                        "sourceHandle": "body_out",
                        "targetHandle": "target-top",
                        "data": {"edgeType": "iterate"},
                    })

            # Implicit sequential order (only for non-last steps)
            # Skip if: loop module with explicit target, or this is a loop body node
            # (loop body nodes' flow is controlled by the loop, not sequential order)
            if i < len(steps) - 1 and not has_loop_target and node_id not in loop_body_node_ids:
                next_id = steps[i + 1].get("id", f"step_{i + 1}")
                edges.append({
                    "id": f"edge_{i}",
                    "source": node_id,
                    "target": next_id,
                    "sourceHandle": "output"
                })

    return nodes, edges


def validate_workflow_start_nodes(workflow_dict: dict) -> dict:
    """
    Validate only the start nodes of a workflow.

    Quick validation for UI feedback.
    """
    try:
        from core.validation import validate_start
    except ImportError:
        return {"valid": True, "warning": "Validation unavailable"}

    nodes = workflow_dict.get("nodes", [])
    edges = workflow_dict.get("edges", [])

    if not nodes and workflow_dict.get("steps"):
        nodes, edges = _convert_steps_to_nodes_edges(workflow_dict.get("steps", []))

    # Filter out loop edges for start node detection
    non_loop_edges = [e for e in edges if e.get("type") != "loop"]

    errors = validate_start(nodes, non_loop_edges)

    if errors:
        return {
            "valid": False,
            "errors": [
                {
                    "code": err.code,
                    "path": err.path,
                    "message": err.message,
                    "meta": err.meta,
                }
                for err in errors
            ]
        }

    return {"valid": True}
