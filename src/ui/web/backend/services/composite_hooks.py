"""
Composite Hooks

Combines multiple ExecutorHooks implementations into one.
Used to run both StepTrackingHooks and EvidenceHooks during execution.
"""

import logging
from typing import Any, List, Optional, TYPE_CHECKING

# Import the runtime contract from the installed package when available.
try:
    from core.engine.hooks import ExecutorHooks, HookContext, HookResult
except ImportError:
    class ExecutorHooks:
        """Fallback ExecutorHooks interface when core is unavailable."""
        pass

    class HookContext:
        """Fallback HookContext when core is unavailable."""
        pass

    class HookResult:
        """Fallback HookResult when core is unavailable."""
        @classmethod
        def continue_execution(cls):
            """Create a result that allows execution to continue."""
            return cls()

        @classmethod
        def stop_execution(cls, reason: str = ""):
            """Create a result that stops execution with an optional reason."""
            result = cls()
            result._should_stop = True
            result._reason = reason
            return result

logger = logging.getLogger(__name__)


class CompositeHooks(ExecutorHooks):
    """
    Combines multiple ExecutorHooks into one.

    All hooks are called in order. If any hook returns stop_execution,
    subsequent hooks are still called but execution will stop.
    """

    def __init__(self, hooks: List[ExecutorHooks]):
        """
        Initialize composite hooks.

        Args:
            hooks: List of ExecutorHooks to combine
        """
        self._hooks = [h for h in hooks if h is not None]

    def add_hooks(self, hooks: ExecutorHooks) -> None:
        """Add hooks to the composite."""
        if hooks is not None:
            self._hooks.append(hooks)

    def on_workflow_start(self, context: HookContext) -> HookResult:
        """Call on_workflow_start on all hooks."""
        result = HookResult.continue_execution()
        for hooks in self._hooks:
            try:
                if hasattr(hooks, 'on_workflow_start'):
                    r = hooks.on_workflow_start(context)
                    if r and hasattr(r, '_should_stop') and r._should_stop:
                        result = r
            except Exception as e:
                logger.warning(f"Hook on_workflow_start failed: {e}")
        return result

    def on_workflow_complete(self, context: HookContext) -> None:
        """Call on_workflow_complete on all hooks."""
        for hooks in self._hooks:
            try:
                if hasattr(hooks, 'on_workflow_complete'):
                    hooks.on_workflow_complete(context)
            except Exception as e:
                logger.warning(f"Hook on_workflow_complete failed: {e}")

    def on_workflow_failed(self, context: HookContext) -> None:
        """Call on_workflow_failed on all hooks."""
        for hooks in self._hooks:
            try:
                if hasattr(hooks, 'on_workflow_failed'):
                    hooks.on_workflow_failed(context)
            except Exception as e:
                logger.warning(f"Hook on_workflow_failed failed: {e}")

    def on_pre_execute(self, context: HookContext) -> HookResult:
        """Call on_pre_execute on all hooks."""
        result = HookResult.continue_execution()
        for hooks in self._hooks:
            try:
                if hasattr(hooks, 'on_pre_execute'):
                    r = hooks.on_pre_execute(context)
                    if r and hasattr(r, '_should_stop') and r._should_stop:
                        result = r
            except Exception as e:
                logger.warning(f"Hook on_pre_execute failed: {e}")
        return result

    def on_post_execute(self, context: HookContext) -> HookResult:
        """Call on_post_execute on all hooks."""
        result = HookResult.continue_execution()
        for hooks in self._hooks:
            try:
                if hasattr(hooks, 'on_post_execute'):
                    r = hooks.on_post_execute(context)
                    if r and hasattr(r, '_should_stop') and r._should_stop:
                        result = r
            except Exception as e:
                logger.warning(f"Hook on_post_execute failed: {e}")
        return result

    def on_error(self, context: HookContext) -> HookResult:
        """Call on_error on all hooks."""
        result = HookResult.continue_execution()
        for hooks in self._hooks:
            try:
                if hasattr(hooks, 'on_error'):
                    r = hooks.on_error(context)
                    if r and hasattr(r, '_should_stop') and r._should_stop:
                        result = r
            except Exception as e:
                logger.warning(f"Hook on_error failed: {e}")
        return result

    def on_retry(self, context: HookContext) -> HookResult:
        """Call on_retry on all hooks."""
        result = HookResult.continue_execution()
        for hooks in self._hooks:
            try:
                if hasattr(hooks, 'on_retry'):
                    r = hooks.on_retry(context)
                    if r and hasattr(r, '_should_stop') and r._should_stop:
                        result = r
            except Exception as e:
                logger.warning(f"Hook on_retry failed: {e}")
        return result
