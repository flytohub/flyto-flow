"""
Tracked Value Class

TrackedValue wrapper that preserves data lineage metadata.
"""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from services.tracking.models import ValueOrigin


@dataclass
class TrackedValue:
    """
    A value wrapped with lineage tracking metadata.

    TrackedValue wraps any Python value and tracks:
    - Where it originally came from (origin)
    - What transformations it went through (transform_chain)
    - Nested tracking for arrays and objects
    """

    # The actual value
    value: Any

    # Origin metadata
    origin: Optional[ValueOrigin] = None

    # Chain of nodes that transformed this value
    transform_chain: List[str] = field(default_factory=list)

    # For nested objects: tracked children
    _tracked_children: Dict[Union[str, int], "TrackedValue"] = field(
        default_factory=dict, repr=False
    )

    # Whether this is a composite value with nested tracking
    is_composite: bool = False

    @classmethod
    def create(
        cls,
        value: Any,
        node_id: str,
        port_id: str = "default",
        execution_id: Optional[str] = None,
        index: Optional[int] = None,
        key_path: Optional[str] = None,
    ) -> "TrackedValue":
        """Create a new tracked value with origin metadata."""
        origin = ValueOrigin(
            node_id=node_id,
            port_id=port_id,
            execution_id=execution_id,
            index=index,
            timestamp=datetime.now(timezone.utc).isoformat(),
            key_path=key_path,
        )

        tracked = cls(
            value=value,
            origin=origin,
            transform_chain=[node_id],
        )

        # Create nested tracking for arrays and objects
        if isinstance(value, list):
            tracked.is_composite = True
            for i, item in enumerate(value):
                tracked._tracked_children[i] = cls.create(
                    value=item,
                    node_id=node_id,
                    port_id=port_id,
                    execution_id=execution_id,
                    index=i,
                    key_path=f"[{i}]" if not key_path else f"{key_path}[{i}]",
                )
        elif isinstance(value, dict):
            tracked.is_composite = True
            for key, val in value.items():
                tracked._tracked_children[key] = cls.create(
                    value=val,
                    node_id=node_id,
                    port_id=port_id,
                    execution_id=execution_id,
                    key_path=key if not key_path else f"{key_path}.{key}",
                )

        return tracked

    @classmethod
    def transform(
        cls,
        value: Any,
        source: "TrackedValue",
        transform_node: str,
        port_id: str = "default",
    ) -> "TrackedValue":
        """Create a transformed value that preserves original lineage."""
        # Copy origin from source
        origin = deepcopy(source.origin) if source.origin else None

        # Extend transform chain
        chain = source.transform_chain.copy()
        if transform_node not in chain:
            chain.append(transform_node)

        tracked = cls(
            value=value,
            origin=origin,
            transform_chain=chain,
        )

        # Handle nested transformation
        if isinstance(value, list) and source.is_composite:
            tracked.is_composite = True
            for i, item in enumerate(value):
                if i in source._tracked_children:
                    tracked._tracked_children[i] = cls.transform(
                        value=item,
                        source=source._tracked_children[i],
                        transform_node=transform_node,
                    )
        elif isinstance(value, dict) and source.is_composite:
            tracked.is_composite = True
            for key, val in value.items():
                if key in source._tracked_children:
                    tracked._tracked_children[key] = cls.transform(
                        value=val,
                        source=source._tracked_children[key],
                        transform_node=transform_node,
                    )

        return tracked

    @classmethod
    def merge(
        cls,
        values: List["TrackedValue"],
        merge_node: str,
        port_id: str = "default",
    ) -> "TrackedValue":
        """Merge multiple tracked values into one array."""
        merged_value = [tv.value for tv in values]

        # Collect all unique origins
        all_origins = []
        for tv in values:
            if tv.origin and tv.origin.node_id not in [o.node_id for o in all_origins]:
                all_origins.append(tv.origin)

        # Create merged tracked value
        primary_origin = all_origins[0] if all_origins else None

        tracked = cls(
            value=merged_value,
            origin=primary_origin,
            transform_chain=[merge_node],
            is_composite=True,
        )

        # Preserve individual item origins
        for i, tv in enumerate(values):
            tracked._tracked_children[i] = tv

        return tracked

    @classmethod
    def wrap(cls, value: Any) -> "TrackedValue":
        """Wrap a raw value without origin information."""
        return cls(value=value)

    def unwrap(self) -> Any:
        """Get the raw value without tracking metadata."""
        return self.value

    def get_item_origin(self, index: int) -> Optional[ValueOrigin]:
        """Get origin for a specific array item."""
        if index in self._tracked_children:
            return self._tracked_children[index].origin
        return self.origin

    def get_field_origin(self, key: str) -> Optional[ValueOrigin]:
        """Get origin for a specific object field."""
        if key in self._tracked_children:
            return self._tracked_children[key].origin
        return self.origin

    def get_path_origin(self, path: str) -> Optional[ValueOrigin]:
        """Get origin for a nested path."""
        parts = self._parse_path(path)
        current = self

        for part in parts:
            if isinstance(part, int):
                if part in current._tracked_children:
                    current = current._tracked_children[part]
                else:
                    return current.origin
            elif isinstance(part, str):
                if part in current._tracked_children:
                    current = current._tracked_children[part]
                else:
                    return current.origin

        return current.origin

    def _parse_path(self, path: str) -> List[Union[str, int]]:
        """Parse a path string into components"""
        parts = []
        for part in re.split(r'\.|\[|\]', path):
            part = part.strip()
            if not part:
                continue
            try:
                parts.append(int(part))
            except ValueError:
                parts.append(part)
        return parts

    def to_dict(self, include_children: bool = False) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "value": self._serialize_value(self.value),
            "origin": self.origin.to_dict() if self.origin else None,
            "transform_chain": self.transform_chain,
            "is_composite": self.is_composite,
        }

        if include_children and self._tracked_children:
            result["children"] = {
                str(k): v.to_dict(include_children=True)
                for k, v in self._tracked_children.items()
            }

        return result

    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for JSON"""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, list):
            return [self._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        return str(value)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrackedValue":
        """Deserialize from dictionary"""
        tracked = cls(
            value=data.get("value"),
            origin=ValueOrigin.from_dict(data["origin"]) if data.get("origin") else None,
            transform_chain=data.get("transform_chain", []),
            is_composite=data.get("is_composite", False),
        )

        # Restore children if present
        if "children" in data:
            for key, child_data in data["children"].items():
                try:
                    k = int(key)
                except ValueError:
                    k = key
                tracked._tracked_children[k] = cls.from_dict(child_data)

        return tracked

    def __repr__(self) -> str:
        origin_str = f" from {self.origin.node_id}" if self.origin else ""
        return f"TrackedValue({self.value!r}{origin_str})"
