"""
Debug Models

Data classes and enums for debugging workflow executions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class TimelineEvent:
    """A single event in the execution timeline."""

    timestamp: str
    event_type: str  # started, succeeded, failed, skipped, cancelled
    node_id: str
    node_run_id: Optional[str] = None
    step_index: int = 0
    module_id: Optional[str] = None
    duration_ms: Optional[int] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "node_id": self.node_id,
            "node_run_id": self.node_run_id,
            "step_index": self.step_index,
            "module_id": self.module_id,
            "duration_ms": self.duration_ms,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error": self.error,
            "error_category": self.error_category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimelineEvent":
        """Create from dictionary."""
        return cls(
            timestamp=data.get("timestamp", ""),
            event_type=data.get("event_type", ""),
            node_id=data.get("node_id", ""),
            node_run_id=data.get("node_run_id"),
            step_index=data.get("step_index", 0),
            module_id=data.get("module_id"),
            duration_ms=data.get("duration_ms"),
            inputs=data.get("inputs"),
            outputs=data.get("outputs"),
            error=data.get("error"),
            error_category=data.get("error_category"),
        )


@dataclass
class ExecutionTimeline:
    """Timeline view of an execution."""

    execution_id: str
    workflow_id: str
    workflow_name: str
    status: str
    started_at: str
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    total_steps: int = 0
    completed_steps: int = 0
    failed_step: Optional[str] = None
    events: List[TimelineEvent] = field(default_factory=list)
    context_snapshots: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "failed_step": self.failed_step,
            "events": [e.to_dict() for e in self.events],
            "context_snapshots": self.context_snapshots,
        }

    def get_node_events(self, node_id: str) -> List[TimelineEvent]:
        """Get all events for a specific node."""
        return [e for e in self.events if e.node_id == node_id]

    def get_context_at_step(self, step_index: int) -> Dict[str, Any]:
        """Get execution context at a specific step."""
        context = {}
        for event in self.events:
            if event.step_index > step_index:
                break
            if event.event_type == "succeeded" and event.outputs:
                context[f"step_{event.step_index}"] = event.outputs
        return context


class RerunMode(str, Enum):
    """Mode for rerunning an execution."""

    REPLAY = "replay"  # Replay entire execution with same inputs
    REHYDRATE = "rehydrate"  # Inject previous outputs, run from specific node
    RECOMPUTE = "recompute"  # Recompute all dependencies of specific node


@dataclass
class RerunConfig:
    """Configuration for rerunning an execution."""

    mode: RerunMode = RerunMode.REPLAY
    from_node_id: Optional[str] = None  # For REHYDRATE/RECOMPUTE
    use_original_inputs: bool = True
    override_inputs: Optional[Dict[str, Any]] = None
    skip_nodes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mode": self.mode.value,
            "from_node_id": self.from_node_id,
            "use_original_inputs": self.use_original_inputs,
            "override_inputs": self.override_inputs,
            "skip_nodes": self.skip_nodes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RerunConfig":
        """Create from dictionary."""
        mode = data.get("mode", "replay")
        if isinstance(mode, str):
            mode = RerunMode(mode)

        return cls(
            mode=mode,
            from_node_id=data.get("from_node_id"),
            use_original_inputs=data.get("use_original_inputs", True),
            override_inputs=data.get("override_inputs"),
            skip_nodes=data.get("skip_nodes", []),
        )


@dataclass
class RerunResult:
    """Result of a rerun operation."""

    success: bool
    new_execution_id: Optional[str] = None
    original_execution_id: Optional[str] = None
    mode: Optional[RerunMode] = None
    injected_outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "new_execution_id": self.new_execution_id,
            "original_execution_id": self.original_execution_id,
            "mode": self.mode.value if self.mode else None,
            "injected_outputs": self.injected_outputs,
            "error": self.error,
        }
