"""Enhanced Loop Execution"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class LoopBreakException(Exception):
    """Raised to break out of a loop."""

    pass


class LoopContinueException(Exception):
    """Raised to continue to next iteration."""

    pass


@dataclass
class ForEachConfig:
    """Configuration for ForEach loop."""

    collection: Union[List[Any], str]  # List or variable reference
    item_variable: str = "item"
    index_variable: str = "index"
    parallel: bool = False
    max_parallel: int = 5
    continue_on_error: bool = False
    steps: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ForEach config to dictionary."""
        return {
            "collection": self.collection,
            "item_variable": self.item_variable,
            "index_variable": self.index_variable,
            "parallel": self.parallel,
            "max_parallel": self.max_parallel,
            "continue_on_error": self.continue_on_error,
            "steps": self.steps,
        }


@dataclass
class WhileConfig:
    """Configuration for While loop."""

    condition: str  # Expression to evaluate
    max_iterations: int = 100
    delay_ms: int = 0  # Delay between iterations
    steps: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert While config to dictionary."""
        return {
            "condition": self.condition,
            "max_iterations": self.max_iterations,
            "delay_ms": self.delay_ms,
            "steps": self.steps,
        }


@dataclass
class LoopResult:
    """Result of loop execution."""

    success: bool
    iterations: int = 0
    results: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    break_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert loop result to dictionary."""
        return {
            "success": self.success,
            "iterations": self.iterations,
            "results": self.results,
            "errors": self.errors,
            "break_reason": self.break_reason,
        }


class LoopExecutor:
    """
    Execute enhanced loop constructs.

    Supports:
    - ForEach with parallel execution
    - While with condition evaluation
    - Break/Continue control
    """

    def __init__(
        self,
        execute_steps: Callable[[List[Dict], Dict], Any],
        evaluate_condition: Callable[[str, Dict], bool],
    ):
        """
        Initialize executor.

        Args:
            execute_steps: Function to execute a list of steps
            evaluate_condition: Function to evaluate a condition string
        """
        self.execute_steps = execute_steps
        self.evaluate_condition = evaluate_condition

    async def execute_foreach(
        self,
        config: ForEachConfig,
        context: Dict[str, Any],
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> LoopResult:
        """
        Execute ForEach loop.

        Args:
            config: ForEach configuration
            context: Execution context
            cancel_check: Optional cancellation check

        Returns:
            LoopResult with iteration results
        """
        # Resolve collection
        collection = config.collection
        if isinstance(collection, str) and collection.startswith("${"):
            var_name = collection[2:-1]
            collection = self._get_nested_value(context, var_name) or []

        if not isinstance(collection, list):
            return LoopResult(
                success=False,
                errors=[f"Collection is not a list: {type(collection)}"],
            )

        results = []
        errors = []

        if config.parallel:
            # Parallel execution
            results, errors = await self._execute_parallel(
                collection=collection,
                config=config,
                context=context,
                cancel_check=cancel_check,
            )
        else:
            # Sequential execution
            for index, item in enumerate(collection):
                if cancel_check and cancel_check():
                    return LoopResult(
                        success=False,
                        iterations=index,
                        results=results,
                        break_reason="cancelled",
                    )

                # Set loop variables
                iter_context = context.copy()
                iter_context[config.item_variable] = item
                iter_context[config.index_variable] = index

                try:
                    result = await self.execute_steps(config.steps, iter_context)
                    results.append(result)
                except LoopBreakException as e:
                    return LoopResult(
                        success=True,
                        iterations=index + 1,
                        results=results,
                        break_reason=str(e) or "break",
                    )
                except LoopContinueException:
                    continue
                except Exception as e:
                    errors.append(f"Iteration {index}: {e}")
                    if not config.continue_on_error:
                        return LoopResult(
                            success=False,
                            iterations=index + 1,
                            results=results,
                            errors=errors,
                        )

        return LoopResult(
            success=len(errors) == 0,
            iterations=len(collection),
            results=results,
            errors=errors,
        )

    async def _execute_parallel(
        self,
        collection: List[Any],
        config: ForEachConfig,
        context: Dict[str, Any],
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> tuple:
        """Execute iterations in parallel with concurrency limit."""
        semaphore = asyncio.Semaphore(config.max_parallel)
        results = [None] * len(collection)
        errors = []

        async def execute_one(index: int, item: Any) -> None:
            async with semaphore:
                if cancel_check and cancel_check():
                    return

                iter_context = context.copy()
                iter_context[config.item_variable] = item
                iter_context[config.index_variable] = index

                try:
                    result = await self.execute_steps(config.steps, iter_context)
                    results[index] = result
                except Exception as e:
                    errors.append(f"Iteration {index}: {e}")

        tasks = [
            execute_one(i, item)
            for i, item in enumerate(collection)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results, errors

    async def execute_while(
        self,
        config: WhileConfig,
        context: Dict[str, Any],
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> LoopResult:
        """
        Execute While loop.

        Args:
            config: While configuration
            context: Execution context
            cancel_check: Optional cancellation check

        Returns:
            LoopResult with iteration results
        """
        results = []
        errors = []
        iteration = 0

        while iteration < config.max_iterations:
            # Check cancellation
            if cancel_check and cancel_check():
                return LoopResult(
                    success=False,
                    iterations=iteration,
                    results=results,
                    break_reason="cancelled",
                )

            # Evaluate condition
            try:
                should_continue = self.evaluate_condition(config.condition, context)
            except Exception as e:
                return LoopResult(
                    success=False,
                    iterations=iteration,
                    errors=[f"Condition evaluation failed: {e}"],
                )

            if not should_continue:
                break

            # Execute steps
            try:
                result = await self.execute_steps(config.steps, context)
                results.append(result)
            except LoopBreakException as e:
                return LoopResult(
                    success=True,
                    iterations=iteration + 1,
                    results=results,
                    break_reason=str(e) or "break",
                )
            except LoopContinueException:
                iteration += 1
                continue
            except Exception as e:
                errors.append(f"Iteration {iteration}: {e}")
                return LoopResult(
                    success=False,
                    iterations=iteration + 1,
                    results=results,
                    errors=errors,
                )

            iteration += 1

            # Delay between iterations
            if config.delay_ms > 0:
                await asyncio.sleep(config.delay_ms / 1000)

        # Check if max iterations reached
        if iteration >= config.max_iterations:
            return LoopResult(
                success=True,
                iterations=iteration,
                results=results,
                break_reason="max_iterations_reached",
            )

        return LoopResult(
            success=True,
            iterations=iteration,
            results=results,
        )

    @staticmethod
    def _get_nested_value(obj: Dict, path: str) -> Any:
        """Get nested value from dict using dot notation."""
        from core.engine.variable_resolver import VariableResolver
        return VariableResolver.get_nested_value(obj, path)
