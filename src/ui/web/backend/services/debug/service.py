"""
Debug Service

Main service class that provides a unified interface
for all debugging capabilities.
"""

from typing import Any, Dict, Optional

from services.debug.models import ExecutionTimeline, RerunMode, RerunResult
from services.debug.timeline import get_timeline, get_node_detail, get_variables_at_step
from services.debug.rerun import replay_execution, rerun_from_node
from services.debug.comparison import compare_executions
from services.debug.error_analysis import get_error_analysis, get_fix_suggestions


class DebugService:
    """
    Service for debugging workflow executions.

    Provides:
    - Execution timeline visualization
    - Variable inspection at any point
    - Replay/Rerun capabilities
    - Step-by-step analysis

    Usage:
        service = DebugService()

        # Get execution timeline
        timeline = await service.get_timeline(execution_id)

        # View context at specific step
        context = timeline.get_context_at_step(3)

        # Replay entire execution
        result = await service.replay_execution(execution_id)

        # Rerun from specific node
        result = await service.rerun_from_node(
            execution_id,
            node_id="step_3",
            mode=RerunMode.REHYDRATE,
        )
    """

    @staticmethod
    async def get_timeline(execution_id: str) -> Optional[ExecutionTimeline]:
        """Get execution timeline for visualization."""
        return await get_timeline(execution_id)

    @staticmethod
    async def get_node_detail(
        execution_id: str,
        node_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific node execution."""
        return await get_node_detail(execution_id, node_id)

    @staticmethod
    async def replay_execution(
        execution_id: str,
        override_inputs: Optional[Dict[str, Any]] = None,
    ) -> RerunResult:
        """Replay an entire execution with same (or overridden) inputs."""
        return await replay_execution(execution_id, override_inputs)

    @staticmethod
    async def rerun_from_node(
        execution_id: str,
        node_id: str,
        mode: RerunMode = RerunMode.REHYDRATE,
        override_inputs: Optional[Dict[str, Any]] = None,
    ) -> RerunResult:
        """Rerun execution starting from a specific node."""
        return await rerun_from_node(execution_id, node_id, mode, override_inputs)

    @staticmethod
    async def get_variables_at_step(
        execution_id: str,
        step_index: int,
    ) -> Dict[str, Any]:
        """Get all variables/context at a specific step."""
        return await get_variables_at_step(execution_id, step_index)

    @staticmethod
    async def compare_executions(
        exec_id_1: str,
        exec_id_2: str,
    ) -> Dict[str, Any]:
        """Compare two executions."""
        return await compare_executions(exec_id_1, exec_id_2)

    @staticmethod
    async def get_error_analysis(execution_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed error analysis for a failed execution."""
        return await get_error_analysis(execution_id)

    @staticmethod
    def _get_fix_suggestions(error_category: str):
        """Get fix suggestions based on error category."""
        return get_fix_suggestions(error_category)
