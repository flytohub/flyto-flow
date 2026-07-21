"""
Checkpoint Service

Manages execution state checkpoints for resume from failure functionality.
Stores checkpoints after each step execution for later recovery.

Design principles:
- Atomic: Each checkpoint is a complete snapshot
- Immutable: Checkpoints are never modified after creation
- Queryable: Can retrieve checkpoints by execution_id, step_index, or step_id
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class CheckpointService:
    """
    Service for managing execution checkpoints.

    Checkpoints are stored in the runs directory alongside execution artifacts.
    Each checkpoint contains the full execution state at a specific step.
    """

    def __init__(self, runs_directory: Optional[Path] = None):
        """
        Initialize checkpoint service.

        Args:
            runs_directory: Base directory for checkpoint storage.
                          If None, uses in-memory storage only.
        """
        self._runs_directory = runs_directory
        self._memory_store: Dict[str, List[Dict[str, Any]]] = {}

    async def save_checkpoint(
        self,
        execution_id: str,
        step_index: int,
        step_id: str,
        data: Dict[str, Any],
        status: str,
    ) -> str:
        """
        Save a checkpoint after step execution.

        Args:
            execution_id: The execution ID
            step_index: Index of the completed step
            step_id: ID of the completed step
            data: Checkpoint data including context, params, etc.
            status: 'success' or 'failed'

        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"{execution_id}_{step_index}_{step_id}"

        checkpoint = {
            'id': checkpoint_id,
            'execution_id': execution_id,
            'step_index': step_index,
            'step_id': step_id,
            'status': status,
            'created_at': _utc_now().isoformat(),
            'data': data,
        }

        # Store in memory
        if execution_id not in self._memory_store:
            self._memory_store[execution_id] = []
        self._memory_store[execution_id].append(checkpoint)

        # Store to disk if runs_directory is set
        if self._runs_directory:
            await self._save_to_disk(execution_id, checkpoint)

        logger.debug(f"Saved checkpoint {checkpoint_id}")
        return checkpoint_id

    async def _save_to_disk(
        self,
        execution_id: str,
        checkpoint: Dict[str, Any]
    ) -> None:
        """Save checkpoint to disk."""
        try:
            # Find execution directory
            exec_dir = self._runs_directory / execution_id
            if not exec_dir.exists():
                exec_dir.mkdir(parents=True, exist_ok=True)

            # Save checkpoint to checkpoints subdirectory
            checkpoints_dir = exec_dir / "checkpoints"
            checkpoints_dir.mkdir(exist_ok=True)

            checkpoint_file = checkpoints_dir / f"{checkpoint['step_index']:04d}_{checkpoint['step_id']}.json"
            checkpoint_file.write_text(json.dumps(checkpoint, indent=2, default=str))

        except Exception as e:
            logger.warning(f"Failed to save checkpoint to disk: {e}")

    async def get_checkpoints(
        self,
        execution_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all checkpoints for an execution.

        Args:
            execution_id: The execution ID

        Returns:
            List of checkpoints ordered by step_index
        """
        checkpoints = self._memory_store.get(execution_id, [])

        # If not in memory, try loading from disk
        if not checkpoints and self._runs_directory:
            checkpoints = await self._load_from_disk(execution_id)
            if checkpoints:
                self._memory_store[execution_id] = checkpoints

        return sorted(checkpoints, key=lambda c: c['step_index'])

    async def _load_from_disk(
        self,
        execution_id: str
    ) -> List[Dict[str, Any]]:
        """Load checkpoints from disk."""
        checkpoints = []
        try:
            checkpoints_dir = self._runs_directory / execution_id / "checkpoints"
            if checkpoints_dir.exists():
                for checkpoint_file in checkpoints_dir.glob("*.json"):
                    try:
                        checkpoint = json.loads(checkpoint_file.read_text())
                        checkpoints.append(checkpoint)
                    except Exception as e:
                        logger.warning(f"Failed to load checkpoint {checkpoint_file}: {e}")
        except Exception as e:
            logger.warning(f"Failed to load checkpoints from disk: {e}")

        return checkpoints

    async def get_checkpoint(
        self,
        execution_id: str,
        step_index: Optional[int] = None,
        step_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific checkpoint.

        Args:
            execution_id: The execution ID
            step_index: Optional step index to find
            step_id: Optional step ID to find

        Returns:
            Checkpoint if found, None otherwise
        """
        checkpoints = await self.get_checkpoints(execution_id)

        for checkpoint in checkpoints:
            if step_index is not None and checkpoint['step_index'] == step_index:
                return checkpoint
            if step_id is not None and checkpoint['step_id'] == step_id:
                return checkpoint

        return None

    async def get_latest_checkpoint(
        self,
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest checkpoint for an execution.

        Args:
            execution_id: The execution ID

        Returns:
            Latest checkpoint if any exist, None otherwise
        """
        checkpoints = await self.get_checkpoints(execution_id)
        return checkpoints[-1] if checkpoints else None

    async def get_latest_successful_checkpoint(
        self,
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest successful checkpoint for an execution.

        Useful for resume from failure - finds the last good state.

        Args:
            execution_id: The execution ID

        Returns:
            Latest successful checkpoint if any exist, None otherwise
        """
        checkpoints = await self.get_checkpoints(execution_id)

        for checkpoint in reversed(checkpoints):
            if checkpoint['status'] == 'success':
                return checkpoint

        return None

    async def delete_checkpoints(
        self,
        execution_id: str
    ) -> int:
        """
        Delete all checkpoints for an execution.

        Args:
            execution_id: The execution ID

        Returns:
            Number of checkpoints deleted
        """
        count = len(self._memory_store.get(execution_id, []))

        # Remove from memory
        if execution_id in self._memory_store:
            del self._memory_store[execution_id]

        # Remove from disk
        if self._runs_directory:
            try:
                checkpoints_dir = self._runs_directory / execution_id / "checkpoints"
                if checkpoints_dir.exists():
                    import shutil
                    shutil.rmtree(checkpoints_dir)
            except Exception as e:
                logger.warning(f"Failed to delete checkpoints from disk: {e}")

        logger.info(f"Deleted {count} checkpoints for {execution_id}")
        return count

    def clear_memory_cache(self) -> None:
        """Clear all in-memory checkpoints."""
        self._memory_store.clear()


# Singleton instance
_checkpoint_service: Optional[CheckpointService] = None


def get_checkpoint_service() -> CheckpointService:
    """Get the global checkpoint service instance."""
    global _checkpoint_service
    if _checkpoint_service is None:
        # Auto-detect runs directory for disk persistence
        runs_dir = None
        try:
            from services.runs_directory import get_runs_directory
            runs_dir = get_runs_directory().base_path
        except Exception:
            pass
        _checkpoint_service = CheckpointService(runs_directory=runs_dir)
    return _checkpoint_service


def init_checkpoint_service(runs_directory: Path) -> CheckpointService:
    """Initialize the checkpoint service with a runs directory."""
    global _checkpoint_service
    _checkpoint_service = CheckpointService(runs_directory)
    return _checkpoint_service
