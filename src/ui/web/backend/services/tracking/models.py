"""
Tracked Value Models

Dataclasses for value origin metadata.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ValueOrigin:
    """
    Origin metadata for a tracked value.

    Describes where a value came from in the execution graph.
    """
    # Source identification
    node_id: str
    port_id: str = "default"
    execution_id: Optional[str] = None

    # Position in array (for array items)
    index: Optional[int] = None

    # Timestamp when value was produced
    timestamp: Optional[str] = None

    # Optional key path for nested values (e.g., "user.address.city")
    key_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "node_id": self.node_id,
            "port_id": self.port_id,
            "execution_id": self.execution_id,
            "index": self.index,
            "timestamp": self.timestamp,
            "key_path": self.key_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValueOrigin":
        """Deserialize from dictionary"""
        return cls(
            node_id=data.get("node_id", "unknown"),
            port_id=data.get("port_id", "default"),
            execution_id=data.get("execution_id"),
            index=data.get("index"),
            timestamp=data.get("timestamp"),
            key_path=data.get("key_path"),
        )
