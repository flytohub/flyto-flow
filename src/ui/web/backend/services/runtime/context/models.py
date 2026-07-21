"""
Execution Context Models

Enums and data classes for execution context.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ScopeType(str, Enum):
    """Variable scope types"""
    WORKFLOW = "workflow"
    NODE = "node"
    FOREACH = "foreach"
    SUBFLOW = "subflow"


class EdgeType(str, Enum):
    """Edge types from Workflow Spec v1.1"""
    CONTROL = "control"
    RESOURCE = "resource"


@dataclass
class VariableScope:
    """A single variable scope level"""
    scope_type: ScopeType
    scope_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    parent: Optional["VariableScope"] = None

    def get(self, key: str, default: Any = None) -> Any:
        """Get variable, checking parent scopes if not found"""
        if key in self.variables:
            return self.variables[key]
        if self.parent:
            return self.parent.get(key, default)
        return default

    def set(self, key: str, value: Any) -> None:
        """Set variable in this scope"""
        self.variables[key] = value

    def has(self, key: str) -> bool:
        """Check if variable exists in this or parent scope"""
        if key in self.variables:
            return True
        if self.parent:
            return self.parent.has(key)
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Flatten all scopes to single dict (for backward compatibility)"""
        result = {}
        if self.parent:
            result.update(self.parent.to_dict())
        result.update(self.variables)
        return result


@dataclass
class PortOutput:
    """Output from a specific port"""
    port_id: str
    value: Any
    edge_type: EdgeType = EdgeType.CONTROL


@dataclass
class NodeOutput:
    """Complete output from a node execution"""
    node_id: str
    event: str  # The __event__ value determining routing
    outputs: Dict[str, PortOutput] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    def get_port_value(self, port_id: str, default: Any = None) -> Any:
        """Get value from specific port"""
        port = self.outputs.get(port_id)
        return port.value if port else default

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dict"""
        return {
            "node_id": self.node_id,
            "event": self.event,
            "outputs": {
                pid: {"value": p.value, "edge_type": p.edge_type.value}
                for pid, p in self.outputs.items()
            },
            "success": self.success,
            "error": self.error,
        }


@dataclass
class SubflowFrame:
    """Stack frame for subflow execution"""
    subflow_id: str
    parent_node_id: str
    entry_scope: VariableScope
    return_event: str = "success"
