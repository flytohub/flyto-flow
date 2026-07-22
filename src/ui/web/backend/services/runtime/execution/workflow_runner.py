"""
Workflow Runner — Execute workflows and manage engine lifecycle.

Extracted from ExecutionManager to keep service.py focused on orchestration.
Contains _run_workflow, _create_workflow_engine, _resolve_ui_vars_in_steps,
and related helpers.
"""

import asyncio
import inspect
import logging
import re
import sys
from typing import Any, Dict, List, Optional

import yaml

from services.runtime.execution.enums import ExecutionStatus
from services.runtime.execution.models import ExecutionInfo
from services.runtime.execution.utils import utc_now

# Browser idle timeout: keep browser alive after workflow completion
BROWSER_IDLE_TIMEOUT = 300  # 5 minutes
from services.runtime.execution.hooks_setup import setup_execution_hooks
from services.runtime.execution.persistence import persist_execution_status
from services.runtime.execution.template_loader import load_template_definitions
from services.runtime.execution.error_handler import trigger_error_workflow, ERROR_WORKFLOW_MARKER

logger = logging.getLogger(__name__)

# Maximum time (seconds) for a single workflow execution.
# Default 540s (9 min) leaves time for orderly local cleanup.
import os
MAX_EXECUTION_TIMEOUT = int(os.environ.get('FLYTO_MAX_EXECUTION_TIMEOUT', '540'))


async def run_workflow(
    manager: Any,
    execution_id: str,
    workflow_yaml: str,
    variables: Dict[str, Any],
    start_step: Optional[int] = None,
    end_step: Optional[int] = None,
    workflow_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Execute workflow and update status.

    Args:
        manager: ExecutionManager instance (provides _executions dict)
        execution_id: Unique execution ID
        workflow_yaml: YAML workflow definition
        variables: Runtime variables
        start_step: Optional start step index (0-based)
        end_step: Optional end step index (0-based)
        workflow_data: Pre-parsed workflow data
    """
    info = manager._executions.get(execution_id)
    if not info:
        return

    info.status = ExecutionStatus.RUNNING
    info.start_time = utc_now()

    # Update SQLite status
    try:
        from gateway.storage import ExecutionRepository
        ExecutionRepository.update_execution(execution_id=execution_id, status="running")
    except Exception as e:
        logger.warning(f"Failed to update SQLite status: {e}")

    # Set up hooks
    combined_hooks = setup_execution_hooks(info)

    try:
        # Import and run workflow engine
        logger.debug(f"Creating workflow engine for {execution_id}")
        engine = await create_workflow_engine(
            manager, info, workflow_yaml, variables, workflow_data,
            start_step, end_step, combined_hooks
        )
        info.engine = engine

        logger.debug(f"Starting engine.execute() for {execution_id} (timeout={MAX_EXECUTION_TIMEOUT}s)")
        result = await asyncio.wait_for(engine.execute(), timeout=MAX_EXECUTION_TIMEOUT)
        logger.debug(f"engine.execute() completed for {execution_id}, result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")

        if info.status == ExecutionStatus.CANCELLED:
            return

        info.status = ExecutionStatus.COMPLETED
        info.result = result
        info.current_step = info.total_steps

        # Post-process: inject download URLs for file outputs
        try:
            from services.runtime.execution.file_output import process_execution_outputs
            workspace_id = info.metadata.get("workspace_id") or info.workspace_id
            await process_execution_outputs(result, info.node_outputs, workspace_id=workspace_id)
        except Exception as e:
            logger.debug(f"File output processing skipped: {e}")

        # Keep browser alive after completion for interactive use
        has_browser = info.metadata.get("has_browser", False)
        if has_browser:
            asyncio.ensure_future(
                _start_browser_idle_timer(execution_id, info)
            )

        logger.debug(f"Execution {execution_id} completed successfully")
        logger.info(f"Execution {execution_id} completed successfully")

    except asyncio.TimeoutError:
        logger.error(f"Execution {execution_id} TIMED OUT after {MAX_EXECUTION_TIMEOUT}s")
        if info.status != ExecutionStatus.CANCELLED:
            info.status = ExecutionStatus.FAILED
            info.error = f"Execution timed out after {MAX_EXECUTION_TIMEOUT} seconds"

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Execution {execution_id} FAILED: {e}")
        logger.error(f"Traceback: {tb}")
        if info.status != ExecutionStatus.CANCELLED:
            info.status = ExecutionStatus.FAILED
            info.error = str(e)
            # Extract step_id from error chain
            cause = e
            while cause:
                if hasattr(cause, 'step_id'):
                    info.error_step_id = cause.step_id
                    break
                cause = cause.__cause__

            logger.error(f"Execution {execution_id} failed: {e}")

            # Trigger error workflow if configured (and not already an error workflow)
            if not info.metadata.get(ERROR_WORKFLOW_MARKER):
                await trigger_error_workflow(manager, info, str(e), tb, workflow_data)

    finally:
        info.end_time = utc_now()
        info.engine = None
        await _cleanup_execution(info)
        await persist_execution_status(info)

        # Auto blueprint feedback: report outcome OR learn new blueprint
        await _auto_blueprint_feedback(info, workflow_data)

        # Push WebSocket notification
        try:
            from services.websocket_manager import get_connection_manager
            ws_manager = get_connection_manager()
            await ws_manager.send_log(execution_id, {
                "type": "execution_complete",
                "execution_id": execution_id,
                "status": info.status.value,
                "error": info.error if info.status == ExecutionStatus.FAILED else None,
            })
        except Exception as e:
            logger.debug(f"Failed to send WebSocket notification: {e}")


async def _auto_blueprint_feedback(
    info: ExecutionInfo,
    workflow_data: Optional[Dict[str, Any]],
) -> None:
    """System-level blueprint feedback — no LLM dependency.

    Two paths:
    1. Workflow FROM a blueprint -> auto-report success/failure
    2. Workflow NOT from a blueprint + succeeded -> auto-learn as new blueprint

    This closes the entire evolution loop at the system level:
    create -> use -> report -> score -> rank -> repeat
    """
    if info.status not in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED):
        return

    source_bp_id = info.metadata.get("source_blueprint_id")
    success = info.status == ExecutionStatus.COMPLETED

    try:
        from flyto_blueprint import get_engine
        engine = get_engine()

        if source_bp_id:
            # Path 1: Report outcome for blueprint-generated workflow
            result = engine.report_outcome(
                source_bp_id, success,
                execution_id=info.execution_id,
            )
            logger.info(
                "Auto-reported blueprint outcome: %s success=%s score=%s",
                source_bp_id, success, result.get("score"),
            )

        elif success and workflow_data:
            # Path 2: Auto-learn from successful non-blueprint workflow
            steps = workflow_data.get("steps", [])
            if len(steps) >= 3:
                learn_result = engine.learn_from_execution(
                    workflow=workflow_data,
                )
                action = learn_result.get("action", "created")
                bp_id = (
                    learn_result.get("blueprint_id")
                    or learn_result.get("data", {}).get("id", "?")
                )
                logger.info(
                    "Auto-learned blueprint from execution %s: %s (action=%s)",
                    info.execution_id, bp_id, action,
                )
    except Exception as e:
        logger.debug("Blueprint auto-feedback failed: %s", e)


def _ensure_module_registry():
    """Ensure ModuleRegistry is populated; force re-registration if near-empty."""
    try:
        from core.modules.registry import ModuleRegistry
        if ModuleRegistry.module_count() < 10:
            logger.warning("ModuleRegistry near-empty (%d), forcing re-registration...",
                           ModuleRegistry.module_count())
            import core.modules.atomic as _atomic
            _atomic._registered = False
            for key in [k for k in list(sys.modules.keys()) if k.startswith('core.modules.atomic.')]:
                del sys.modules[key]
            _atomic.register_all()
            logger.info("Re-registered %d modules", ModuleRegistry.module_count())
    except Exception as e:
        logger.warning("Module pre-check failed: %s", e)


def _import_workflow_engine():
    """Import WorkflowEngine from the installed flyto-core package."""
    from core.engine import WorkflowEngine
    return WorkflowEngine


async def create_workflow_engine(
    manager: Any,
    info: ExecutionInfo,
    workflow_yaml: str,
    variables: Dict[str, Any],
    workflow_data: Optional[Dict[str, Any]],
    start_step: Optional[int],
    end_step: Optional[int],
    hooks: Optional[Any],
) -> Any:
    """Create and configure WorkflowEngine.

    Args:
        manager: ExecutionManager instance (for pause/checkpoint callbacks)
        info: ExecutionInfo for the current execution
        workflow_yaml: YAML workflow definition
        variables: Runtime variables
        workflow_data: Pre-parsed workflow data
        start_step: Optional start step index
        end_step: Optional end step index
        hooks: Combined execution hooks
    """
    _ensure_module_registry()
    WorkflowEngine = _import_workflow_engine()

    # Parse workflow if needed
    if workflow_data is None:
        workflow_data = yaml.safe_load(workflow_yaml)

    # Resolve [[variable]] placeholders in step params using UI input values
    # Desktop frontend wraps inputs under {"ui": {"base": "..."}},
    # but mobile app sends flat {"base": "..."} — support both.
    ui_values = (variables or {}).get("ui", {})
    if not ui_values and variables:
        # Flat params from mobile app — use all non-internal variables as ui values
        ui_values = {k: v for k, v in variables.items() if not k.startswith("_")}
    if ui_values:
        resolve_ui_vars_in_steps(workflow_data.get("steps", []), ui_values)

    steps = workflow_data.get("steps", [])
    info.total_steps = len(steps)

    # Initialize node_order and node_states for frontend rendering
    info.node_order = [step.get("id", f"step_{i}") for i, step in enumerate(steps)]
    info.node_states = {node_id: "pending" for node_id in info.node_order}
    logger.info(f"[ExecutionService] Initialized node_order: {info.node_order}")
    logger.info(f"[ExecutionService] Initialized node_states: {info.node_states}")

    # Build engine kwargs
    engine_kwargs = {"start_step": start_step, "end_step": end_step}
    sig = inspect.signature(WorkflowEngine.__init__)

    # Add hooks if supported
    if hooks and "hooks" in sig.parameters:
        engine_kwargs["hooks"] = hooks
        logger.debug(f"Passing hooks to engine: {type(hooks).__name__}")

    # Set up pause callback if supported
    if "pause_callback" in sig.parameters:
        pause_callback = await _create_pause_callback(info)
        if pause_callback:
            engine_kwargs["pause_callback"] = pause_callback

    # Set up checkpoint callback if supported
    if "checkpoint_callback" in sig.parameters:
        checkpoint_callback = await _create_checkpoint_callback(
            info.execution_id, workflow_yaml
        )
        if checkpoint_callback:
            engine_kwargs["checkpoint_callback"] = checkpoint_callback

    # Step mode and initial context
    if "step_mode" in sig.parameters and info.metadata.get('step_mode'):
        engine_kwargs["step_mode"] = True

    # Pre-load template definitions for template.invoke steps
    initial_context = info.metadata.get('initial_context', {})
    logger.debug(f"Checking for template.invoke steps in {len(steps)} steps")

    # Use embedded definitions from snapshot (publisher's own sub-templates)
    embedded_templates = workflow_data.get("embedded_templates")

    from services.runtime.execution.template_loader import TemplateDependencyError
    try:
        template_definitions = await load_template_definitions(
            steps, info.workspace_id, embedded_templates=embedded_templates,
        )
    except TemplateDependencyError as e:
        logger.error(f"Template dependency error: {e}")
        info.status = ExecutionStatus.FAILED
        info.error = str(e)
        info.completed_at = utc_now()
        await persist_execution_status(info)
        raise

    logger.debug(f"Loaded template_definitions: {list(template_definitions.keys())}")
    if template_definitions:
        initial_context['template_definitions'] = template_definitions
        logger.debug(f"Pre-loaded {len(template_definitions)} template definitions")

    # Keep browser alive after execution so users can interact
    initial_context['keep_browser_alive'] = True

    if "initial_context" in sig.parameters and initial_context:
        engine_kwargs["initial_context"] = initial_context

    return WorkflowEngine(workflow_data, variables, **engine_kwargs)


def resolve_ui_vars_in_steps(steps: List[Dict[str, Any]], ui_values: Dict[str, Any]) -> None:
    """Replace [[variable]] and {{variable}} placeholders in step params with actual UI input values.

    Two-phase resolution (using shared VariableResolver.resolve_tvars from flyto-core):
    1. [[var]] → look up _tvars[var] first, fallback to ui_values for backward compat
    2. {{var}} → look up ui_values[var] (user-entered form values)

    This ensures [[var]] works regardless of value source:
    - UI Input: _tvars[var] = "{{input}}" → phase 1 expands to "{{input}}" → phase 2 resolves
    - Previous Step: _tvars[var] = "${steps.x.result}" → phase 1 expands → engine resolves ${...}
    - Fixed Value: _tvars[var] = "hello" → phase 1 expands → done
    """
    from core.engine.variable_resolver import VariableResolver

    mustache_re = re.compile(r'\{\{(\w+)\}\}')

    def _resolve_mustache(value):
        """Phase 2: Replace {{var}} using ui_values."""
        if isinstance(value, str) and '{{' in value:
            def _sub(m):
                name = m.group(1)
                return str(ui_values[name]) if name in ui_values else m.group(0)
            return mustache_re.sub(_sub, value)
        if isinstance(value, dict):
            return {k: _resolve_mustache(v) for k, v in value.items() if k != '_tvars'}
        if isinstance(value, list):
            return [_resolve_mustache(item) for item in value]
        return value

    for step in steps:
        if "params" not in step or not isinstance(step["params"], dict):
            continue

        params = step["params"]

        # Phase 1: [[var]] → _tvars lookup (or ui_values fallback for backward compat)
        step["params"] = VariableResolver.resolve_tvars(params, fallback=ui_values)
        # Phase 2: {{var}} → ui_values lookup (resolves user-entered form values)
        step["params"] = _resolve_mustache(step["params"])

        # Also resolve in flow control fields
        for field in ("run_if", "skip_if", "foreach"):
            if field in step and isinstance(step[field], str):
                val = step[field]
                if '[[' in val:
                    tvars = params.get("_tvars") or {}
                    val = VariableResolver.TVARS_PATTERN.sub(
                        lambda m: str(tvars.get(m.group(1), ui_values.get(m.group(1), m.group(0)))),
                        val,
                    )
                if '{{' in val:
                    val = mustache_re.sub(lambda m: str(ui_values.get(m.group(1), m.group(0))), val)
                step[field] = val


async def _create_pause_callback(info: ExecutionInfo) -> Optional[callable]:
    """Create pause callback for execution control."""
    try:
        from services.runtime.execution_control import get_execution_controller
        controller = get_execution_controller()
        controller.register_execution(info.execution_id)

        # Set breakpoints
        breakpoints = info.metadata.get('breakpoints', set())
        for bp_node_id in breakpoints:
            controller.set_breakpoint(info.execution_id, bp_node_id)

        # State sync callback
        def on_state_change(exec_id: str, state):
            if exec_id == info.execution_id and state:
                if state.status == "paused":
                    info.status = ExecutionStatus.PAUSED
                elif state.status == "running":
                    info.status = ExecutionStatus.RUNNING

        controller.add_state_callback(on_state_change)

        async def pause_callback(step_index, step_id, variables, node_outputs, internal_should_pause=False):
            return await controller.check_pause_point(
                execution_id=info.execution_id,
                step_index=step_index,
                step_id=step_id,
                variables=variables,
                node_outputs=node_outputs,
                internal_should_pause=internal_should_pause
            )

        return pause_callback
    except Exception as e:
        logger.warning(f"Failed to create pause callback: {e}")
        return None


async def _create_checkpoint_callback(
    execution_id: str, workflow_yaml: str = ""
) -> Optional[callable]:
    """Create checkpoint callback for state snapshots."""
    try:
        from services.checkpoint_service import get_checkpoint_service
        checkpoint_service = get_checkpoint_service()

        async def checkpoint_callback(step_index, step_id, checkpoint_data, status):
            # Embed workflow_yaml for resume support
            checkpoint_data['workflow_yaml'] = workflow_yaml
            await checkpoint_service.save_checkpoint(
                execution_id=execution_id,
                step_index=step_index,
                step_id=step_id,
                data=checkpoint_data,
                status=status
            )

        return checkpoint_callback
    except ImportError:
        return None


async def _cleanup_execution(info: ExecutionInfo) -> None:
    """Clean up resources after execution."""
    from services.credentials.service import CredentialService

    # Unregister from controller
    try:
        from services.runtime.execution_control import get_execution_controller
        controller = get_execution_controller()
        controller.unregister_execution(info.execution_id)
    except Exception as e:
        logger.debug(f"Failed to unregister execution controller: {e}")

    # Release concurrency slot
    try:
        from services.concurrency_manager import release_execution_slot
        await release_execution_slot(info.execution_id)
    except Exception as e:
        logger.warning(f"Failed to release concurrency slot: {e}")

    # Clean up evidence collector
    try:
        from services.evidence_collector import remove_evidence_collector
        remove_evidence_collector(info.execution_id)
    except Exception as e:
        logger.debug(f"Failed to remove evidence collector: {e}")

    # Clean up credential tokens
    try:
        if info.metadata.get('credential_tokens'):
            count = CredentialService.cleanup_execution_tokens(info.execution_id)
            if count > 0:
                logger.debug(f"Cleaned up {count} credential tokens for {info.execution_id}")
    except Exception as e:
        logger.warning(f"Failed to cleanup credential tokens: {e}")


# --- Browser Idle Timer ---
# Tracks active idle timers so user input can reset them
_browser_idle_timers: Dict[str, asyncio.Task] = {}


async def _start_browser_idle_timer(execution_id: str, info: ExecutionInfo) -> None:
    """Start an idle timer that closes the browser after BROWSER_IDLE_TIMEOUT seconds.

    Sends browser_idle event to frontend with countdown info.
    The timer can be reset by calling reset_browser_idle_timer().
    """
    # Cancel existing timer if any
    existing = _browser_idle_timers.pop(execution_id, None)
    if existing and not existing.done():
        existing.cancel()

    async def _idle_countdown():
        try:
            # Notify frontend via both execution WS and browser screencast WS
            try:
                from services.websocket_manager import get_connection_manager
                ws_manager = get_connection_manager()
                await ws_manager.send_log(execution_id, {
                    "type": "browser_idle",
                    "timeout_seconds": BROWSER_IDLE_TIMEOUT,
                })
            except Exception:
                pass
            try:
                from services.screencast import get_screencast_manager
                sc_manager = get_screencast_manager()
                await sc_manager._broadcast_json(execution_id, {
                    "type": "browser_idle",
                    "timeout_seconds": BROWSER_IDLE_TIMEOUT,
                })
            except Exception:
                pass

            logger.info(f"Browser idle timer started for {execution_id}: {BROWSER_IDLE_TIMEOUT}s")

            # Wait for timeout
            await asyncio.sleep(BROWSER_IDLE_TIMEOUT)

            # Timer expired — close browser
            logger.info(f"Browser idle timeout reached for {execution_id}, closing browser")
            try:
                from services.screencast import get_screencast_manager
                manager = get_screencast_manager()
                await manager.close_browser(execution_id)
            except Exception as e:
                logger.warning(f"Failed to close idle browser: {e}")

            _browser_idle_timers.pop(execution_id, None)

        except asyncio.CancelledError:
            logger.debug(f"Browser idle timer cancelled for {execution_id}")

    task = asyncio.ensure_future(_idle_countdown())
    _browser_idle_timers[execution_id] = task


def reset_browser_idle_timer(execution_id: str, info: Optional[ExecutionInfo] = None) -> bool:
    """Reset the browser idle timer (called when user interacts with browser).

    Returns True if timer was reset, False if no active timer.
    """
    existing = _browser_idle_timers.get(execution_id)
    if existing and not existing.done():
        existing.cancel()
        if info is None:
            try:
                from services.runtime.execution import get_execution_manager
                mgr = get_execution_manager()
                info = mgr.get_info(execution_id)
            except Exception:
                pass
        if info:
            asyncio.ensure_future(_start_browser_idle_timer(execution_id, info))
            return True
    return False


def cancel_browser_idle_timer(execution_id: str) -> None:
    """Cancel browser idle timer (e.g. when user manually closes browser)."""
    existing = _browser_idle_timers.pop(execution_id, None)
    if existing and not existing.done():
        existing.cancel()
