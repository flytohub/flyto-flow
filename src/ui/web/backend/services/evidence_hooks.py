"""
Evidence Hooks

ExecutorHooks implementation for evidence collection.
Captures context before/after each step for debugging features.

Also handles:
- Screenshot capture based on ScreenshotMode
- Browser context tracking for screenshot capability
"""

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

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
    from services.evidence_collector import EvidenceCollector, ScreenshotMode

logger = logging.getLogger(__name__)


class EvidenceHooks(ExecutorHooks):
    """
    Hooks for collecting execution evidence.

    Captures:
    - Context before each step
    - Context after each step
    - Step parameters and results
    - Timing information
    """

    def __init__(self, collector: "EvidenceCollector"):
        """
        Initialize evidence hooks.

        Args:
            collector: Evidence collector instance
        """
        self._collector = collector
        self._current_context: Dict[str, Any] = {}

    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set the current execution context.

        Called by the engine before step execution to provide
        current context state.

        Args:
            context: Current execution context
        """
        self._current_context = context

    def on_workflow_start(self, context: HookContext) -> HookResult:
        """Initialize evidence collection for workflow."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._collector.initialize())
            logger.debug(f"Evidence collector initialized at {self._collector.evidence_dir}")
        except Exception as e:
            logger.warning(f"Failed to initialize evidence collector: {e}")

        return HookResult.continue_execution()

    def on_workflow_complete(self, context: HookContext) -> None:
        """Finalize evidence collection."""
        logger.debug(f"Evidence collection complete for {self._collector.execution_id}")

    def on_workflow_failed(self, context: HookContext) -> None:
        """Handle workflow failure in evidence."""
        logger.debug(f"Evidence collection: workflow failed for {self._collector.execution_id}")

    def on_pre_execute(self, context: HookContext) -> HookResult:
        """
        Record step start with context before.

        Args:
            context: Hook context with step info

        Returns:
            HookResult to continue execution
        """
        import asyncio

        step_id = context.step_id or f"step_{context.step_index}"
        step_index = context.step_index or 0
        module_id = context.module_id or "unknown"
        params = context.params or {}

        # Get current context from the hook context or stored context
        current_ctx = getattr(context, 'variables', None) or self._current_context

        try:
            loop = asyncio.get_event_loop()
            loop.create_task(
                self._collector.on_step_start(
                    step_id=step_id,
                    step_index=step_index,
                    module_id=module_id,
                    params=params,
                    context=dict(current_ctx) if current_ctx else {},
                )
            )
        except Exception as e:
            logger.warning(f"Failed to record step start: {e}")

        return HookResult.continue_execution()

    def on_post_execute(self, context: HookContext) -> HookResult:
        """
        Record step completion with context after.

        Also tracks browser context for screenshot capture:
        - browser.launch: Sets browser context from result
        - browser.close: Clears browser context

        Args:
            context: Hook context with result/error

        Returns:
            HookResult to continue execution
        """
        import asyncio

        step_id = context.step_id or f"step_{context.step_index}"
        module_id = context.module_id or ""

        # Get context after execution
        current_ctx = getattr(context, 'variables', None) or self._current_context

        # Get result or error
        result = context.result if hasattr(context, 'result') else None
        error = None

        if context.error:
            error = str(context.error_message or context.error)

        # Track browser context for screenshots
        self._update_browser_context(module_id, current_ctx, error)

        try:
            loop = asyncio.get_event_loop()
            loop.create_task(
                self._collector.on_step_complete(
                    step_id=step_id,
                    context=dict(current_ctx) if current_ctx else {},
                    result=result,
                    error=error,
                )
            )
        except Exception as e:
            logger.warning(f"Failed to record step completion: {e}")

        return HookResult.continue_execution()

    def _update_browser_context(
        self,
        module_id: str,
        context: Dict[str, Any],
        error: Optional[str],
    ) -> None:
        """
        Update browser context based on module execution.

        Args:
            module_id: Module that was executed
            context: Current execution context
            error: Error message if step failed
        """
        # browser.launch: Set browser context for screenshots
        if module_id == "browser.launch" and not error:
            browser = context.get("browser")
            if browser:
                self._collector.set_browser_context(browser)
                logger.debug("Browser context set from browser.launch")

        # browser.close: Clear browser context
        elif module_id == "browser.close":
            self._collector.clear_browser_context()
            logger.debug("Browser context cleared after browser.close")

    def on_error(self, context: HookContext) -> HookResult:
        """Handle step error."""
        return HookResult.continue_execution()

    def on_retry(self, context: HookContext) -> HookResult:
        """Handle retry attempt."""
        return HookResult.continue_execution()


def create_evidence_hooks(
    execution_id: str,
    screenshot_mode: Optional[str] = None,
) -> Optional[EvidenceHooks]:
    """
    Create evidence hooks for an execution.

    Args:
        execution_id: Execution identifier
        screenshot_mode: Screenshot mode ("off", "on_error", "all")

    Returns:
        EvidenceHooks instance or None if creation fails
    """
    try:
        from services.evidence_collector import get_evidence_collector, ScreenshotMode

        # Parse screenshot mode string to enum
        mode = None
        if screenshot_mode:
            try:
                mode = ScreenshotMode(screenshot_mode)
            except ValueError:
                logger.warning(f"Invalid screenshot_mode: {screenshot_mode}, using default")

        collector = get_evidence_collector(execution_id, screenshot_mode=mode)
        return EvidenceHooks(collector)
    except Exception as e:
        logger.warning(f"Failed to create evidence hooks: {e}")
        return None
