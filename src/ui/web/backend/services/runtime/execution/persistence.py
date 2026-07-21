"""
Execution Persistence

Handles persisting execution state to SQLite and data providers (Firebase).
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
    Persist execution status to SQLite and data provider.

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

    # 3. Persist to data provider (Firebase) for stats
    await _persist_to_provider(info, duration_ms)

    # 4. Settle per-call template earnings/refunds if this execution came from
    # the marketplace per-call path. The settlement helper is idempotent and
    # no-ops for ordinary workflow executions.
    await _settle_per_call_execution(info)

    # 5. Fire-and-forget: AI root cause analysis on failure
    if info.status == ExecutionStatus.FAILED:
        _trigger_root_cause_analysis(info.execution_id)


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


async def _persist_to_provider(info: "ExecutionInfo", duration_ms: Optional[int]) -> None:
    """Persist execution to data provider (Firebase)."""
    if not info.provider_execution_id or not info.user_id:
        return

    try:
        from services.cloud_client import cloud_put

        firebase_status_map = {
            ExecutionStatus.COMPLETED: "success",
            ExecutionStatus.FAILED: "failed",
            ExecutionStatus.CANCELLED: "cancelled",
            ExecutionStatus.RUNNING: "running",
            ExecutionStatus.PENDING: "pending",
        }

        await cloud_put(
            f"workflows/{info.workflow_id}/executions/{info.provider_execution_id}",
            json={
                "status": firebase_status_map.get(info.status, "failed"),
                "result_data": redact_sensitive(info.result),
                "error_message": info.error,
                "finished_at": info.end_time.isoformat() if info.end_time else None,
                "duration_ms": duration_ms,
            },
        )
        logger.info(f"Persisted execution {info.execution_id} to cloud")

    except Exception as e:
        logger.warning(f"Failed to persist execution status to cloud: {e}")


async def _settle_per_call_execution(info: "ExecutionInfo") -> None:
    """Best-effort per-call earning settlement for terminal executions."""
    try:
        from services.per_call_settlement import (
            is_terminal_execution_status,
            settle_per_call_execution,
        )

        if not is_terminal_execution_status(info.status):
            return

        await settle_per_call_execution(
            execution_id=info.execution_id,
            status=info.status,
            error_message=info.error,
        )
    except Exception as e:
        logger.warning(
            "Failed to settle per-call execution %s: %s",
            info.execution_id,
            e,
        )


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
    user_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get execution history from SQLite.

    Args:
        workflow_id: Filter by workflow ID
        user_id: Filter by user ID
        limit: Maximum number of results

    Returns:
        List of execution dicts
    """
    try:
        from gateway.storage import ExecutionRepository
        executions = ExecutionRepository.list_executions(
            workflow_id=workflow_id,
            user_id=user_id,
            limit=limit,
        )
        return [e.to_dict() for e in executions]
    except Exception as e:
        logger.warning(f"Failed to get execution history from SQLite: {e}")
        return []


def cleanup_old_executions(
    in_memory_executions: Dict[str, "ExecutionInfo"],
    max_age_seconds: int = 3600,
    user_id: Optional[str] = None,
) -> int:
    """
    Remove old completed/failed/cancelled executions from memory.

    Args:
        in_memory_executions: Dictionary of executions to clean
        max_age_seconds: Remove executions older than this
        user_id: If provided, only clean executions owned by this user

    Returns:
        Number of executions removed
    """
    now = utc_now()
    to_remove = []

    for exec_id, info in in_memory_executions.items():
        # Filter by user if specified
        if user_id and info.user_id != user_id:
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


def _trigger_root_cause_analysis(execution_id: str) -> None:
    """Fire-and-forget: trigger AI root cause analysis for a failed execution."""
    import asyncio

    try:
        from services.cloud.ai_insights import get_ai_insights_service
        service = get_ai_insights_service()

        # Check if auto root cause is enabled
        config = service._get_config()
        if not config.get("auto_root_cause", True):
            return
        if not service.enabled:
            return

        # Schedule as background task (don't block the persistence pipeline)
        loop = asyncio.get_event_loop()
        loop.create_task(_run_root_cause(service, execution_id))
    except Exception as e:
        logger.debug(f"Auto root cause skipped: {e}")


async def _run_root_cause(service, execution_id: str) -> None:
    """Background coroutine for root cause analysis."""
    try:
        result = await service.analyze_root_cause(execution_id)
        if result.get("ok"):
            logger.info(f"Auto root cause analysis completed for {execution_id}")
        else:
            logger.warning(f"Auto root cause analysis failed for {execution_id}: {result.get('error')}")
    except Exception as e:
        logger.warning(f"Auto root cause analysis error for {execution_id}: {e}")
