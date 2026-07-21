"""
Execution Context

Main ExecutionContext class that combines all context components.
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional

from services.runtime.context.models import (
    EdgeType,
    NodeOutput,
    PortOutput,
    ScopeType,
    SubflowFrame,
    VariableScope,
)
from services.runtime.context.scope import ScopeManager
from services.runtime.context.tracking import OutputTracker
from services.runtime.context.subflow import SubflowManager
from services.runtime.context.resource import ResourceInjector


class ExecutionContext:
    """
    Execution context for workflow runs.

    Manages:
    - Hierarchical variable scopes
    - Node output history
    - Event routing state
    - Subflow execution stack

    Usage:
        ctx = ExecutionContext(workflow_id="my_workflow")
        ctx.set_variable("input_url", "https://example.com")

        # After node execution
        ctx.record_node_output(node_output)

        # Get next node based on event
        event = ctx.get_last_event()
    """

    def __init__(
        self,
        workflow_id: str,
        initial_variables: Optional[Dict[str, Any]] = None,
        enable_tracking: bool = True,
    ):
        """Initialize execution context with scope, tracking, and subflow managers."""
        self.workflow_id = workflow_id
        self.execution_id: Optional[str] = None

        # Initialize components
        self._scope_manager = ScopeManager(workflow_id, initial_variables)
        self._output_tracker = OutputTracker(enable_tracking, None)
        self._subflow_manager = SubflowManager(self._scope_manager)
        self._resource_injector = ResourceInjector(self._output_tracker)

        # For backwards compatibility
        self._enable_tracking = enable_tracking

    # ─────────────────────────────────────────────────────────
    # Properties for backwards compatibility
    # ─────────────────────────────────────────────────────────

    @property
    def _root_scope(self) -> VariableScope:
        """Access the root variable scope."""
        return self._scope_manager.root_scope

    @property
    def _current_scope(self) -> VariableScope:
        """Access the current variable scope."""
        return self._scope_manager.current_scope

    @property
    def _node_outputs(self) -> Dict[str, NodeOutput]:
        """Access node outputs by node ID."""
        return self._output_tracker.node_outputs

    @property
    def _output_history(self) -> List[NodeOutput]:
        """Access chronological output history."""
        return self._output_tracker.output_history

    @property
    def _last_event(self) -> Optional[str]:
        """Access the last emitted event."""
        return self._output_tracker.last_event

    @property
    def _last_node_id(self) -> Optional[str]:
        """Access the last executed node ID."""
        return self._output_tracker.last_node_id

    @property
    def _subflow_stack(self) -> List[SubflowFrame]:
        """Access the subflow execution stack."""
        return self._subflow_manager.subflow_stack

    @property
    def _resource_values(self) -> Dict[str, Any]:
        """Access resource edge values."""
        return self._output_tracker.resource_values

    @property
    def _tracked_outputs(self) -> Dict[str, Dict[str, Any]]:
        """Access tracked outputs for lineage."""
        return self._output_tracker.tracked_outputs

    # ─────────────────────────────────────────────────────────
    # Variable Scope Management (delegate to ScopeManager)
    # ─────────────────────────────────────────────────────────

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get variable from current scope chain."""
        return self._scope_manager.get_variable(key, default)

    def set_variable(self, key: str, value: Any) -> None:
        """Set variable in current scope."""
        self._scope_manager.set_variable(key, value)

    def has_variable(self, key: str) -> bool:
        """Check if variable exists in scope chain."""
        return self._scope_manager.has_variable(key)

    def get_all_variables(self) -> Dict[str, Any]:
        """Get all variables flattened (for backward compatibility)."""
        return self._scope_manager.get_all_variables()

    def push_scope(
        self,
        scope_type: ScopeType,
        scope_id: str,
        initial_vars: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Push a new scope level."""
        self._scope_manager.push_scope(scope_type, scope_id, initial_vars)

    def pop_scope(self) -> Optional[VariableScope]:
        """Pop current scope, return to parent."""
        return self._scope_manager.pop_scope()

    def enter_node_scope(self, node_id: str) -> None:
        """Enter node execution scope."""
        self._scope_manager.enter_node_scope(node_id)

    def exit_node_scope(self) -> None:
        """Exit node execution scope."""
        self._scope_manager.exit_node_scope()

    def enter_foreach_scope(
        self,
        item: Any,
        index: int,
        item_var: str = "item",
        index_var: str = "index",
    ) -> None:
        """Enter foreach iteration scope."""
        self._scope_manager.enter_foreach_scope(item, index, item_var, index_var)

    def exit_foreach_scope(self) -> None:
        """Exit foreach iteration scope."""
        self._scope_manager.exit_foreach_scope()

    # ─────────────────────────────────────────────────────────
    # Node Output Tracking (delegate to OutputTracker)
    # ─────────────────────────────────────────────────────────

    def record_node_output(self, output: NodeOutput) -> None:
        """Record output from a node execution."""
        self._output_tracker._execution_id = self.execution_id
        self._output_tracker.record_node_output(output)

    def get_node_output(self, node_id: str) -> Optional[NodeOutput]:
        """Get output from a specific node."""
        return self._output_tracker.get_node_output(node_id)

    def get_port_value(
        self,
        node_id: str,
        port_id: str,
        default: Any = None,
    ) -> Any:
        """Get specific port value from a node."""
        return self._output_tracker.get_port_value(node_id, port_id, default)

    def get_last_event(self) -> Optional[str]:
        """Get the last event emitted."""
        return self._output_tracker.last_event

    def get_last_node_id(self) -> Optional[str]:
        """Get the last node that executed."""
        return self._output_tracker.last_node_id

    # ─────────────────────────────────────────────────────────
    # Item-Level Lineage Tracking
    # ─────────────────────────────────────────────────────────

    def get_tracked_output(
        self,
        node_id: str,
        port_id: str = "default",
    ) -> Optional[Any]:
        """Get tracked output from a specific node/port."""
        return self._output_tracker.get_tracked_output(node_id, port_id)

    def get_value_origin(
        self,
        node_id: str,
        port_id: str = "default",
    ) -> Optional[Any]:
        """Get origin metadata for a node output."""
        return self._output_tracker.get_value_origin(node_id, port_id)

    def get_item_origin(
        self,
        node_id: str,
        port_id: str = "default",
        index: int = 0,
    ) -> Optional[Any]:
        """Get origin for a specific item in an array output."""
        tracked = self.get_tracked_output(node_id, port_id)
        if tracked and hasattr(tracked, 'get_item_origin'):
            return tracked.get_item_origin(index)
        return None

    def get_field_origin(
        self,
        node_id: str,
        port_id: str = "default",
        field: str = "",
    ) -> Optional[Any]:
        """Get origin for a specific field in an object output."""
        tracked = self.get_tracked_output(node_id, port_id)
        if tracked:
            if "." in field or "[" in field:
                if hasattr(tracked, 'get_path_origin'):
                    return tracked.get_path_origin(field)
            elif hasattr(tracked, 'get_field_origin'):
                return tracked.get_field_origin(field)
        return None

    def get_all_tracked_outputs(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get all tracked outputs for lineage visualization."""
        return self._output_tracker.get_all_tracked_outputs()

    def get_lineage_graph_data(self) -> Dict[str, Any]:
        """Get data for lineage graph visualization."""
        return self._output_tracker.get_lineage_graph_data()

    # ─────────────────────────────────────────────────────────
    # Resource Edge Data Injection
    # ─────────────────────────────────────────────────────────

    def get_resource_value(self, source_ref: str, default: Any = None) -> Any:
        """Get value from resource edge source."""
        return self._resource_injector.get_resource_value(source_ref, default)

    def inject_resource_inputs(
        self,
        node_id: str,
        resource_edges: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Inject resource values from connected edges into node inputs."""
        return self._resource_injector.inject_resource_inputs(node_id, resource_edges)

    # ─────────────────────────────────────────────────────────
    # Subflow Management
    # ─────────────────────────────────────────────────────────

    def enter_subflow(
        self,
        subflow_id: str,
        parent_node_id: str,
        input_mapping: Optional[Dict[str, str]] = None,
    ) -> None:
        """Enter a subflow execution."""
        self._subflow_manager.enter_subflow(subflow_id, parent_node_id, input_mapping)

    def exit_subflow(
        self,
        output_mapping: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Exit current subflow."""
        return self._subflow_manager.exit_subflow(output_mapping)

    def get_subflow_depth(self) -> int:
        """Get current subflow nesting depth."""
        return self._subflow_manager.get_subflow_depth()

    def is_in_subflow(self) -> bool:
        """Check if currently in a subflow."""
        return self._subflow_manager.is_in_subflow()

    # ─────────────────────────────────────────────────────────
    # Serialization
    # ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context state."""
        result = {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "variables": self.get_all_variables(),
            "last_event": self._output_tracker.last_event,
            "last_node_id": self._output_tracker.last_node_id,
            "subflow_depth": self.get_subflow_depth(),
            "node_outputs": {
                nid: out.to_dict() for nid, out in self._output_tracker.node_outputs.items()
            },
        }

        # Include item-level tracking data
        if self._enable_tracking and self._output_tracker.tracked_outputs:
            result["tracked_outputs"] = self.get_all_tracked_outputs()

        return result

    def snapshot(self) -> Dict[str, Any]:
        """Create checkpoint snapshot of context state."""
        result = {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "variables": deepcopy(self.get_all_variables()),
            "resource_values": deepcopy(self._output_tracker.resource_values),
            "last_event": self._output_tracker.last_event,
            "last_node_id": self._output_tracker.last_node_id,
            "output_history": [o.to_dict() for o in self._output_tracker.output_history],
            "enable_tracking": self._enable_tracking,
        }

        # Include tracked outputs for lineage restoration
        if self._enable_tracking and self._output_tracker.tracked_outputs:
            result["tracked_outputs"] = {
                node_id: {
                    port_id: tracked.to_dict(include_children=True) if hasattr(tracked, 'to_dict') else {"value": tracked}
                    for port_id, tracked in ports.items()
                }
                for node_id, ports in self._output_tracker.tracked_outputs.items()
            }

        return result

    @classmethod
    def from_snapshot(
        cls,
        snapshot: Dict[str, Any],
    ) -> "ExecutionContext":
        """Restore context from checkpoint snapshot."""
        from services.tracked_value import TrackedValue

        ctx = cls(
            workflow_id=snapshot["workflow_id"],
            initial_variables=snapshot.get("variables", {}),
            enable_tracking=snapshot.get("enable_tracking", True),
        )
        ctx.execution_id = snapshot.get("execution_id")
        ctx._output_tracker._resource_values.update(snapshot.get("resource_values", {}))

        # Restore output history
        for out_dict in snapshot.get("output_history", []):
            output = NodeOutput(
                node_id=out_dict["node_id"],
                event=out_dict["event"],
                success=out_dict.get("success", True),
                error=out_dict.get("error"),
            )
            for pid, pdata in out_dict.get("outputs", {}).items():
                output.outputs[pid] = PortOutput(
                    port_id=pid,
                    value=pdata["value"],
                    edge_type=EdgeType(pdata.get("edge_type", "control")),
                )
            ctx._output_tracker._node_outputs[output.node_id] = output
            ctx._output_tracker._output_history.append(output)

        # Update last event and node
        if ctx._output_tracker._output_history:
            last = ctx._output_tracker._output_history[-1]
            ctx._output_tracker._last_event = last.event
            ctx._output_tracker._last_node_id = last.node_id

        # Restore tracked outputs
        if "tracked_outputs" in snapshot:
            for node_id, ports in snapshot["tracked_outputs"].items():
                ctx._output_tracker._tracked_outputs[node_id] = {}
                for port_id, tracked_data in ports.items():
                    ctx._output_tracker._tracked_outputs[node_id][port_id] = TrackedValue.from_dict(
                        tracked_data
                    )

        return ctx
