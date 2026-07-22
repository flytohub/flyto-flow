"""
Step Tracking Hooks

Implements ExecutorHooks to track step-level execution in SQLite and JSONL logs.
Bridges WorkflowEngine lifecycle events to storage and runs directory.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING

from services.runtime.execution.redaction import looks_like_secret, redact_sensitive

# Import the runtime contract from the installed package when available.
try:
    from core.engine.hooks import ExecutorHooks, HookContext, HookResult
except ImportError:
    class ExecutorHooks:
        """Fallback stub for ExecutorHooks when core package is unavailable."""
        pass

    class HookContext:
        """Fallback stub for HookContext when core package is unavailable."""
        pass

    class HookResult:
        """Fallback stub for HookResult when core package is unavailable."""
        @classmethod
        def continue_execution(cls):
            """Return a result indicating execution should continue."""
            return cls()

if TYPE_CHECKING:
    from services.runs_directory import RunsDirectory
    from services.runtime.execution.models import ExecutionInfo

logger = logging.getLogger(__name__)


class StepTrackingHooks(ExecutorHooks):
    """
    Tracks step execution to SQLite and runs directory.

    Records:
    - Step start/end times
    - Input parameters (redacted)
    - Output data (redacted)
    - Error information
    """

    # Keys that indicate sensitive data
    SENSITIVE_KEYS = frozenset({
        "password",
        "passwd",
        "pwd",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "api_key",
        "apikey",
        "auth",
        "authorization",
        "credential",
        "credentials",
        "private_key",
        "private",
        "access_key",
        "secret_key",
        "session",
        "cookie",
        "jwt",
        "bearer",
    })

    # Maximum size for logged data (bytes)
    MAX_DATA_SIZE = 32000

    def __init__(
        self,
        execution_id: str,
        runs_directory: Optional["RunsDirectory"] = None,
        execution_repo: Optional[Any] = None,
        execution_info: Optional["ExecutionInfo"] = None,
        workspace_id: Optional[str] = None,
    ):
        """
        Initialize step tracking hooks.

        Args:
            execution_id: Unique execution identifier
            runs_directory: RunsDirectory instance for JSONL logs
            execution_repo: ExecutionRepository class for SQLite
            execution_info: ExecutionInfo instance for node state tracking
            workspace_id: Workspace ID for points deduction (None = skip deduction)
        """
        self._execution_id = execution_id
        self._runs_directory = runs_directory
        self._execution_repo = execution_repo
        self._execution_info = execution_info
        self._workspace_id = workspace_id
        self._step_start_times: Dict[str, float] = {}
        self._step_indices: Dict[str, int] = {}

    @property
    def execution_id(self) -> str:
        """Get execution identifier."""
        return self._execution_id

    def on_workflow_start(self, context: HookContext) -> HookResult:
        """Log workflow start."""
        logger.info(
            f"Workflow started: {context.workflow_id} ({context.workflow_name})"
        )

        if self._runs_directory:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                loop.create_task(
                    self._runs_directory.append_step_log(
                        self._execution_id,
                        {
                            "event": "workflow_started",
                            "workflow_id": context.workflow_id,
                            "workflow_name": context.workflow_name,
                            "total_steps": context.total_steps,
                        },
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to log workflow start: {e}")

        return HookResult.continue_execution()

    def on_workflow_complete(self, context: HookContext) -> None:
        """Log workflow completion."""
        logger.info(
            f"Workflow completed: {context.workflow_id} "
            f"(elapsed: {context.elapsed_ms:.1f}ms)"
        )

        if self._runs_directory:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                loop.create_task(
                    self._runs_directory.append_step_log(
                        self._execution_id,
                        {
                            "event": "workflow_completed",
                            "workflow_id": context.workflow_id,
                            "elapsed_ms": context.elapsed_ms,
                        },
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to log workflow complete: {e}")

    def on_workflow_failed(self, context: HookContext) -> None:
        """Log workflow failure."""
        logger.error(
            f"Workflow failed: {context.workflow_id} "
            f"- {context.error_type}: {context.error_message}"
        )

        if self._runs_directory:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                loop.create_task(
                    self._runs_directory.append_step_log(
                        self._execution_id,
                        {
                            "event": "workflow_failed",
                            "workflow_id": context.workflow_id,
                            "error_type": context.error_type,
                            "error_message": context.error_message,
                            "elapsed_ms": context.elapsed_ms,
                        },
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to log workflow failed: {e}")

    def on_pre_execute(self, context: HookContext) -> HookResult:
        """
        Record step start in SQLite and JSONL.

        Args:
            context: Execution context with step info

        Returns:
            HookResult to continue execution
        """
        step_id = context.step_id or f"step_{context.step_index}"
        step_index = context.step_index or 0

        # Track start time
        self._step_start_times[step_id] = time.time()
        self._step_indices[step_id] = step_index

        # Redact sensitive params
        safe_params = self._redact_sensitive(context.params)
        safe_params = self._truncate_data(safe_params)

        # Update node state for frontend rendering
        if self._execution_info:
            self._execution_info.node_states[step_id] = "running"
            self._execution_info.active_node_id = step_id
            # Track start time in node_timings for duration display
            start_time_iso = datetime.now(timezone.utc).isoformat()
            self._execution_info.node_timings[step_id] = {
                "started_at": start_time_iso,
                "completed_at": None,
                "duration_ms": None
            }
            # Track node inputs for diff view
            self._execution_info.node_inputs[step_id] = safe_params

        logger.debug(
            f"Step {step_index}/{context.total_steps}: "
            f"{context.module_id} ({step_id})"
        )

        # Create step record in SQLite
        if self._execution_repo:
            try:
                self._execution_repo.add_step(
                    execution_id=self._execution_id,
                    step_id=step_id,
                    step_index=step_index,
                    module_id=context.module_id or "",
                    status="running",
                    input_params=safe_params,
                )
            except Exception as e:
                logger.warning(f"Failed to create step record: {e}")

        # Append to JSONL log
        if self._runs_directory:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                loop.create_task(
                    self._runs_directory.append_step_log(
                        self._execution_id,
                        {
                            "event": "step_started",
                            "step_id": step_id,
                            "step_index": step_index,
                            "module_id": context.module_id,
                            "attempt": context.attempt,
                            "input_params": safe_params,
                        },
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to append step log: {e}")

        return HookResult.continue_execution()

    def on_post_execute(self, context: HookContext) -> HookResult:
        """
        Record step completion in SQLite and JSONL.

        Args:
            context: Execution context with result/error

        Returns:
            HookResult to continue execution
        """
        step_id = context.step_id or f"step_{context.step_index}"

        # Calculate duration
        start_time = self._step_start_times.get(step_id)
        duration_ms = None
        if start_time:
            duration_ms = int((time.time() - start_time) * 1000)
            del self._step_start_times[step_id]

        now = datetime.now(timezone.utc).isoformat()

        # Determine status and prepare data
        if context.error:
            status = "failure"
            safe_output = None
            error_message = str(context.error_message or context.error)

            # Update node state for frontend rendering
            if self._execution_info:
                self._execution_info.node_states[step_id] = "failed"
                self._execution_info.active_node_id = None
                # Update node_timings with completion data
                if step_id in self._execution_info.node_timings:
                    self._execution_info.node_timings[step_id]["completed_at"] = now
                    self._execution_info.node_timings[step_id]["duration_ms"] = duration_ms

            logger.debug(
                f"Step failed: {step_id} "
                f"- {context.error_type}: {error_message}"
            )
        else:
            status = "success"
            safe_output = self._redact_sensitive(context.result)
            safe_output = self._truncate_output(safe_output)
            error_message = None

            # Update node state for frontend rendering
            if self._execution_info:
                self._execution_info.node_states[step_id] = "completed"
                self._execution_info.active_node_id = None
                # Update node_timings with completion data
                if step_id in self._execution_info.node_timings:
                    self._execution_info.node_timings[step_id]["completed_at"] = now
                    self._execution_info.node_timings[step_id]["duration_ms"] = duration_ms
                # Track node outputs for diff view
                self._execution_info.node_outputs[step_id] = safe_output

                # Collect display outputs (__display__: true) — no truncation
                self._collect_display_outputs(context.result, step_id, context.module_id, now)

            logger.debug(
                f"Step completed: {step_id} ({duration_ms}ms)"
            )

        # Update step record in SQLite
        if self._execution_repo:
            try:
                self._execution_repo.update_step(
                    execution_id=self._execution_id,
                    step_id=step_id,
                    status=status,
                    finished_at=now,
                    duration_ms=duration_ms,
                    output_data=safe_output,
                    error_message=error_message,
                )
            except Exception as e:
                logger.warning(f"Failed to update step record: {e}")

        # Broadcast step result via WebSocket for real-time Preview Results
        try:
            import asyncio
            from services.websocket_manager import manager as ws_manager
            asyncio.ensure_future(ws_manager.send_log(self._execution_id, {
                "type": "step_completed",
                "step_id": step_id,
                "module_id": context.module_id,
                "status": status,
                "output": safe_output,
                "duration_ms": duration_ms,
            }))
        except Exception:
            pass

        # Append to JSONL log
        if self._runs_directory:
            try:
                import asyncio

                event_data = {
                    "event": "step_succeeded" if status == "success" else "step_failed",
                    "step_id": step_id,
                    "step_index": self._step_indices.get(step_id),
                    "module_id": context.module_id,
                    "duration_ms": duration_ms,
                }

                if status == "success":
                    event_data["output"] = safe_output
                else:
                    event_data["error_type"] = context.error_type
                    event_data["error_message"] = error_message

                loop = asyncio.get_event_loop()
                loop.create_task(
                    self._runs_directory.append_step_log(
                        self._execution_id,
                        event_data,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to append step log: {e}")

        return HookResult.continue_execution()

    def on_error(self, context: HookContext) -> HookResult:
        """Log step error."""
        step_id = context.step_id or f"step_{context.step_index}"

        logger.warning(
            f"Error in step {step_id}: "
            f"{context.error_type}: {context.error_message}"
        )

        return HookResult.continue_execution()

    def create_step_notifier(self, step_id: str):
        """Create a real-time notification callback for agent streaming.

        Returns an async callback that broadcasts agent events (tool calls,
        iterations) via WebSocket for real-time frontend display.
        """
        execution_id = self._execution_id
        execution_info = self._execution_info

        async def _notify(event_type: str, data: dict):
            # Update execution info for polling fallback
            if execution_info and event_type == 'agent:tool_call':
                execution_info.metadata.setdefault('agent_activity', {})[step_id] = {
                    'tool': data.get('tool', ''),
                    'iteration': data.get('iteration', 0),
                    'tool_call_index': data.get('tool_call_index', 0),
                }
            elif execution_info and event_type == 'agent:tool_result':
                # Clear active tool after result
                agent_activity = execution_info.metadata.get('agent_activity', {})
                if step_id in agent_activity:
                    agent_activity[step_id]['status'] = 'completed'

            # Broadcast via WebSocket
            try:
                from services.websocket_manager import manager as ws_manager
                await ws_manager.send_log(execution_id, {
                    'type': event_type,
                    'step_id': step_id,
                    **data,
                })
            except Exception:
                pass

        return _notify

    def on_retry(self, context: HookContext) -> HookResult:
        """Log retry attempt."""
        step_id = context.step_id or f"step_{context.step_index}"

        logger.info(
            f"Retrying step {step_id}: "
            f"attempt {context.attempt}/{context.max_attempts}"
        )

        if self._runs_directory:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                loop.create_task(
                    self._runs_directory.append_step_log(
                        self._execution_id,
                        {
                            "event": "step_retry",
                            "step_id": step_id,
                            "step_index": context.step_index,
                            "module_id": context.module_id,
                            "attempt": context.attempt,
                            "max_attempts": context.max_attempts,
                        },
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to log retry: {e}")

        return HookResult.continue_execution()

    def _collect_display_outputs(
        self, result: Any, step_id: str, module_id: str, timestamp: str
    ) -> None:
        """
        Extract __display__ items from a step result and append to display_outputs.

        Handles:
        - Direct __display__: true on result
        - __display__: true nested inside result['data'] (after wrap_legacy_result)
        - __display_items__: [...] from loop nested mode (aggregated body outputs)
        """
        if not self._execution_info or not isinstance(result, dict):
            return

        def _append(src: dict) -> None:
            """Append a display output entry from the given source dict."""
            self._execution_info.display_outputs.append({
                'step_id': step_id,
                'module_id': module_id,
                'timestamp': timestamp,
                'type': src.get('type', 'text'),
                'title': src.get('title', ''),
                'content': src.get('content', ''),
                'data_uri': src.get('data_uri', ''),
                'mode': src.get('mode', 'display'),
                'validation_warning': src.get('validation_warning', ''),
            })

        # 1) Direct __display__ on result
        if result.get('__display__'):
            _append(result)
            return

        # 2) __display__ nested inside "data" (after wrap_legacy_result)
        data = result.get('data')
        if isinstance(data, dict) and data.get('__display__'):
            _append(data)
            return

        # 3) __display_items__ from loop nested mode
        display_items = result.get('__display_items__')
        if not display_items and isinstance(data, dict):
            display_items = data.get('__display_items__')
        if isinstance(display_items, list):
            for item in display_items:
                if isinstance(item, dict):
                    _append(item)

    def _redact_sensitive(self, data: Any) -> Any:
        """
        Redact sensitive values from data.

        Args:
            data: Data that may contain sensitive values

        Returns:
            Data with sensitive values replaced by [REDACTED]
        """
        return redact_sensitive(data, sensitive_keys=self.SENSITIVE_KEYS)

    def _looks_like_secret(self, value: str) -> bool:
        """
        Check if a string value looks like a secret.

        Args:
            value: String to check

        Returns:
            True if value appears to be a secret
        """
        return looks_like_secret(value)

    def _truncate_output(self, data: Any, max_size: int = None) -> Any:
        """
        Smart truncation for step outputs sent to frontend.

        Strategy: preserve user-facing fields (ok, data.result, error),
        strip intermediate data (data.steps with tool results, items_full).
        Only falls back to _truncate_data if still over limit.
        """
        import json

        max_size = max_size or self.MAX_DATA_SIZE

        try:
            if len(json.dumps(data, default=str)) <= max_size:
                return data
        except (TypeError, ValueError):
            return self._truncate_data(data, max_size)

        if not isinstance(data, dict):
            return self._truncate_data(data, max_size)

        # Strip heavy fields that aren't needed for frontend display
        result = dict(data)

        # Strip items_full (redundant with data)
        result.pop('items_full', None)

        # If data.steps exists (agent tool call history), summarize it
        if isinstance(result.get('data'), dict) and 'steps' in result['data']:
            steps = result['data']['steps']
            result['data'] = dict(result['data'])
            # Keep only tool_call entries (names), drop full tool_results
            result['data']['steps'] = [
                {'type': s['type'], 'tool': s.get('tool', ''), 'iteration': s.get('iteration')}
                if s.get('type') == 'tool_call'
                else {'type': s['type'], 'iteration': s.get('iteration')}
                if s.get('type') == 'final_answer'
                else s
                for s in steps
                if s.get('type') != 'tool_result'  # Drop tool results entirely
            ]

        # Check if under limit now
        try:
            if len(json.dumps(result, default=str)) <= max_size:
                return result
        except (TypeError, ValueError):
            pass

        # Still too large — fall back to generic truncation
        return self._truncate_data(result, max_size)

    def _truncate_data(self, data: Any, max_size: int = None) -> Any:
        """
        Truncate data to maximum size.

        Args:
            data: Data to truncate
            max_size: Maximum size in bytes

        Returns:
            Truncated data
        """
        import json

        max_size = max_size or self.MAX_DATA_SIZE

        try:
            serialized = json.dumps(data, default=str)
            if len(serialized) <= max_size:
                return data
        except (TypeError, ValueError):
            return str(data)[:max_size]

        # Truncate based on type
        if isinstance(data, dict):
            # Phase 1: include all keys, truncating large string values first.
            # This preserves small structured fields (like element hints) that
            # would otherwise be dropped when a large blob (content/text) appears first.
            result = {}
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 500:
                    # Truncate large strings to leave room for other keys
                    result[key] = value[:500] + f"... [truncated {len(value) - 500} chars]"
                else:
                    result[key] = value

            try:
                if len(json.dumps(result, default=str)) <= max_size:
                    return result
            except (TypeError, ValueError):
                pass

            # Phase 2: still too large — drop keys by size (largest first)
            result2 = {}
            current_size = 2  # {}
            # Priority keys that MUST survive truncation (user-facing output)
            priority_keys = ('ok', 'data', 'result', 'error', 'error_code', 'status')
            # Sort: priority keys first, then small values first so hints/metadata survive
            sorted_items = sorted(
                data.items(),
                key=lambda kv: (0 if kv[0] in priority_keys else 1, len(json.dumps(kv[1], default=str)))
            )
            for key, value in sorted_items:
                item_json = json.dumps({key: value}, default=str)
                if current_size + len(item_json) > max_size:
                    # Try truncated version
                    if isinstance(value, str) and len(value) > 200:
                        trunc_val = value[:200] + "..."
                        trunc_json = json.dumps({key: trunc_val}, default=str)
                        if current_size + len(trunc_json) <= max_size:
                            result2[key] = trunc_val
                            current_size += len(trunc_json)
                            continue
                    result2["_truncated"] = True
                    break
                result2[key] = value
                current_size += len(item_json)
            return result2

        if isinstance(data, list):
            result = []
            current_size = 2  # []
            for item in data:
                item_json = json.dumps(item, default=str)
                if current_size + len(item_json) > max_size:
                    result.append({"_truncated": True, "_remaining": len(data) - len(result)})
                    break
                result.append(item)
                current_size += len(item_json)
            return result

        if isinstance(data, str):
            if len(data) > max_size:
                return data[:max_size - 20] + f"... [truncated {len(data) - max_size + 20} chars]"

        return data
