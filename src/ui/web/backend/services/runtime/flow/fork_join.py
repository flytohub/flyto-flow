"""Fork/Join Parallel Execution"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class JoinStrategy(str, Enum):
    """Strategy for joining parallel branches."""

    ALL = "all"  # Wait for all branches
    ANY = "any"  # Wait for any branch to complete
    FIRST_SUCCESS = "first_success"  # Wait for first successful branch


@dataclass
class Branch:
    """A branch in a fork/join construct."""

    id: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    condition: Optional[str] = None  # Optional condition to execute

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the branch to a dictionary."""
        return {
            "id": self.id,
            "steps": self.steps,
            "condition": self.condition,
        }


@dataclass
class ForkJoinConfig:
    """Configuration for Fork/Join parallel execution."""

    branches: List[Branch] = field(default_factory=list)
    join_strategy: JoinStrategy = JoinStrategy.ALL
    timeout_ms: int = 60000  # 1 minute
    continue_on_error: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the fork/join configuration to a dictionary."""
        return {
            "branches": [b.to_dict() for b in self.branches],
            "join_strategy": self.join_strategy.value,
            "timeout_ms": self.timeout_ms,
            "continue_on_error": self.continue_on_error,
        }


@dataclass
class BranchResult:
    """Result of a single branch execution."""

    branch_id: str
    success: bool
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int = 0
    skipped: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the branch result to a dictionary."""
        return {
            "branch_id": self.branch_id,
            "success": self.success,
            "outputs": self.outputs,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "skipped": self.skipped,
        }


@dataclass
class ForkJoinResult:
    """Result of Fork/Join execution."""

    success: bool
    branch_results: List[BranchResult] = field(default_factory=list)
    merged_outputs: Dict[str, Any] = field(default_factory=dict)
    total_duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the fork/join result to a dictionary."""
        return {
            "success": self.success,
            "branch_results": [b.to_dict() for b in self.branch_results],
            "merged_outputs": self.merged_outputs,
            "total_duration_ms": self.total_duration_ms,
        }


class ForkJoinExecutor:
    """
    Execute parallel branches with configurable join strategy.

    Supports:
    - ALL: Wait for all branches (default)
    - ANY: Complete when any branch finishes
    - FIRST_SUCCESS: Complete when first branch succeeds
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

    async def execute(
        self,
        config: ForkJoinConfig,
        context: Dict[str, Any],
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> ForkJoinResult:
        """
        Execute Fork/Join.

        Args:
            config: Fork/Join configuration
            context: Execution context
            cancel_check: Optional cancellation check

        Returns:
            ForkJoinResult with all branch results
        """
        start_time = datetime.now(timezone.utc)

        # Filter branches by condition
        active_branches = []
        skipped_results = []

        for branch in config.branches:
            if branch.condition:
                try:
                    should_run = self.evaluate_condition(branch.condition, context)
                    if not should_run:
                        skipped_results.append(BranchResult(
                            branch_id=branch.id,
                            success=True,
                            skipped=True,
                        ))
                        continue
                except Exception as e:
                    logger.warning(f"Branch condition failed: {e}")

            active_branches.append(branch)

        if not active_branches:
            return ForkJoinResult(
                success=True,
                branch_results=skipped_results,
            )

        # Execute based on strategy
        if config.join_strategy == JoinStrategy.ALL:
            branch_results = await self._execute_all(
                active_branches, config, context, cancel_check
            )
        elif config.join_strategy == JoinStrategy.ANY:
            branch_results = await self._execute_any(
                active_branches, config, context, cancel_check
            )
        else:  # FIRST_SUCCESS
            branch_results = await self._execute_first_success(
                active_branches, config, context, cancel_check
            )

        # Combine with skipped
        all_results = skipped_results + branch_results

        # Calculate success
        if config.continue_on_error:
            success = True
        else:
            success = all(
                r.success or r.skipped for r in all_results
            )

        # Merge outputs
        merged = {}
        for result in all_results:
            if result.outputs:
                merged[result.branch_id] = result.outputs

        total_duration = int(
            (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        )

        return ForkJoinResult(
            success=success,
            branch_results=all_results,
            merged_outputs=merged,
            total_duration_ms=total_duration,
        )

    async def _execute_all(
        self,
        branches: List[Branch],
        config: ForkJoinConfig,
        context: Dict[str, Any],
        cancel_check: Optional[Callable[[], bool]],
    ) -> List[BranchResult]:
        """Execute all branches and wait for all to complete."""
        tasks = [
            self._execute_branch(branch, context, cancel_check)
            for branch in branches
        ]

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=config.timeout_ms / 1000,
            )
        except asyncio.TimeoutError:
            # Return timeout for all incomplete
            return [
                BranchResult(
                    branch_id=b.id,
                    success=False,
                    error=f"Timeout after {config.timeout_ms}ms",
                )
                for b in branches
            ]

        # Convert exceptions to results
        branch_results = []
        for i, result in enumerate(results):
            if isinstance(result, BranchResult):
                branch_results.append(result)
            elif isinstance(result, Exception):
                branch_results.append(BranchResult(
                    branch_id=branches[i].id,
                    success=False,
                    error=str(result),
                ))
            else:
                branch_results.append(BranchResult(
                    branch_id=branches[i].id,
                    success=True,
                    outputs=result if isinstance(result, dict) else {"result": result},
                ))

        return branch_results

    async def _execute_any(
        self,
        branches: List[Branch],
        config: ForkJoinConfig,
        context: Dict[str, Any],
        cancel_check: Optional[Callable[[], bool]],
    ) -> List[BranchResult]:
        """Execute all branches, return when any completes."""
        tasks = {
            asyncio.create_task(
                self._execute_branch(branch, context, cancel_check)
            ): branch
            for branch in branches
        }

        results = []
        pending = set(tasks.keys())

        try:
            done, pending = await asyncio.wait(
                pending,
                timeout=config.timeout_ms / 1000,
                return_when=asyncio.FIRST_COMPLETED,
            )
        except asyncio.TimeoutError:
            done = set()

        # Process completed
        for task in done:
            branch = tasks[task]
            try:
                result = task.result()
                if isinstance(result, BranchResult):
                    results.append(result)
                else:
                    results.append(BranchResult(
                        branch_id=branch.id,
                        success=True,
                        outputs=result if isinstance(result, dict) else {"result": result},
                    ))
            except Exception as e:
                results.append(BranchResult(
                    branch_id=branch.id,
                    success=False,
                    error=str(e),
                ))

        # Cancel pending
        for task in pending:
            task.cancel()

        return results

    async def _execute_first_success(
        self,
        branches: List[Branch],
        config: ForkJoinConfig,
        context: Dict[str, Any],
        cancel_check: Optional[Callable[[], bool]],
    ) -> List[BranchResult]:
        """Execute branches until first success."""
        tasks = {
            asyncio.create_task(
                self._execute_branch(branch, context, cancel_check)
            ): branch
            for branch in branches
        }

        results = []
        pending = set(tasks.keys())
        found_success = False

        deadline = asyncio.get_event_loop().time() + (config.timeout_ms / 1000)

        while pending and not found_success:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break

            done, pending = await asyncio.wait(
                pending,
                timeout=remaining,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                branch = tasks[task]
                try:
                    result = task.result()
                    if isinstance(result, BranchResult):
                        results.append(result)
                        if result.success:
                            found_success = True
                    else:
                        results.append(BranchResult(
                            branch_id=branch.id,
                            success=True,
                            outputs=result if isinstance(result, dict) else {"result": result},
                        ))
                        found_success = True
                except Exception as e:
                    results.append(BranchResult(
                        branch_id=branch.id,
                        success=False,
                        error=str(e),
                    ))

        # Cancel pending
        for task in pending:
            task.cancel()

        return results

    async def _execute_branch(
        self,
        branch: Branch,
        context: Dict[str, Any],
        cancel_check: Optional[Callable[[], bool]],
    ) -> BranchResult:
        """Execute a single branch."""
        start_time = datetime.now(timezone.utc)

        try:
            # Create isolated context for branch
            branch_context = context.copy()
            branch_context["_branch_id"] = branch.id

            result = await self.execute_steps(branch.steps, branch_context)

            duration_ms = int(
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            )

            return BranchResult(
                branch_id=branch.id,
                success=True,
                outputs=result if isinstance(result, dict) else {"result": result},
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int(
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            )

            return BranchResult(
                branch_id=branch.id,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )
