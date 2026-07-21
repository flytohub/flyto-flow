"""
Output and Lineage Tracking

Node output tracking and item-level lineage for workflow execution.
"""

import logging
from typing import Any, Dict, List, Optional

from services.runtime.context.models import EdgeType, NodeOutput, PortOutput

logger = logging.getLogger(__name__)


class OutputTracker:
    """Tracks node outputs and provides lineage information."""

    def __init__(self, enable_tracking: bool = True, execution_id: Optional[str] = None):
        """Initialize output tracking, resource values, and lineage state."""
        self._enable_tracking = enable_tracking
        self._execution_id = execution_id

        # Node output tracking
        self._node_outputs: Dict[str, NodeOutput] = {}
        self._output_history: List[NodeOutput] = []

        # Event routing
        self._last_event: Optional[str] = None
        self._last_node_id: Optional[str] = None

        # Resource port connections (node_id.port_id -> value)
        self._resource_values: Dict[str, Any] = {}

        # Item-level lineage tracking
        self._tracked_outputs: Dict[str, Dict[str, Any]] = {}  # node_id -> port_id -> TrackedValue

    @property
    def last_event(self) -> Optional[str]:
        """Get the last event emitted."""
        return self._last_event

    @property
    def last_node_id(self) -> Optional[str]:
        """Get the last node that executed."""
        return self._last_node_id

    @property
    def node_outputs(self) -> Dict[str, NodeOutput]:
        """Get all node outputs."""
        return self._node_outputs

    @property
    def output_history(self) -> List[NodeOutput]:
        """Get output history."""
        return self._output_history

    @property
    def resource_values(self) -> Dict[str, Any]:
        """Get resource values."""
        return self._resource_values

    @property
    def tracked_outputs(self) -> Dict[str, Dict[str, Any]]:
        """Get tracked outputs."""
        return self._tracked_outputs

    def record_node_output(self, output: NodeOutput) -> None:
        """Record output from a node execution."""
        self._node_outputs[output.node_id] = output
        self._output_history.append(output)
        self._last_event = output.event
        self._last_node_id = output.node_id

        # Store resource port values for injection
        for port_id, port_output in output.outputs.items():
            if port_output.edge_type == EdgeType.RESOURCE:
                key = f"{output.node_id}.{port_id}"
                self._resource_values[key] = port_output.value

        # Track outputs for item-level lineage
        if self._enable_tracking:
            self._track_node_outputs(output)

        logger.debug(
            f"Recorded output for {output.node_id}: event={output.event}, "
            f"ports={list(output.outputs.keys())}"
        )

    def _track_node_outputs(self, output: NodeOutput) -> None:
        """Create TrackedValue wrappers for node outputs."""
        from services.tracked_value import track_output

        if output.node_id not in self._tracked_outputs:
            self._tracked_outputs[output.node_id] = {}

        for port_id, port_output in output.outputs.items():
            tracked = track_output(
                value=port_output.value,
                node_id=output.node_id,
                port_id=port_id,
                execution_id=self._execution_id,
            )
            self._tracked_outputs[output.node_id][port_id] = tracked

    def get_node_output(self, node_id: str) -> Optional[NodeOutput]:
        """Get output from a specific node."""
        return self._node_outputs.get(node_id)

    def get_port_value(
        self,
        node_id: str,
        port_id: str,
        default: Any = None,
    ) -> Any:
        """Get specific port value from a node."""
        output = self._node_outputs.get(node_id)
        if output:
            return output.get_port_value(port_id, default)
        return default

    def get_tracked_output(
        self,
        node_id: str,
        port_id: str = "default",
    ) -> Optional[Any]:
        """Get tracked output from a specific node/port."""
        node_outputs = self._tracked_outputs.get(node_id)
        if node_outputs:
            return node_outputs.get(port_id)
        return None

    def get_value_origin(
        self,
        node_id: str,
        port_id: str = "default",
    ) -> Optional[Any]:
        """Get origin metadata for a node output."""
        tracked = self.get_tracked_output(node_id, port_id)
        if tracked and hasattr(tracked, 'origin'):
            return tracked.origin
        return None

    def get_all_tracked_outputs(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get all tracked outputs for lineage visualization."""
        result = {}
        for node_id, ports in self._tracked_outputs.items():
            result[node_id] = {}
            for port_id, tracked in ports.items():
                if hasattr(tracked, 'to_dict'):
                    result[node_id][port_id] = tracked.to_dict(include_children=False)
                else:
                    result[node_id][port_id] = {"value": tracked}
        return result

    def get_lineage_graph_data(self) -> Dict[str, Any]:
        """Get data for lineage graph visualization."""
        nodes = []
        edges = []

        for node_id, ports in self._tracked_outputs.items():
            for port_id, tracked in ports.items():
                value = tracked.value if hasattr(tracked, 'value') else tracked
                transform_chain = tracked.transform_chain if hasattr(tracked, 'transform_chain') else []

                # Add node
                nodes.append({
                    "id": f"{node_id}.{port_id}",
                    "node_id": node_id,
                    "port_id": port_id,
                    "value_type": type(value).__name__,
                    "is_array": isinstance(value, list),
                    "item_count": len(value) if isinstance(value, list) else None,
                    "transform_chain": transform_chain,
                })

                # Add edges from origin
                if hasattr(tracked, 'origin') and tracked.origin and tracked.origin.node_id != node_id:
                    edges.append({
                        "source": f"{tracked.origin.node_id}.{tracked.origin.port_id}",
                        "target": f"{node_id}.{port_id}",
                        "type": "data_flow",
                    })

        return {
            "nodes": nodes,
            "edges": edges,
        }
