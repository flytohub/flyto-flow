"""
Execution Manager Service

Main service class for managing workflow execution lifecycle.
Delegates heavy logic to focused helper modules:
- workflow_runner: Engine creation, execution loop, cleanup
- template_loader: Template definition fetching
- error_handler: Error workflow triggering
- credential_resolver: SecretRef token creation
"""

import asyncio
import logging
import uuid
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from services.runtime.execution.enums import ExecutionStatus
from services.runtime.execution.models import ExecutionInfo
from services.runtime.execution.utils import utc_now, ensure_sqlite_initialized
from services.runtime.execution.queue_integration import USE_QUEUE, enqueue_execution, cancel_queued_execution
from services.runtime.execution.persistence import (
    get_execution_status,
    get_execution_history,
    cleanup_old_executions,
)
from services.runtime.execution.redaction import redact_sensitive
from services.runtime.execution.workflow_runner import run_workflow
from services.runtime.execution.credential_resolver import create_credential_tokens

import os

logger = logging.getLogger(__name__)

# Maximum time (seconds) for a single workflow execution (default: 30 minutes)
MAX_EXECUTION_TIMEOUT = int(os.environ.get('FLYTO_MAX_EXECUTION_TIMEOUT', '1800'))

# Module-level singleton instance
_execution_manager: Optional["ExecutionManager"] = None


class ExecutionManager:
    """
    Manager for workflow executions.

    Responsibilities:
    - Start/run workflows
    - Track execution status
    - Cancel running workflows
    - Clean up old executions

    Not responsible for:
    - Actual workflow execution (delegated to WorkflowEngine via workflow_runner)
    - Step-level tracking (delegated to StepTrackingHooks)
    - Persistence (delegated to persistence module)
    - Template loading (delegated to template_loader)
    - Error workflow handling (delegated to error_handler)
    - Credential token creation (delegated to credential_resolver)

    Usage:
        manager = get_execution_manager()
        exec_id = await manager.start(workflow_yaml, variables)
        status = manager.get_status(exec_id)
        manager.cancel(exec_id)
    """

    def __init__(self):
        """Initialize execution store and async lock."""
        self._executions: Dict[str, ExecutionInfo] = {}
        self._lock = asyncio.Lock()

    async def start(
        self,
        workflow_yaml: str,
        variables: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None,
        start_step: Optional[int] = None,
        end_step: Optional[int] = None,
        user_id: Optional[str] = None,
        workflow_name: Optional[str] = None,
        breakpoints: Optional[List[str]] = None,
        screenshot_mode: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Start a new workflow execution.

        Args:
            workflow_yaml: YAML workflow definition
            variables: Runtime variables to inject
            workflow_id: Optional workflow identifier
            start_step: Optional start step index (0-based) for partial execution
            end_step: Optional end step index (0-based) for partial execution
            user_id: Optional user ID for ownership tracking
            workflow_name: Optional workflow name (parsed from YAML if not provided)
            breakpoints: Optional list of node IDs where execution should pause
            screenshot_mode: Screenshot capture mode ("off", "on_error", "all")
            initial_context: Optional initial context to inject (for replay/resume)

        Returns:
            execution_id: Unique execution identifier

        Raises:
            Exception: If rate limited or concurrency check fails
        """
        # Initialize SQLite if needed
        ensure_sqlite_initialized()

        execution_id = str(uuid.uuid4())
        workflow_id = workflow_id or f"workflow_{execution_id[:8]}"

        # Check concurrency limits
        await self._check_concurrency_limits(execution_id, user_id, workflow_id)

        # Parse workflow data
        workflow_data, workflow_name = self._parse_workflow(workflow_yaml, workflow_name)

        raw_variables = variables or {}
        safe_variables = redact_sensitive(raw_variables)
        runtime_initial_context = self._build_runtime_initial_context(
            raw_variables, initial_context
        )

        # Create execution snapshot
        snapshot, snapshot_dicts = await self._create_snapshot(
            execution_id, workflow_id, workflow_name, workflow_data, safe_variables, user_id
        )

        # Create SQLite record
        execution_id = await self._create_sqlite_record(
            execution_id, workflow_id, workflow_name, user_id, safe_variables, snapshot_dicts
        )

        # Create provider record (Firebase)
        provider_execution_id = await self._create_provider_record(
            user_id, workflow_id, safe_variables
        )

        # Create ExecutionInfo
        info = ExecutionInfo(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            user_id=user_id,
            provider_execution_id=provider_execution_id,
            input_params=safe_variables,
        )
        info.snapshot = snapshot

        # Set metadata
        if breakpoints:
            info.metadata['breakpoints'] = set(breakpoints)
            logger.debug(f"Set {len(breakpoints)} human checkpoints for {execution_id}")
        if screenshot_mode:
            info.metadata['screenshot_mode'] = screenshot_mode
        if runtime_initial_context:
            info.metadata['initial_context'] = runtime_initial_context

        # Track source blueprint for auto-reporting outcomes
        source_bp_id = workflow_data.get("source_blueprint_id")
        if source_bp_id:
            info.metadata['source_blueprint_id'] = source_bp_id

        # Create credential tokens for secretRef parameters
        try:
            credential_tokens = await create_credential_tokens(
                execution_id, workflow_data, workflow_id, user_id
            )
            if credential_tokens:
                info.metadata['credential_tokens'] = credential_tokens
                logger.debug(f"Created {len(credential_tokens)} credential tokens for {execution_id}")
        except Exception as e:
            logger.warning(f"Failed to create credential tokens: {e}")

        # Create runs directory
        info.runs_directory = await self._create_runs_directory(execution_id, snapshot)

        async with self._lock:
            self._executions[execution_id] = info

        # Start execution
        await self._start_execution(
            info, workflow_yaml, raw_variables, start_step, end_step, workflow_data
        )

        logger.info(f"Started execution {execution_id} for workflow {workflow_id}")
        return execution_id

    async def start_lightweight(
        self,
        workflow_yaml: str,
        variables: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None,
        workflow_name: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Start a lightweight execution — skips snapshot, SQLite, Firebase,
        credentials, and runs directory.

        Used by device job executor for single-step streaming execution
        where speed matters and persistence is handled by the job queue.
        """
        execution_id = str(uuid.uuid4())
        workflow_id = workflow_id or f"workflow_{execution_id[:8]}"

        workflow_data, workflow_name = self._parse_workflow(workflow_yaml, workflow_name)

        raw_variables = variables or {}
        safe_variables = redact_sensitive(raw_variables)
        runtime_initial_context = self._build_runtime_initial_context(
            raw_variables, initial_context
        )

        info = ExecutionInfo(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            input_params=safe_variables,
        )
        if runtime_initial_context:
            info.metadata['initial_context'] = runtime_initial_context

        async with self._lock:
            self._executions[execution_id] = info

        info.task = asyncio.create_task(
            run_workflow(
                self, info.execution_id, workflow_yaml, variables or {},
                None, None, workflow_data,
            )
        )

        logger.info(f"Started lightweight execution {execution_id}")
        return execution_id

    def _build_runtime_initial_context(
        self,
        variables: Dict[str, Any],
        initial_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build raw runtime context while persistence keeps redacted params."""
        context = dict(initial_context or {})
        if not variables:
            return context

        context.setdefault("variables", dict(variables))
        for key, value in variables.items():
            if isinstance(key, str) and key not in context:
                context[key] = value

        trigger_payload = variables.get("trigger_payload") or variables.get("_trigger_payload")
        if isinstance(trigger_payload, dict):
            context["trigger_payload"] = trigger_payload
            context["_trigger_payload"] = trigger_payload
            arguments = trigger_payload.get("arguments")
            if isinstance(arguments, dict):
                for key, value in arguments.items():
                    if isinstance(key, str) and key not in context:
                        context[key] = value

        return context

    # ------------------------------------------------------------------
    # Setup helpers (kept on the class — tightly coupled to start())
    # ------------------------------------------------------------------

    async def _check_concurrency_limits(
        self,
        execution_id: str,
        user_id: Optional[str],
        workflow_id: str,
    ) -> None:
        """Check and acquire concurrency slot."""
        org_id = user_id or "default"
        try:
            from services.concurrency_manager import acquire_execution_slot
            result = await acquire_execution_slot(
                execution_id=execution_id,
                user_id=user_id or "anonymous",
                org_id=org_id,
                workflow_id=workflow_id,
            )
            if not result.success:
                logger.warning(f"Execution {execution_id} rejected: {result.error_code}")
                raise Exception(
                    f"Rate limited: {result.error}. "
                    f"Retry after {result.retry_after_seconds} seconds."
                )
            logger.info(f"Acquired execution slot for {execution_id}")
        except ImportError:
            logger.debug("Concurrency manager not available")
        except Exception as e:
            if "Rate limited" in str(e):
                raise
            logger.warning(f"Concurrency check failed, proceeding: {e}")

    def _parse_workflow(
        self,
        workflow_yaml: str,
        workflow_name: Optional[str],
    ) -> tuple[Dict[str, Any], str]:
        """Parse workflow YAML securely and extract name."""
        from services.runtime.execution.yaml_security import parse_workflow_yaml, YAMLSecurityError

        workflow_data = {}
        try:
            workflow_data = parse_workflow_yaml(workflow_yaml, validate_modules=True)
            if not workflow_name:
                workflow_name = workflow_data.get("name", "Unnamed Workflow")
        except YAMLSecurityError as e:
            logger.warning(f"Workflow YAML security error: {e}")
            raise ValueError(f"Invalid workflow: {e}") from e
        except Exception as e:
            logger.error(f"Failed to parse workflow YAML: {e}")
            if not workflow_name:
                workflow_name = "Unnamed Workflow"

        return workflow_data, workflow_name

    async def _create_snapshot(
        self,
        execution_id: str,
        workflow_id: str,
        workflow_name: str,
        workflow_data: Dict[str, Any],
        variables: Optional[Dict[str, Any]],
        user_id: Optional[str],
    ) -> tuple[Optional[Any], Optional[tuple]]:
        """Create execution snapshot for reproducibility."""
        try:
            from services.runtime.snapshot import SnapshotService
            snapshot = SnapshotService.create_execution_snapshot(
                exec_id=execution_id,
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                workflow_data=workflow_data,
                input_params=variables or {},
                trigger={"type": "manual", "user_id": user_id},
            )
            snapshot_dicts = (
                asdict(snapshot.workflow),
                [asdict(m) for m in snapshot.modules],
                asdict(snapshot.env),
            )
            logger.info(f"Created execution snapshot for {execution_id}")
            return snapshot, snapshot_dicts
        except Exception as e:
            logger.warning(f"Failed to create execution snapshot: {e}")
            return None, None

    async def _create_sqlite_record(
        self,
        execution_id: str,
        workflow_id: str,
        workflow_name: str,
        user_id: Optional[str],
        variables: Optional[Dict[str, Any]],
        snapshot_dicts: Optional[tuple],
    ) -> str:
        """Create execution record in SQLite."""
        try:
            from gateway.storage import ExecutionRepository
            workflow_snapshot, modules_snapshot, env_snapshot = snapshot_dicts or (None, None, None)
            sqlite_exec = ExecutionRepository.create_execution(
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                user_id=user_id,
                input_params=variables or {},
                workflow_snapshot=workflow_snapshot,
                modules_snapshot=modules_snapshot,
                env_snapshot=env_snapshot,
            )
            logger.info(f"Created execution record in SQLite: {sqlite_exec.id}")
            return sqlite_exec.id
        except Exception as e:
            logger.warning(f"Failed to create execution in SQLite: {e}")
            return execution_id

    async def _create_provider_record(
        self,
        user_id: Optional[str],
        workflow_id: str,
        variables: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """Create execution record in data provider (Firebase)."""
        if not user_id or workflow_id == "local":
            return None

        try:
            from services.cloud_client import cloud_post
            result = await cloud_post(
                f"workflows/{workflow_id}/execute",
                json={"params": variables or {}},
            )
            if result and result.get("id"):
                logger.info(f"Created execution record in cloud: {result['id']}")
                return result["id"]
            return None
        except Exception as e:
            logger.warning(f"Failed to create execution in cloud: {e}")
            return None

    async def _create_runs_directory(
        self,
        execution_id: str,
        snapshot: Optional[Any],
    ) -> Optional[Any]:
        """Create runs directory and write manifest."""
        try:
            from services.runs_directory import get_runs_directory
            runs_dir = get_runs_directory()
            await runs_dir.create_run_directory(execution_id)
            if snapshot:
                await runs_dir.write_manifest(execution_id, snapshot)
            logger.info(f"Created runs directory for {execution_id}")
            return runs_dir
        except Exception as e:
            logger.warning(f"Failed to create runs directory: {e}")
            return None

    async def _start_execution(
        self,
        info: ExecutionInfo,
        workflow_yaml: str,
        variables: Dict[str, Any],
        start_step: Optional[int],
        end_step: Optional[int],
        workflow_data: Dict[str, Any],
    ) -> None:
        """Start execution via queue or direct task."""
        if USE_QUEUE:
            success = await enqueue_execution(
                execution_id=info.execution_id,
                workflow_id=info.workflow_id,
                user_id=info.user_id,
                priority=0,
            )
            if not success:
                # Fall back to direct execution
                info.task = asyncio.create_task(
                    run_workflow(
                        self, info.execution_id, workflow_yaml, variables,
                        start_step, end_step, workflow_data
                    )
                )
        else:
            info.task = asyncio.create_task(
                run_workflow(
                    self, info.execution_id, workflow_yaml, variables,
                    start_step, end_step, workflow_data
                )
            )

    # ------------------------------------------------------------------
    # Query / control methods
    # ------------------------------------------------------------------

    def get_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status from memory or SQLite."""
        return get_execution_status(execution_id, self._executions)

    def get_all_executions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active execution statuses (in-memory only)."""
        return {exec_id: info.to_dict() for exec_id, info in self._executions.items()}

    def get_execution_history(
        self,
        workflow_id: str = None,
        user_id: str = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get execution history from SQLite."""
        return get_execution_history(workflow_id, user_id, limit)

    def cancel(self, execution_id: str) -> bool:
        """Cancel a running execution (sync wrapper)."""
        if USE_QUEUE:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.cancel_async(execution_id))
                    return True
                return loop.run_until_complete(self.cancel_async(execution_id))
            except Exception as e:
                logger.error(f"Failed to cancel via queue: {e}")
        return self._cancel_direct(execution_id)

    async def cancel_async(self, execution_id: str, reason: str = "User cancelled") -> bool:
        """Cancel a running execution (async version)."""
        if USE_QUEUE:
            if await cancel_queued_execution(execution_id, reason):
                info = self._executions.get(execution_id)
                if info:
                    info.status = ExecutionStatus.CANCELLED
                    info.end_time = utc_now()
                logger.info(f"Execution {execution_id} cancelled via queue")
                return True
        return self._cancel_direct(execution_id)

    def _cancel_direct(self, execution_id: str) -> bool:
        """Cancel execution directly (legacy mode)."""
        info = self._executions.get(execution_id)
        if not info:
            logger.warning(f"Execution {execution_id} not found")
            return False

        if info.status != ExecutionStatus.RUNNING:
            logger.warning(f"Execution {execution_id} is not running")
            return False

        if info.engine:
            info.engine.cancel()
        if info.task and not info.task.done():
            info.task.cancel()

        info.status = ExecutionStatus.CANCELLED
        info.end_time = utc_now()
        logger.info(f"Execution {execution_id} cancelled")
        return True

    def cleanup(self, max_age_seconds: int = 3600, user_id: Optional[str] = None) -> int:
        """Remove old completed/failed/cancelled executions."""
        return cleanup_old_executions(self._executions, max_age_seconds, user_id)


def get_execution_manager() -> ExecutionManager:
    """Get the singleton execution manager instance."""
    global _execution_manager
    if _execution_manager is None:
        _execution_manager = ExecutionManager()
        logger.info("Created ExecutionManager singleton instance")
    return _execution_manager
