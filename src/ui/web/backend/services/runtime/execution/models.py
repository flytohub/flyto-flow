"""
Execution Info Model

Container for execution state and metadata.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.runtime.execution.enums import ExecutionStatus
from services.runtime.execution.redaction import redact_sensitive


class ExecutionInfo:
    """
    Execution state container.

    Holds all information about a workflow execution including:
    - Identifiers (execution_id, workflow_id, user_id)
    - Status and timing (status, start_time, end_time)
    - Progress (current_step, total_steps)
    - Results (result, error, error_step_id)
    - Phase 0 tracking (snapshot, runs_directory, step_hooks, outcome)
    - Execution control (metadata with breakpoints, step_mode, initial_context)

    Usage:
        info = ExecutionInfo(
            execution_id="abc-123",
            workflow_id="workflow-456",
            workflow_name="My Workflow",
            user_id="user-789",
        )
        info.status = ExecutionStatus.RUNNING
        info.start_time = datetime.now(timezone.utc)
    """

    def __init__(
        self,
        execution_id: str,
        workflow_id: str,
        workflow_name: str = "",
        user_id: Optional[str] = None,
        provider_execution_id: Optional[str] = None,
        input_params: Optional[Dict[str, Any]] = None,
    ):
        """Initialize execution state with identifiers and default values."""
        # Identifiers
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.user_id = user_id
        self.provider_execution_id = provider_execution_id  # ID in data provider (Firebase)
        self.sqlite_execution_id = execution_id  # Same as execution_id for SQLite
        self.input_params = input_params or {}

        # Status and timing
        self.status = ExecutionStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Progress
        self.current_step: int = 0
        self.total_steps: int = 0

        # Results
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.error_step_id: Optional[str] = None

        # Runtime references (not serialized)
        self.engine: Optional[Any] = None
        self.task: Optional[asyncio.Task] = None

        # Phase 0: Snapshot and tracking
        self.snapshot: Optional[Any] = None
        self.runs_directory: Optional[Any] = None
        self.step_hooks: Optional[Any] = None
        self.outcome: Optional[Any] = None

        # P0: Execution control metadata (breakpoints, step_mode, initial_context)
        self.metadata: Dict[str, Any] = {}

        # Node-level state tracking (for frontend rendering)
        self.node_states: Dict[str, str] = {}  # node_id -> "pending"|"running"|"completed"|"failed"
        self.active_node_id: Optional[str] = None
        self.node_order: List[str] = []  # Ordered list of node IDs from workflow steps

        # Node-level timing tracking (for duration display)
        self.node_timings: Dict[str, Dict[str, Any]] = {}  # node_id -> {started_at, completed_at, duration_ms}

        # Node-level inputs tracking (for diff view)
        self.node_inputs: Dict[str, Any] = {}  # node_id -> input params

        # Node-level outputs tracking (for diff view)
        self.node_outputs: Dict[str, Any] = {}  # node_id -> output data

        # Display outputs (collected from __display__: true results, no truncation)
        self.display_outputs: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        # Calculate progress percentage
        progress_percent = 0
        if self.total_steps > 0:
            progress_percent = int((self.current_step / self.total_steps) * 100)

        # Get completed node IDs from node_states
        completed_node_ids = [
            node_id for node_id, state in self.node_states.items()
            if state == "completed"
        ]

        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "user_id": self.user_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            # Legacy fields (keep for backward compatibility)
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            # New fields for frontend rendering
            "node_states": self.node_states,
            "node_timings": self.node_timings,  # {node_id: {started_at, completed_at, duration_ms}}
            "node_inputs": redact_sensitive(self.node_inputs),    # {node_id: input_params} for diff view
            "node_outputs": redact_sensitive(self.node_outputs),  # {node_id: output_data} for diff view
            "active_node_id": self.active_node_id,
            "completed_node_ids": completed_node_ids,
            "progress": {
                "current": self.current_step,
                "total": self.total_steps,
                "percent": progress_percent,
            },
            "input_params": redact_sensitive(self.input_params),
            "result": redact_sensitive(self._safe_serialize(self.result)),
            "error": self.error,
            "error_step_id": self.error_step_id,
            "display_outputs": redact_sensitive(self.display_outputs),
            "has_browser": bool(self.metadata.get("has_browser")),
        }

    def _safe_serialize(self, obj: Any) -> Any:
        """
        Safely serialize result, handling non-serializable objects.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable version of the object
        """
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, dict):
            return {k: self._safe_serialize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._safe_serialize(item) for item in obj]
        # For non-serializable objects, return a string representation
        try:
            if hasattr(obj, '__dict__'):
                return f"<{type(obj).__name__}>"
            return str(obj)
        except (TypeError, ValueError):
            return f"<{type(obj).__name__}>"
