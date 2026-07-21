"""
Try-Catch-Finally Executor

Executes Try-Catch-Finally blocks for workflow error handling.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

from services.error_taxonomy import ErrorClassifier, ClassifiedError
from services.runtime.flow.models import TryCatchFinallyConfig, TryCatchFinallyResult

logger = logging.getLogger(__name__)


class TryCatchFinallyExecutor:
    """
    Executes Try-Catch-Finally blocks.

    Usage:
        config = TryCatchFinallyConfig(
            try_steps=["step1", "step2"],
            catch_steps=["error_handler"],
            finally_steps=["cleanup"],
        )

        executor = TryCatchFinallyExecutor(config, step_executor)
        result = await executor.execute(context)
    """

    def __init__(
        self,
        config: TryCatchFinallyConfig,
        step_executor: Callable[[str, Dict[str, Any]], Any],
    ):
        """
        Initialize executor.

        Args:
            config: Try-Catch-Finally configuration
            step_executor: Function to execute a step by ID
        """
        self.config = config
        self.step_executor = step_executor

    async def execute(
        self,
        context: Dict[str, Any],
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> TryCatchFinallyResult:
        """
        Execute the Try-Catch-Finally block.

        Args:
            context: Execution context
            cancel_check: Optional function to check for cancellation

        Returns:
            Execution result
        """
        result = TryCatchFinallyResult(
            success=False,
            try_completed=False,
            catch_executed=False,
            finally_executed=False,
        )

        classified_error: Optional[ClassifiedError] = None

        # Execute TRY block
        try:
            for step_id in self.config.try_steps:
                if cancel_check and cancel_check():
                    raise asyncio.CancelledError("Cancelled")

                step_result = await self._execute_step(step_id, context)
                result.try_results[step_id] = step_result

            result.try_completed = True
            result.success = True

        except asyncio.CancelledError:
            raise  # Don't catch cancellation

        except Exception as e:
            classified_error = ErrorClassifier.classify(e)
            result.error = str(e)
            result.error_category = classified_error.category

            logger.warning(
                f"Try block failed: {e} "
                f"(category: {classified_error.category.value})"
            )

            # Check if we should catch this error
            should_catch = self._should_catch(classified_error)

            if should_catch and self.config.catch_steps:
                # Execute CATCH block
                try:
                    result.catch_executed = True

                    # Add error info to context for catch handlers
                    catch_context = {
                        **context,
                        "_error": str(e),
                        "_error_category": classified_error.category.value,
                        "_error_fingerprint": classified_error.fingerprint,
                    }

                    for step_id in self.config.catch_steps:
                        if cancel_check and cancel_check():
                            raise asyncio.CancelledError("Cancelled")

                        step_result = await self._execute_step(step_id, catch_context)
                        result.catch_results[step_id] = step_result

                    # Catch succeeded, mark overall as success
                    result.success = True

                except asyncio.CancelledError:
                    raise

                except Exception as catch_error:
                    logger.error(f"Catch block also failed: {catch_error}")
                    result.error = f"Catch failed: {catch_error}"

        # Execute FINALLY block (always runs)
        finally:
            if self.config.finally_steps:
                try:
                    result.finally_executed = True

                    for step_id in self.config.finally_steps:
                        # Don't check cancellation in finally - must complete
                        step_result = await self._execute_step(step_id, context)
                        result.finally_results[step_id] = step_result

                except Exception as finally_error:
                    logger.error(f"Finally block failed: {finally_error}")
                    # Finally error doesn't change success status
                    # but we log it

        return result

    async def _execute_step(
        self,
        step_id: str,
        context: Dict[str, Any],
    ) -> Any:
        """Execute a single step."""
        if asyncio.iscoroutinefunction(self.step_executor):
            return await self.step_executor(step_id, context)
        else:
            return self.step_executor(step_id, context)

    def _should_catch(self, error: ClassifiedError) -> bool:
        """Check if error should be caught."""
        if not self.config.catch_errors:
            return True  # Catch all

        return error.category in self.config.catch_errors
