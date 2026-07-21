"""
Tracked Value - Item-Level Data Lineage

DEPRECATED: This module has been split into the tracking/ package.
Import from services.tracking instead.

This file is kept for backwards compatibility.
"""

import warnings

warnings.warn(
    "tracked_value module is deprecated. "
    "Import from services.tracking instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export all public APIs from the new package
from services.tracking import (
    # Models
    ValueOrigin,
    # TrackedValue
    TrackedValue,
    # Helpers
    get_item_origins,
    get_value_origin,
    is_tracked,
    track_output,
    unwrap_value,
    # Context
    TrackingContext,
)

__all__ = [
    # Models
    "ValueOrigin",
    # TrackedValue
    "TrackedValue",
    # Helpers
    "get_item_origins",
    "get_value_origin",
    "is_tracked",
    "track_output",
    "unwrap_value",
    # Context
    "TrackingContext",
]
