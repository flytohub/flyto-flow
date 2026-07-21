"""Sub-workflow Execution"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class SubworkflowMode(str, Enum):
    """How to execute sub-workflow."""

    INLINE = "inline"  # Execute within same execution context
    SPAWN = "spawn"  # Create new execution record
    ASYNC = "async"  # Fire and forget


@dataclass
class SubworkflowConfig:
    """Configuration for sub-workflow invocation."""

    workflow_id: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    mode: SubworkflowMode = SubworkflowMode.INLINE
    timeout_ms: int = 300000  # 5 minutes
    output_variable: Optional[str] = None
    on_error: str = "fail"  # fail, continue, skip

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dict."""
        return {
            "workflow_id": self.workflow_id,
            "inputs": self.inputs,
            "mode": self.mode.value,
            "timeout_ms": self.timeout_ms,
            "output_variable": self.output_variable,
            "on_error": self.on_error,
        }


@dataclass
class SubworkflowResult:
    """Result of sub-workflow execution."""

    success: bool
    execution_id: Optional[str] = None
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dict."""
        return {
            "success": self.success,
            "execution_id": self.execution_id,
            "outputs": self.outputs,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


class SubworkflowExecutor:
    """
    Execute sub-workflows within a parent workflow.

    Supports three modes:
    - inline: Execute within same context, share variables
    - spawn: Create separate execution, isolated context
    - async: Fire and forget, don't wait for result
    """

    def __init__(
        self,
        get_workflow: Callable[[str], Any],
        execute_workflow: Callable[[Any, Dict], Any],
    ):
        """
        Initialize executor.

        Args:
            get_workflow: Function to fetch workflow by ID
            execute_workflow: Function to execute a workflow
        """
        self.get_workflow = get_workflow
        self.execute_workflow = execute_workflow

    async def invoke(
        self,
        config: SubworkflowConfig,
        parent_context: Dict[str, Any],
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> SubworkflowResult:
        """
        Invoke a sub-workflow.

        Args:
            config: Sub-workflow configuration
            parent_context: Parent execution context
            cancel_check: Optional cancellation check function

        Returns:
            SubworkflowResult with outputs or error
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Get workflow definition
            workflow = await self.get_workflow(config.workflow_id)
            if not workflow:
                return SubworkflowResult(
                    success=False,
                    error=f"Workflow {config.workflow_id} not found",
                )

            # Resolve inputs from parent context
            resolved_inputs = self._resolve_inputs(config.inputs, parent_context)

            # Execute based on mode
            if config.mode == SubworkflowMode.ASYNC:
                # Fire and forget
                asyncio.create_task(
                    self._execute_async(workflow, resolved_inputs)
                )
                return SubworkflowResult(
                    success=True,
                    outputs={"status": "scheduled"},
                )

            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    self.execute_workflow(workflow, resolved_inputs),
                    timeout=config.timeout_ms / 1000,
                )
            except asyncio.TimeoutError:
                return SubworkflowResult(
                    success=False,
                    error=f"Sub-workflow timed out after {config.timeout_ms}ms",
                    duration_ms=config.timeout_ms,
                )

            duration_ms = int(
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            )

            return SubworkflowResult(
                success=True,
                execution_id=result.get("execution_id"),
                outputs=result.get("outputs", result),
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int(
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            )
            logger.error(f"Sub-workflow {config.workflow_id} failed: {e}")

            return SubworkflowResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

    async def _execute_async(
        self,
        workflow: Any,
        inputs: Dict[str, Any],
    ) -> None:
        """Execute workflow asynchronously (fire and forget)."""
        try:
            await self.execute_workflow(workflow, inputs)
        except Exception as e:
            logger.error(f"Async sub-workflow failed: {e}")

    def _resolve_inputs(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolve input variables from parent context."""
        resolved = {}
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("${"):
                # Variable reference
                var_name = value[2:-1]  # Remove ${ and }
                resolved[key] = self._get_nested_value(context, var_name)
            else:
                resolved[key] = value
        return resolved

    @staticmethod
    def _get_nested_value(obj: Dict, path: str) -> Any:
        """Get nested value from dict using dot notation."""
        from core.engine.variable_resolver import VariableResolver
        return VariableResolver.get_nested_value(obj, path)
