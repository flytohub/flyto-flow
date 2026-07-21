"""
Workflow Converter Service

Backward compatibility — split into converter_helpers, steps_to_vueflow, vueflow_to_steps.

Usage:
    from services.template.workflow_converter import WorkflowConverter

    # Steps -> VueFlow
    vueflow = WorkflowConverter.steps_to_vueflow(steps)

    # VueFlow -> Steps
    steps = WorkflowConverter.vueflow_to_steps(nodes, edges)

    # Auto-detect and validate
    result = WorkflowConverter.validate_and_convert(workflow_data)
"""

from typing import Dict, List, Any

from services.template.converter_helpers import *  # noqa: F401,F403
from services.template.steps_to_vueflow import (  # noqa: F401
    convert_steps_to_vueflow as _s2v,
    _auto_detect_iterate_connections,
    _sort_steps_for_layout,
    _create_node,
    _reposition_resource_nodes,
)
from services.template.vueflow_to_steps import (  # noqa: F401
    convert_vueflow_to_steps as _v2s,
    _normalize_module_id,
    _sanitize_params,
    _extract_connections_from_edges,
    _resolve_switch_case_key,
)


class WorkflowConverter:
    """
    Unified workflow format converter.

    Provides bidirectional conversion between:
    - Steps format (backend/execution)
    - VueFlow format (frontend/canvas)
    """

    @staticmethod
    def steps_to_vueflow(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert backend steps to VueFlow-compatible format."""
        return _s2v(steps)

    @staticmethod
    def vueflow_to_steps(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert VueFlow elements to backend steps format."""
        return _v2s(nodes, edges)

    # Delegate private methods for backward compatibility
    _auto_detect_iterate_connections = staticmethod(_auto_detect_iterate_connections)
    _sort_steps_for_layout = staticmethod(_sort_steps_for_layout)
    _create_node = staticmethod(_create_node)
    _reposition_resource_nodes = staticmethod(_reposition_resource_nodes)
    _normalize_module_id = staticmethod(_normalize_module_id)
    _sanitize_params = staticmethod(_sanitize_params)
    _extract_connections_from_edges = staticmethod(_extract_connections_from_edges)
    _resolve_switch_case_key = staticmethod(_resolve_switch_case_key)

    @staticmethod
    def validate_and_convert(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Auto-detect format, validate, and convert workflow data.

        Args:
            workflow_data: Workflow data in either steps or nodes/edges format

        Returns:
            {
                "steps": [...],
                "nodes": [...],
                "edges": [...],
                "format": "steps" | "vueflow",
                "valid": bool
            }
        """
        has_nodes = bool(workflow_data.get("nodes"))
        has_steps = bool(workflow_data.get("steps"))

        result = {
            "valid": True,
            "format": None,
            "steps": [],
            "nodes": [],
            "edges": []
        }

        if has_nodes:
            # VueFlow format -> convert to steps
            result["format"] = "vueflow"
            result["nodes"] = workflow_data.get("nodes", [])
            result["edges"] = workflow_data.get("edges", [])

            steps_result = WorkflowConverter.vueflow_to_steps(
                result["nodes"],
                result["edges"]
            )
            result["steps"] = steps_result.get("steps", [])

        elif has_steps:
            # Steps format -> convert to VueFlow
            result["format"] = "steps"
            result["steps"] = workflow_data.get("steps", [])

            vueflow_result = WorkflowConverter.steps_to_vueflow(result["steps"])
            result["nodes"] = vueflow_result.get("nodes", [])
            result["edges"] = vueflow_result.get("edges", [])

        else:
            result["valid"] = False

        return result


# Convenience functions
def steps_to_vueflow(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert steps to VueFlow format."""
    return WorkflowConverter.steps_to_vueflow(steps)


def vueflow_to_steps(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert VueFlow to steps format."""
    return WorkflowConverter.vueflow_to_steps(nodes, edges)


# Re-export helpers used by validation.py and other callers
def convert_steps_to_vueflow(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert steps to VueFlow format. Alias for API layer compatibility."""
    return WorkflowConverter.steps_to_vueflow(steps)


def convert_vueflow_to_steps(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert VueFlow to steps format. Alias for API layer compatibility."""
    return WorkflowConverter.vueflow_to_steps(nodes, edges)
