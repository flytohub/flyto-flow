"""
Execution Persistence

Handles persisting execution state to local SQLite and run artifacts.
"""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from services.runtime.execution.enums import ExecutionStatus
from services.runtime.execution.redaction import redact_sensitive
from services.runtime.execution.utils import utc_now

if TYPE_CHECKING:
    from services.runtime.execution.models import ExecutionInfo

logger = logging.getLogger(__name__)


async def persist_execution_status(info: "ExecutionInfo") -> None:
    """
    Persist execution status to local storage.

    Args:
        info: ExecutionInfo instance with final status
    """
    # Map internal status to storage status
    status_map = {
        ExecutionStatus.COMPLETED: "success",
        ExecutionStatus.FAILED: "failure",
        ExecutionStatus.CANCELLED: "cancelled",
        ExecutionStatus.RUNNING: "running",
        ExecutionStatus.PENDING: "pending",
    }

    # Calculate duration
    duration_ms = None
    if info.start_time and info.end_time:
        duration_ms = int((info.end_time - info.start_time).total_seconds() * 1000)

    # Phase 0: Classify outcome
    outcome, outcome_reason, error_category, error_fingerprint = await _classify_outcome(
        info, duration_ms
    )

    # 1. Persist to SQLite (local storage)
    await _persist_to_sqlite(info, status_map, duration_ms, outcome, outcome_reason, error_category, error_fingerprint)

    # 2. Write result.json to runs directory
    await _write_result_json(info)



async def _classify_outcome(
    info: "ExecutionInfo",
    duration_ms: Optional[int],
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Classify execution outcome using OutcomeClassifier."""
    outcome = None
    outcome_reason = None
    error_category = None
    error_fingerprint = None

    try:
        from services.outcome_classifier import OutcomeClassifier
        from gateway.storage import ExecutionRepository

        # Get step records from SQLite
        step_records = []
        try:
            execution = ExecutionRepository.get_execution(
                info.execution_id, include_steps=True
            )
            if execution and execution.steps:
                step_records = [s.to_dict() for s in execution.steps]
        except Exception:
            pass

        # Classify execution outcome
        outcome_obj = OutcomeClassifier.classify_execution(
            exec_id=info.execution_id,
            step_records=step_records,
            duration_ms=duration_ms,
            was_cancelled=(info.status == ExecutionStatus.CANCELLED),
        )
        info.outcome = outcome_obj
        outcome = outcome_obj.outcome.value
        outcome_reason = outcome_obj.outcome_reason

        if outcome_obj.failure_info:
            error_category = outcome_obj.failure_info.error_category.value
            error_fingerprint = outcome_obj.failure_info.fingerprint

        logger.info(f"Classified outcome for {info.execution_id}: {outcome}")
    except Exception as e:
        logger.warning(f"Failed to classify outcome: {e}")

    return outcome, outcome_reason, error_category, error_fingerprint


async def _persist_to_sqlite(
    info: "ExecutionInfo",
    status_map: Dict[ExecutionStatus, str],
    duration_ms: Optional[int],
    outcome: Optional[str],
    outcome_reason: Optional[str],
    error_category: Optional[str],
    error_fingerprint: Optional[str],
) -> None:
    """Persist execution to SQLite."""
    try:
        from gateway.storage import ExecutionRepository
        ExecutionRepository.update_execution(
            execution_id=info.execution_id,
            status=status_map.get(info.status, "failure"),
            finished_at=info.end_time.isoformat() if info.end_time else None,
            duration_ms=duration_ms,
            result_data=redact_sensitive(info.result),
            error_message=info.error,
            error_step_id=info.error_step_id,
            outcome=outcome,
            outcome_reason=outcome_reason,
            error_category=error_category,
            error_fingerprint=error_fingerprint,
        )
        logger.info(f"Persisted execution {info.execution_id} to SQLite")
    except Exception as e:
        logger.warning(f"Failed to persist execution to SQLite: {e}")


async def _write_result_json(info: "ExecutionInfo") -> None:
    """Write result.json to runs directory."""
    if not info.runs_directory or not info.outcome:
        return

    try:
        result_data = info.outcome.to_dict()
        result_data["result"] = redact_sensitive(info.result)
        await info.runs_directory.write_result(info.execution_id, result_data)
        logger.info(f"Wrote result.json for {info.execution_id}")
    except Exception as e:
        logger.warning(f"Failed to write result.json: {e}")


def get_execution_status(
    execution_id: str,
    in_memory_executions: Dict[str, "ExecutionInfo"],
) -> Optional[Dict[str, Any]]:
    """
    Get execution status from memory or SQLite.

    Args:
        execution_id: Execution to look up
        in_memory_executions: Dictionary of active executions

    Returns:
        Execution status dict or None if not found
    """
    # First check in-memory (active executions)
    info = in_memory_executions.get(execution_id)
    if info:
        # Update current_step from engine if running
        if info.engine and info.status == ExecutionStatus.RUNNING:
            engine_step = getattr(info.engine, 'current_step', None)
            logger.info(f"[Status] exec={execution_id[:8]} engine_step={engine_step} total={info.total_steps}")
            if engine_step is not None:
                info.current_step = engine_step
        else:
            logger.info(f"[Status] exec={execution_id[:8]} no_engine={info.engine is None} status={info.status.value} current={info.current_step}")
        return info.to_dict()

    # Fall back to SQLite for historical executions
    try:
        from gateway.storage import ExecutionRepository
        execution = ExecutionRepository.get_execution(execution_id)
        if execution:
            return execution.to_dict()
    except Exception as e:
        logger.warning(f"Failed to get execution from SQLite: {e}")

    return None


def get_execution_history(
    workflow_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get execution history from SQLite.

    Args:
        workflow_id: Filter by workflow ID
        workspace_id: Filter by workspace ID
        limit: Maximum number of results

    Returns:
        List of execution dicts
    """
    try:
        from gateway.storage import ExecutionRepository
        executions = ExecutionRepository.list_executions(
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            limit=limit,
        )
        return [e.to_dict() for e in executions]
    except Exception as e:
        logger.warning(f"Failed to get execution history from SQLite: {e}")
        return []


def cleanup_old_executions(
    in_memory_executions: Dict[str, "ExecutionInfo"],
    max_age_seconds: int = 3600,
    workspace_id: Optional[str] = None,
) -> int:
    """
    Remove old completed/failed/cancelled executions from memory.

    Args:
        in_memory_executions: Dictionary of executions to clean
        max_age_seconds: Remove executions older than this
        workspace_id: If provided, only clean executions owned by this user

    Returns:
        Number of executions removed
    """
    now = utc_now()
    to_remove = []

    for exec_id, info in in_memory_executions.items():
        # Filter by workspace if specified
        if workspace_id and info.workspace_id != workspace_id:
            continue

        if info.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
            if info.end_time:
                age = (now - info.end_time).total_seconds()
                if age > max_age_seconds:
                    to_remove.append(exec_id)

    for exec_id in to_remove:
        del in_memory_executions[exec_id]

    if to_remove:
        logger.info(f"Cleaned up {len(to_remove)} old executions")

    return len(to_remove)
