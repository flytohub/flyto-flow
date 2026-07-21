"""
Saga Executor

Executes Saga pattern with compensation for distributed transactions.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from services.runtime.flow.models import (
    CompensationConfig,
    CompensationOrder,
    CompensationResult,
    OnCompensationFailure,
    SagaConfig,
    SagaResult,
    SagaStep,
)

logger = logging.getLogger(__name__)


class SagaExecutor:
    """
    Executes Saga pattern with compensation.

    Usage:
        steps = [
            SagaStep(
                step_id="reserve",
                module_id="inventory.reserve",
                compensation=CompensationConfig(module_id="inventory.release"),
            ),
            SagaStep(
                step_id="charge",
                module_id="payment.charge",
                compensation=CompensationConfig(module_id="payment.refund"),
            ),
        ]

        executor = SagaExecutor(steps, config, step_executor)
        result = await executor.execute(context)
    """

    def __init__(
        self,
        steps: List[SagaStep],
        config: SagaConfig,
        step_executor: Callable[[str, Dict[str, Any]], Any],
        compensation_executor: Optional[Callable[[CompensationConfig, Dict[str, Any]], Any]] = None,
        alert_handler: Optional[Callable[[str, Exception], None]] = None,
    ):
        """
        Initialize Saga executor.

        Args:
            steps: List of saga steps
            config: Saga configuration
            step_executor: Function to execute steps
            compensation_executor: Function to execute compensations
            alert_handler: Function to send alerts
        """
        self.steps = steps
        self.config = config
        self.step_executor = step_executor
        self.compensation_executor = compensation_executor or step_executor
        self.alert_handler = alert_handler

    async def execute(
        self,
        context: Dict[str, Any],
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> SagaResult:
        """
        Execute the Saga.

        Args:
            context: Execution context
            cancel_check: Optional cancellation check

        Returns:
            Saga execution result
        """
        completed_steps: List[SagaStep] = []
        result = SagaResult(success=False, completed_steps=[])

        # Execute steps in order
        for step in self.steps:
            if cancel_check and cancel_check():
                result.error = "Cancelled"
                break

            try:
                step_result = await self._execute_step(step, context)
                step.executed = True
                step.result = step_result
                completed_steps.append(step)
                result.completed_steps.append(step.step_id)

            except Exception as e:
                logger.error(f"Saga step {step.step_id} failed: {e}")
                result.failed_step = step.step_id
                result.error = str(e)

                # Run compensations
                await self._run_compensations(completed_steps, context, result)
                return result

        # All steps succeeded
        result.success = True
        return result

    async def _execute_step(
        self,
        step: SagaStep,
        context: Dict[str, Any],
    ) -> Any:
        """Execute a single step."""
        if asyncio.iscoroutinefunction(self.step_executor):
            return await self.step_executor(step.step_id, context)
        else:
            return self.step_executor(step.step_id, context)

    async def _run_compensations(
        self,
        completed_steps: List[SagaStep],
        context: Dict[str, Any],
        result: SagaResult,
    ) -> None:
        """Run compensations for completed steps."""
        result.compensations_run = True

        # Order compensations
        steps_to_compensate = [s for s in completed_steps if s.compensation]

        if self.config.compensation_order == CompensationOrder.LIFO:
            steps_to_compensate = list(reversed(steps_to_compensate))

        # Execute compensations
        for step in steps_to_compensate:
            comp_result = await self._execute_compensation(
                step=step,
                context=context,
            )
            result.compensation_results.append(comp_result)

            if not comp_result.success:
                if self.config.on_compensation_failure == OnCompensationFailure.ABORT:
                    result.requires_manual_intervention = True
                    logger.error(
                        f"Compensation for {step.step_id} failed, aborting"
                    )
                    break

                elif self.config.on_compensation_failure == OnCompensationFailure.MANUAL:
                    result.requires_manual_intervention = True
                    logger.warning(
                        f"Compensation for {step.step_id} failed, "
                        "requires manual intervention"
                    )

    async def _execute_compensation(
        self,
        step: SagaStep,
        context: Dict[str, Any],
    ) -> CompensationResult:
        """Execute a single compensation with retries."""
        comp_config = step.compensation
        attempts = 0
        last_error: Optional[str] = None

        max_retries = min(
            comp_config.max_retries,
            self.config.max_compensation_retries,
        )

        while attempts < max_retries:
            attempts += 1

            try:
                # Add compensation context
                comp_context = {
                    **context,
                    "_compensation_for": step.step_id,
                    "_original_result": step.result,
                }

                if asyncio.iscoroutinefunction(self.compensation_executor):
                    await self.compensation_executor(comp_config, comp_context)
                else:
                    self.compensation_executor(comp_config, comp_context)

                logger.info(
                    f"Compensation for {step.step_id} succeeded "
                    f"(attempt {attempts})"
                )

                return CompensationResult(
                    step_id=step.step_id,
                    success=True,
                    attempts=attempts,
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Compensation for {step.step_id} failed "
                    f"(attempt {attempts}/{max_retries}): {e}"
                )

                # Alert on each failure if configured
                if (
                    self.config.on_compensation_failure == OnCompensationFailure.ALERT
                    and self.alert_handler
                ):
                    self.alert_handler(
                        f"Compensation failed for {step.step_id}",
                        e,
                    )

        return CompensationResult(
            step_id=step.step_id,
            success=False,
            attempts=attempts,
            error=last_error,
        )
