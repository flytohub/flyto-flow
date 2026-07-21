"""
Resource Edge Injection

Resource edge data injection for workflow execution.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ResourceInjector:
    """Handles resource edge data injection."""

    def __init__(self, output_tracker):
        """Initialize with an output tracker for resource value lookups."""
        self._output_tracker = output_tracker

    def get_resource_value(self, source_ref: str, default: Any = None) -> Any:
        """
        Get value from resource edge source.

        Args:
            source_ref: "node_id.port_id" format
            default: Default if not found

        Returns:
            The resource value
        """
        return self._output_tracker.resource_values.get(source_ref, default)

    def inject_resource_inputs(
        self,
        node_id: str,
        resource_edges: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Inject resource values from connected edges into node inputs.

        Args:
            node_id: Target node ID
            resource_edges: List of resource edge definitions
                [{source: "node.port", target_param: "param_name"}, ...]

        Returns:
            Dict of injected param values
        """
        injected = {}
        for edge in resource_edges:
            source_ref = edge.get("source")
            target_param = edge.get("target_param")
            if source_ref and target_param:
                value = self.get_resource_value(source_ref)
                if value is not None:
                    injected[target_param] = value
                    logger.debug(
                        f"Injected {source_ref} -> {node_id}.{target_param}"
                    )
        return injected
