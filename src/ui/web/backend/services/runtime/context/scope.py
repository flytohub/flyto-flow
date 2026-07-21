"""
Variable Scope Management

Hierarchical variable scope management for workflow execution.
"""

import logging
from typing import Any, Dict, Optional

from services.runtime.context.models import ScopeType, VariableScope

logger = logging.getLogger(__name__)


class ScopeManager:
    """Manages hierarchical variable scopes."""

    def __init__(
        self,
        workflow_id: str,
        initial_variables: Optional[Dict[str, Any]] = None,
    ):
        """Initialize with a root workflow scope and optional variables."""
        self._root_scope = VariableScope(
            scope_type=ScopeType.WORKFLOW,
            scope_id=workflow_id,
            variables=initial_variables or {},
        )
        self._current_scope = self._root_scope

    @property
    def current_scope(self) -> VariableScope:
        """Get current scope."""
        return self._current_scope

    @property
    def root_scope(self) -> VariableScope:
        """Get root scope."""
        return self._root_scope

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get variable from current scope chain."""
        return self._current_scope.get(key, default)

    def set_variable(self, key: str, value: Any) -> None:
        """Set variable in current scope."""
        self._current_scope.set(key, value)

    def has_variable(self, key: str) -> bool:
        """Check if variable exists in scope chain."""
        return self._current_scope.has(key)

    def get_all_variables(self) -> Dict[str, Any]:
        """Get all variables flattened (for backward compatibility)."""
        return self._current_scope.to_dict()

    def push_scope(
        self,
        scope_type: ScopeType,
        scope_id: str,
        initial_vars: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Push a new scope level."""
        new_scope = VariableScope(
            scope_type=scope_type,
            scope_id=scope_id,
            variables=initial_vars or {},
            parent=self._current_scope,
        )
        self._current_scope = new_scope
        logger.debug(f"Pushed scope: {scope_type.value}/{scope_id}")

    def pop_scope(self) -> Optional[VariableScope]:
        """Pop current scope, return to parent."""
        if self._current_scope.parent is None:
            logger.warning("Cannot pop root scope")
            return None

        popped = self._current_scope
        self._current_scope = self._current_scope.parent
        logger.debug(f"Popped scope: {popped.scope_type.value}/{popped.scope_id}")
        return popped

    def enter_node_scope(self, node_id: str) -> None:
        """Enter node execution scope."""
        self.push_scope(ScopeType.NODE, node_id)

    def exit_node_scope(self) -> None:
        """Exit node execution scope."""
        if self._current_scope.scope_type == ScopeType.NODE:
            self.pop_scope()

    def enter_foreach_scope(
        self,
        item: Any,
        index: int,
        item_var: str = "item",
        index_var: str = "index",
    ) -> None:
        """Enter foreach iteration scope."""
        self.push_scope(
            ScopeType.FOREACH,
            f"foreach_{index}",
            {item_var: item, index_var: index},
        )

    def exit_foreach_scope(self) -> None:
        """Exit foreach iteration scope."""
        if self._current_scope.scope_type == ScopeType.FOREACH:
            self.pop_scope()
