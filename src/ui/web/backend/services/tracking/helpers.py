"""
Tracked Value Helpers

Convenience functions for working with tracked values.
"""

from typing import Any, List, Optional

from services.tracking.models import ValueOrigin
from services.tracking.tracked_value import TrackedValue


def track_output(
    value: Any,
    node_id: str,
    port_id: str = "default",
    execution_id: Optional[str] = None,
) -> TrackedValue:
    """
    Convenience function to create a tracked output value.

    Use this in module execution to wrap output with tracking.
    """
    return TrackedValue.create(
        value=value,
        node_id=node_id,
        port_id=port_id,
        execution_id=execution_id,
    )


def unwrap_value(value: Any) -> Any:
    """
    Unwrap a value if it's tracked, otherwise return as-is.

    Safe to call on any value.
    """
    if isinstance(value, TrackedValue):
        return value.unwrap()
    return value


def is_tracked(value: Any) -> bool:
    """Check if a value is tracked"""
    return isinstance(value, TrackedValue)


def get_value_origin(value: Any) -> Optional[ValueOrigin]:
    """Get origin metadata if value is tracked"""
    if isinstance(value, TrackedValue):
        return value.origin
    return None


def get_item_origins(values: List[Any]) -> List[Optional[ValueOrigin]]:
    """Get origins for each item in a list"""
    origins = []
    for v in values:
        if isinstance(v, TrackedValue):
            origins.append(v.origin)
        else:
            origins.append(None)
    return origins
