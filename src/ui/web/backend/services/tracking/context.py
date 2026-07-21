"""
Tracking Context

Context manager for tracked values during workflow execution.
"""

from typing import Any, Dict, List, Optional

from services.tracking.models import ValueOrigin
from services.tracking.tracked_value import TrackedValue


class TrackingContext:
    """
    Helper class to manage tracked values during workflow execution.

    Integrates with ExecutionContext to provide item-level lineage.
    """

    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self._tracked_vars: Dict[str, TrackedValue] = {}

    def set_tracked(
        self,
        key: str,
        value: Any,
        node_id: str,
        port_id: str = "default",
    ) -> TrackedValue:
        """
        Set a tracked variable.

        Args:
            key: Variable name
            value: Value to store
            node_id: Node that produced this
            port_id: Output port

        Returns:
            The created TrackedValue
        """
        if isinstance(value, TrackedValue):
            # Already tracked, just update transform chain
            tracked = TrackedValue.transform(
                value=value.value,
                source=value,
                transform_node=node_id,
                port_id=port_id,
            )
        else:
            # New tracking
            tracked = TrackedValue.create(
                value=value,
                node_id=node_id,
                port_id=port_id,
                execution_id=self.execution_id,
            )

        self._tracked_vars[key] = tracked
        return tracked

    def get_tracked(self, key: str) -> Optional[TrackedValue]:
        """Get a tracked variable"""
        return self._tracked_vars.get(key)

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get the raw value of a tracked variable"""
        tracked = self._tracked_vars.get(key)
        if tracked:
            return tracked.value
        return default

    def get_origin(self, key: str) -> Optional[ValueOrigin]:
        """Get origin of a tracked variable"""
        tracked = self._tracked_vars.get(key)
        if tracked:
            return tracked.origin
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize all tracked values"""
        return {
            key: tracked.to_dict(include_children=True)
            for key, tracked in self._tracked_vars.items()
        }

    def get_lineage_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all tracked values and their origins.

        Returns a structure suitable for API responses.
        """
        summary = {}
        for key, tracked in self._tracked_vars.items():
            summary[key] = {
                "value_type": type(tracked.value).__name__,
                "value_preview": self._preview_value(tracked.value),
                "origin": tracked.origin.to_dict() if tracked.origin else None,
                "transform_chain": tracked.transform_chain,
                "is_array": isinstance(tracked.value, list),
                "item_count": len(tracked.value) if isinstance(tracked.value, list) else None,
                "item_origins": self._get_item_origins_summary(tracked)
                    if isinstance(tracked.value, list) else None,
            }
        return summary

    def _preview_value(self, value: Any, max_len: int = 50) -> str:
        """Create a preview of a value"""
        if value is None:
            return "null"
        if isinstance(value, str):
            return value[:max_len] + "..." if len(value) > max_len else value
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, list):
            return f"[{len(value)} items]"
        if isinstance(value, dict):
            return f"{{{len(value)} keys}}"
        return str(type(value).__name__)

    def _get_item_origins_summary(
        self,
        tracked: TrackedValue,
    ) -> List[Dict[str, Any]]:
        """Get origin summary for array items"""
        if not tracked.is_composite:
            return []

        summaries = []
        for i in range(len(tracked.value)):
            if i in tracked._tracked_children:
                child = tracked._tracked_children[i]
                summaries.append({
                    "index": i,
                    "origin_node": child.origin.node_id if child.origin else None,
                })
            else:
                summaries.append({
                    "index": i,
                    "origin_node": tracked.origin.node_id if tracked.origin else None,
                })
        return summaries
