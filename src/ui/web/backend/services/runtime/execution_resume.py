"""
Execution Resume Service

Provides resume-from-failure functionality for workflow executions.
Saves execution snapshots at checkpoints and allows resuming from any saved state.

Design:
- Decoupled from execution engine
- Checkpoint-based state persistence
- Supports resume from failure or specific node
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CheckpointType(str, Enum):
    """Type of checkpoint."""
    NODE_START = "node_start"
    NODE_COMPLETE = "node_complete"
    ERROR = "error"
    MANUAL = "manual"


@dataclass
class ExecutionCheckpoint:
    """Snapshot of execution state at a checkpoint."""
    id: str
    execution_id: str
    checkpoint_type: CheckpointType
    node_id: str
    node_index: int
    timestamp: str
    variables: Dict[str, Any]
    node_outputs: Dict[str, Any]
    workflow_yaml: str
    remaining_steps: List[str]
    error_message: Optional[str] = None
    browser_state: Optional[Dict[str, Any]] = None


@dataclass
class ResumeOptions:
    """Available resume options for an execution."""
    execution_id: str
    can_resume: bool
    checkpoints: List[Dict[str, Any]]
    recommended_checkpoint: Optional[str] = None
    failure_node: Optional[str] = None
    failure_message: Optional[str] = None


class ExecutionResumeService:
    """
    Manages execution checkpoints and resume functionality.

    Workflow:
    1. Worker saves checkpoints during execution
    2. On failure, checkpoints are preserved
    3. User can view resume options
    4. User selects checkpoint to resume from
    5. New execution continues from checkpoint state
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize resume service.

        Args:
            storage_path: Path to store checkpoint files (optional)
        """
        self._checkpoints: Dict[str, List[ExecutionCheckpoint]] = {}
        self._storage_path = storage_path

        if storage_path:
            storage_path.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        execution_id: str,
        checkpoint_type: CheckpointType,
        node_id: str,
        node_index: int,
        variables: Dict[str, Any],
        node_outputs: Dict[str, Any],
        workflow_yaml: str,
        remaining_steps: List[str],
        error_message: Optional[str] = None,
        browser_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save an execution checkpoint.

        Args:
            execution_id: The execution ID
            checkpoint_type: Type of checkpoint
            node_id: Current node ID
            node_index: Current node index
            variables: Current variable state
            node_outputs: Outputs from completed nodes
            workflow_yaml: The workflow YAML definition
            remaining_steps: List of remaining step IDs
            error_message: Error message if checkpoint is for error
            browser_state: Browser state if applicable

        Returns:
            Checkpoint ID
        """
        checkpoint_id = str(uuid.uuid4())

        checkpoint = ExecutionCheckpoint(
            id=checkpoint_id,
            execution_id=execution_id,
            checkpoint_type=checkpoint_type,
            node_id=node_id,
            node_index=node_index,
            timestamp=datetime.now(timezone.utc).isoformat(),
            variables=variables.copy(),
            node_outputs=node_outputs.copy(),
            workflow_yaml=workflow_yaml,
            remaining_steps=remaining_steps.copy(),
            error_message=error_message,
            browser_state=browser_state
        )

        if execution_id not in self._checkpoints:
            self._checkpoints[execution_id] = []

        self._checkpoints[execution_id].append(checkpoint)

        # Persist to disk if storage path configured
        if self._storage_path:
            self._persist_checkpoint(checkpoint)

        logger.debug(
            f"Checkpoint saved: {checkpoint_id} for execution {execution_id} "
            f"at node {node_id} ({checkpoint_type.value})"
        )

        return checkpoint_id

    def get_resume_options(self, execution_id: str) -> Optional[ResumeOptions]:
        """
        Get available resume options for an execution.

        Args:
            execution_id: The execution ID

        Returns:
            ResumeOptions or None if no checkpoints exist
        """
        checkpoints = self._checkpoints.get(execution_id, [])

        if not checkpoints:
            # Try loading from disk
            if self._storage_path:
                checkpoints = self._load_checkpoints(execution_id)
                if checkpoints:
                    self._checkpoints[execution_id] = checkpoints

        if not checkpoints:
            return None

        # Find error checkpoint if any
        error_checkpoint = None
        for cp in reversed(checkpoints):
            if cp.checkpoint_type == CheckpointType.ERROR:
                error_checkpoint = cp
                break

        # Build checkpoint summaries
        checkpoint_summaries = [
            {
                "id": cp.id,
                "type": cp.checkpoint_type.value,
                "node_id": cp.node_id,
                "node_index": cp.node_index,
                "timestamp": cp.timestamp,
                "has_error": cp.error_message is not None
            }
            for cp in checkpoints
        ]

        # Recommend last successful checkpoint before error
        recommended = None
        if error_checkpoint:
            for cp in reversed(checkpoints):
                if cp.checkpoint_type == CheckpointType.NODE_COMPLETE:
                    recommended = cp.id
                    break

        return ResumeOptions(
            execution_id=execution_id,
            can_resume=len(checkpoints) > 0,
            checkpoints=checkpoint_summaries,
            recommended_checkpoint=recommended,
            failure_node=error_checkpoint.node_id if error_checkpoint else None,
            failure_message=error_checkpoint.error_message if error_checkpoint else None
        )

    def get_checkpoint(
        self,
        execution_id: str,
        checkpoint_id: str
    ) -> Optional[ExecutionCheckpoint]:
        """
        Get a specific checkpoint.

        Args:
            execution_id: The execution ID
            checkpoint_id: The checkpoint ID

        Returns:
            ExecutionCheckpoint or None
        """
        checkpoints = self._checkpoints.get(execution_id, [])

        for cp in checkpoints:
            if cp.id == checkpoint_id:
                return cp

        return None

    def can_resume(self, execution_id: str) -> bool:
        """
        Check if an execution can be resumed.

        Args:
            execution_id: The execution ID

        Returns:
            True if resumable
        """
        options = self.get_resume_options(execution_id)
        return options is not None and options.can_resume

    def prepare_resume(
        self,
        execution_id: str,
        checkpoint_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Prepare resume data from a checkpoint.

        Args:
            execution_id: The execution ID
            checkpoint_id: Optional specific checkpoint (default: recommended)

        Returns:
            Resume data dict or None
        """
        options = self.get_resume_options(execution_id)
        if not options or not options.can_resume:
            return None

        # Use recommended checkpoint if not specified
        target_id = checkpoint_id or options.recommended_checkpoint
        if not target_id:
            # Use last checkpoint if no recommended
            checkpoints = self._checkpoints.get(execution_id, [])
            if checkpoints:
                target_id = checkpoints[-1].id
            else:
                return None

        checkpoint = self.get_checkpoint(execution_id, target_id)
        if not checkpoint:
            return None

        return {
            "workflow_yaml": checkpoint.workflow_yaml,
            "variables": checkpoint.variables,
            "node_outputs": checkpoint.node_outputs,
            "start_from_node": checkpoint.node_id,
            "start_from_index": checkpoint.node_index,
            "remaining_steps": checkpoint.remaining_steps,
            "original_execution_id": execution_id,
            "checkpoint_id": checkpoint_id,
            "browser_state": checkpoint.browser_state
        }

    def clear_checkpoints(self, execution_id: str) -> int:
        """
        Clear all checkpoints for an execution.

        Args:
            execution_id: The execution ID

        Returns:
            Number of checkpoints removed
        """
        count = len(self._checkpoints.get(execution_id, []))
        self._checkpoints.pop(execution_id, None)

        # Remove from disk if storage configured
        if self._storage_path:
            self._remove_checkpoints(execution_id)

        return count

    def cleanup(self, max_age_seconds: int = 86400) -> int:
        """
        Remove old checkpoints.

        Args:
            max_age_seconds: Maximum age in seconds (default: 24h)

        Returns:
            Number of executions cleaned up
        """
        now = datetime.now(timezone.utc)
        to_remove = []

        for exec_id, checkpoints in self._checkpoints.items():
            if not checkpoints:
                to_remove.append(exec_id)
                continue

            # Check age of newest checkpoint
            newest = max(checkpoints, key=lambda c: c.timestamp)
            ts = datetime.fromisoformat(newest.timestamp.replace("Z", "+00:00"))
            age = (now - ts).total_seconds()

            if age > max_age_seconds:
                to_remove.append(exec_id)

        for exec_id in to_remove:
            self.clear_checkpoints(exec_id)

        return len(to_remove)

    def _persist_checkpoint(self, checkpoint: ExecutionCheckpoint) -> None:
        """Persist checkpoint to disk."""
        if not self._storage_path:
            return

        exec_dir = self._storage_path / checkpoint.execution_id
        exec_dir.mkdir(exist_ok=True)

        file_path = exec_dir / f"{checkpoint.id}.json"
        data = {
            "id": checkpoint.id,
            "execution_id": checkpoint.execution_id,
            "checkpoint_type": checkpoint.checkpoint_type.value,
            "node_id": checkpoint.node_id,
            "node_index": checkpoint.node_index,
            "timestamp": checkpoint.timestamp,
            "variables": checkpoint.variables,
            "node_outputs": checkpoint.node_outputs,
            "workflow_yaml": checkpoint.workflow_yaml,
            "remaining_steps": checkpoint.remaining_steps,
            "error_message": checkpoint.error_message,
            "browser_state": checkpoint.browser_state
        }

        with open(file_path, "w") as f:
            json.dump(data, f)

    def _load_checkpoints(self, execution_id: str) -> List[ExecutionCheckpoint]:
        """Load checkpoints from disk."""
        if not self._storage_path:
            return []

        exec_dir = self._storage_path / execution_id
        if not exec_dir.exists():
            return []

        checkpoints = []
        for file_path in exec_dir.glob("*.json"):
            try:
                with open(file_path) as f:
                    data = json.load(f)

                checkpoint = ExecutionCheckpoint(
                    id=data["id"],
                    execution_id=data["execution_id"],
                    checkpoint_type=CheckpointType(data["checkpoint_type"]),
                    node_id=data["node_id"],
                    node_index=data["node_index"],
                    timestamp=data["timestamp"],
                    variables=data["variables"],
                    node_outputs=data["node_outputs"],
                    workflow_yaml=data["workflow_yaml"],
                    remaining_steps=data["remaining_steps"],
                    error_message=data.get("error_message"),
                    browser_state=data.get("browser_state")
                )
                checkpoints.append(checkpoint)
            except Exception as e:
                logger.error(f"Failed to load checkpoint {file_path}: {e}")

        # Sort by timestamp
        checkpoints.sort(key=lambda c: c.timestamp)
        return checkpoints

    def _remove_checkpoints(self, execution_id: str) -> None:
        """Remove checkpoints from disk."""
        if not self._storage_path:
            return

        exec_dir = self._storage_path / execution_id
        if not exec_dir.exists():
            return

        import shutil
        shutil.rmtree(exec_dir, ignore_errors=True)


# Global singleton instance
_resume_service: Optional[ExecutionResumeService] = None


def get_resume_service() -> ExecutionResumeService:
    """Get the global execution resume service instance."""
    global _resume_service
    if _resume_service is None:
        _resume_service = ExecutionResumeService()
    return _resume_service
