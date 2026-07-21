"""
Execution Context Package

Manages execution state during workflow runs:
- Variable scopes (workflow, node, foreach)
- Node output tracking with port mappings
- Event routing for control flow
- Subflow stack for nested execution
- Item-level data lineage tracking (TrackedValue)
"""

from services.runtime.context.models import (
    ScopeType,
    EdgeType,
    VariableScope,
    PortOutput,
    NodeOutput,
    SubflowFrame,
)
from services.runtime.context.scope import ScopeManager
from services.runtime.context.tracking import OutputTracker
from services.runtime.context.subflow import SubflowManager
from services.runtime.context.resource import ResourceInjector
from services.runtime.context.helpers import create_node_output, parse_module_result
from services.runtime.context.context import ExecutionContext

__all__ = [
    # Models
    "ScopeType",
    "EdgeType",
    "VariableScope",
    "PortOutput",
    "NodeOutput",
    "SubflowFrame",
    # Components
    "ScopeManager",
    "OutputTracker",
    "SubflowManager",
    "ResourceInjector",
    # Helpers
    "create_node_output",
    "parse_module_result",
    # Main class
    "ExecutionContext",
]
