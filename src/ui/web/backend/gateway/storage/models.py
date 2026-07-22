"""
SQLite Models

Data classes for execution records.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionStep:
    """Single step execution record."""

    execution_id: str
    step_id: str
    step_index: int = 0
    module_id: str = ""

    status: str = "pending"  # pending, running, success, failure, skipped

    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None

    input_params: Dict[str, Any] = field(default_factory=dict)
    output_data: Any = None
    error_message: Optional[str] = None

    id: Optional[int] = None  # Auto-incremented by SQLite

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "step_id": self.step_id,
            "step_index": self.step_index,
            "module_id": self.module_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "input_params": self.input_params,
            "output_data": self.output_data,
            "error_message": self.error_message,
        }

    @classmethod
    def from_row(cls, row) -> "ExecutionStep":
        """Create from SQLite row."""
        return cls(
            id=row["id"],
            execution_id=row["execution_id"],
            step_id=row["step_id"],
            step_index=row["step_index"] or 0,
            module_id=row["module_id"] or "",
            status=row["status"] or "pending",
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            duration_ms=row["duration_ms"],
            input_params=json.loads(row["input_params"] or "{}"),
            output_data=json.loads(row["output_data"]) if row["output_data"] else None,
            error_message=row["error_message"],
        )


@dataclass
class Execution:
    """Workflow execution record."""

    id: str
    workflow_id: str
    workflow_name: str = ""
    workflow_version: str = "1.0.0"
    workspace_id: Optional[str] = None

    status: str = "pending"  # pending, running, success, failure, cancelled

    started_at: str = ""
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None

    input_params: Dict[str, Any] = field(default_factory=dict)
    result_data: Any = None

    error_message: Optional[str] = None
    error_step_id: Optional[str] = None

    # Snapshot data
    workflow_snapshot: Optional[Dict[str, Any]] = None
    modules_snapshot: Optional[List[Dict[str, Any]]] = None
    env_snapshot: Optional[Dict[str, Any]] = None

    # Outcome classification
    outcome: Optional[str] = None
    outcome_reason: Optional[str] = None
    error_category: Optional[str] = None
    error_fingerprint: Optional[str] = None

    created_at: Optional[str] = None

    # Populated separately
    steps: List[ExecutionStep] = field(default_factory=list)

    def to_dict(self, include_steps: bool = True) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_version": self.workflow_version,
            "workspace_id": self.workspace_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "input_params": self.input_params,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "error_step_id": self.error_step_id,
            "workflow_snapshot": self.workflow_snapshot,
            "modules_snapshot": self.modules_snapshot,
            "env_snapshot": self.env_snapshot,
            "outcome": self.outcome,
            "outcome_reason": self.outcome_reason,
            "error_category": self.error_category,
            "error_fingerprint": self.error_fingerprint,
            "created_at": self.created_at,
        }

        if include_steps:
            result["steps"] = [s.to_dict() for s in self.steps]

        return result

    @classmethod
    def from_row(cls, row) -> "Execution":
        """Create from SQLite row."""
        # Helper to safely get column value
        def get_col(name, default=None):
            try:
                return row[name]
            except (IndexError, KeyError):
                return default

        return cls(
            id=row["id"],
            workflow_id=row["workflow_id"],
            workflow_name=row["workflow_name"] or "",
            workflow_version=row["workflow_version"] or "1.0.0",
            workspace_id=row["workspace_id"],
            status=row["status"] or "pending",
            started_at=row["started_at"] or "",
            finished_at=row["finished_at"],
            duration_ms=row["duration_ms"],
            input_params=json.loads(row["input_params"] or "{}"),
            result_data=json.loads(row["result_data"]) if row["result_data"] else None,
            error_message=row["error_message"],
            error_step_id=row["error_step_id"],
            workflow_snapshot=json.loads(get_col("workflow_snapshot") or "null"),
            modules_snapshot=json.loads(get_col("modules_snapshot") or "null"),
            env_snapshot=json.loads(get_col("env_snapshot") or "null"),
            outcome=get_col("outcome"),
            outcome_reason=get_col("outcome_reason"),
            error_category=get_col("error_category"),
            error_fingerprint=get_col("error_fingerprint"),
            created_at=row["created_at"],
        )
