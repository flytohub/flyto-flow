"""
Subflow Management

Manages subflow execution stack for nested workflows.
"""

import logging
from typing import Any, Dict, List, Optional

from services.runtime.context.models import ScopeType, SubflowFrame, VariableScope

logger = logging.getLogger(__name__)


class SubflowManager:
    """Manages subflow execution stack."""

    def __init__(self, scope_manager):
        """Initialize with a scope manager and empty subflow stack."""
        self._scope_manager = scope_manager
        self._subflow_stack: List[SubflowFrame] = []

    @property
    def subflow_stack(self) -> List[SubflowFrame]:
        """Get subflow stack."""
        return self._subflow_stack

    def enter_subflow(
        self,
        subflow_id: str,
        parent_node_id: str,
        input_mapping: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Enter a subflow execution.

        Args:
            subflow_id: The subflow workflow ID
            parent_node_id: The container node that invoked subflow
            input_mapping: Map of parent vars to subflow vars
        """
        # Save current scope for return
        frame = SubflowFrame(
            subflow_id=subflow_id,
            parent_node_id=parent_node_id,
            entry_scope=self._scope_manager.current_scope,
        )
        self._subflow_stack.append(frame)

        # Create new scope for subflow
        subflow_vars = {}
        if input_mapping:
            for parent_var, subflow_var in input_mapping.items():
                if self._scope_manager.has_variable(parent_var):
                    subflow_vars[subflow_var] = self._scope_manager.get_variable(parent_var)

        self._scope_manager.push_scope(ScopeType.SUBFLOW, subflow_id, subflow_vars)
        logger.info(f"Entered subflow: {subflow_id} from {parent_node_id}")

    def exit_subflow(
        self,
        output_mapping: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Exit current subflow.

        Args:
            output_mapping: Map of subflow vars to parent vars

        Returns:
            The parent node ID for continuation
        """
        if not self._subflow_stack:
            logger.warning("No subflow to exit")
            return None

        frame = self._subflow_stack.pop()

        # Map outputs back to parent scope
        if output_mapping:
            for subflow_var, parent_var in output_mapping.items():
                if self._scope_manager.has_variable(subflow_var):
                    value = self._scope_manager.get_variable(subflow_var)
                    # Temporarily store for parent scope
                    parent_scope = self._scope_manager.current_scope.parent
                    if parent_scope:
                        parent_scope.set(parent_var, value)

        # Restore to parent scope
        self._scope_manager.pop_scope()
        logger.info(f"Exited subflow: {frame.subflow_id}")
        return frame.parent_node_id

    def get_subflow_depth(self) -> int:
        """Get current subflow nesting depth."""
        return len(self._subflow_stack)

    def is_in_subflow(self) -> bool:
        """Check if currently in a subflow."""
        return len(self._subflow_stack) > 0
