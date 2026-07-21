"""
Execution Context Helpers

Helper functions for creating and parsing node outputs.
"""

from typing import Any, Dict, Optional

from services.runtime.context.models import EdgeType, NodeOutput, PortOutput


def create_node_output(
    node_id: str,
    event: str,
    outputs: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error: Optional[str] = None,
) -> NodeOutput:
    """
    Create a NodeOutput from raw module result.

    Args:
        node_id: The node ID
        event: The __event__ value
        outputs: Dict of port_id -> value
        success: Whether execution succeeded
        error: Error message if failed

    Returns:
        NodeOutput instance
    """
    node_output = NodeOutput(
        node_id=node_id,
        event=event,
        success=success,
        error=error,
    )

    if outputs:
        for port_id, value in outputs.items():
            node_output.outputs[port_id] = PortOutput(
                port_id=port_id,
                value=value,
            )

    return node_output


def parse_module_result(
    node_id: str,
    result: Dict[str, Any],
) -> NodeOutput:
    """
    Parse module execution result into NodeOutput.

    Supports both v1.0 and v1.1 result formats:
    - v1.0: {data: ..., error: ...}
    - v1.1: {__event__: ..., outputs: {port: value}}

    Args:
        node_id: The node ID
        result: Raw module result

    Returns:
        NodeOutput instance
    """
    # v1.1 format with __event__
    if "__event__" in result:
        event = result["__event__"]
        outputs = result.get("outputs", {})
        success = event != "error"
        error = result.get("error") if not success else None

        return create_node_output(
            node_id=node_id,
            event=event,
            outputs=outputs,
            success=success,
            error=error,
        )

    # v1.0 format - convert to v1.1
    success = result.get("ok", True) and not result.get("error")
    event = "success" if success else "error"
    error = result.get("error") if not success else None

    # Map v1.0 data to default port
    outputs = {}
    if "data" in result:
        outputs["default"] = result["data"]
    elif "result" in result:
        outputs["default"] = result["result"]
    elif "value" in result:
        outputs["default"] = result["value"]

    return create_node_output(
        node_id=node_id,
        event=event,
        outputs=outputs,
        success=success,
        error=error,
    )
