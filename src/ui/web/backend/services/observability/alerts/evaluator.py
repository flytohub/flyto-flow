"""
Alert Evaluator

Single responsibility: Evaluate alert conditions against metrics.
"""

import logging
import operator
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from services.observability.alerts.rule import AlertRule, AlertState, RuleEvaluationState

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of evaluating an alert rule."""

    rule_id: str
    condition_met: bool
    previous_state: AlertState
    new_state: AlertState
    evaluated_value: Optional[float] = None
    threshold_value: Optional[float] = None
    error: Optional[str] = None

    def state_changed(self) -> bool:
        """Check if state changed."""
        return self.previous_state != self.new_state


class ConditionParser:
    """
    Parse and evaluate alert conditions.

    Supported operators: >, <, >=, <=, ==, !=
    Supported format: "metric_name operator value"

    Examples:
        "queue_depth > 100"
        "error_rate >= 0.05"
        "active_workers == 0"
    """

    OPERATORS: Dict[str, Callable[[float, float], bool]] = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }

    PATTERN = re.compile(r"^(\w+)\s*(>=|<=|==|!=|>|<)\s*([\d.]+)$")

    @classmethod
    def parse(cls, condition: str) -> Optional[tuple]:
        """
        Parse a condition string.

        Args:
            condition: Condition string

        Returns:
            Tuple of (metric_name, operator_func, threshold) or None
        """
        match = cls.PATTERN.match(condition.strip())
        if not match:
            return None

        metric_name = match.group(1)
        op_str = match.group(2)
        threshold = float(match.group(3))

        op_func = cls.OPERATORS.get(op_str)
        if op_func is None:
            return None

        return metric_name, op_func, threshold

    @classmethod
    def evaluate(
        cls,
        condition: str,
        metrics: Dict[str, float],
    ) -> tuple[bool, Optional[float], Optional[float]]:
        """
        Evaluate a condition against metrics.

        Args:
            condition: Condition string
            metrics: Dictionary of metric name to value

        Returns:
            Tuple of (result, actual_value, threshold_value)
        """
        parsed = cls.parse(condition)
        if parsed is None:
            logger.warning(f"Invalid condition format: {condition}")
            return False, None, None

        metric_name, op_func, threshold = parsed
        actual_value = metrics.get(metric_name)

        if actual_value is None:
            logger.debug(f"Metric not found: {metric_name}")
            return False, None, threshold

        result = op_func(actual_value, threshold)
        return result, actual_value, threshold


class AlertEvaluator:
    """
    Evaluate alert rules against metrics.

    Manages rule evaluation state and determines when alerts
    should fire or resolve.
    """

    def __init__(self):
        """Initialize evaluator."""
        self._states: Dict[str, RuleEvaluationState] = {}

    def evaluate(
        self,
        rule: AlertRule,
        metrics: Dict[str, float],
    ) -> EvaluationResult:
        """
        Evaluate a rule against current metrics.

        Args:
            rule: Alert rule to evaluate
            metrics: Current metric values

        Returns:
            Evaluation result
        """
        # Get or create state
        state = self._states.get(rule.id)
        if state is None:
            state = RuleEvaluationState(rule_id=rule.id)
            self._states[rule.id] = state

        previous_state = state.current_state

        # Check if rule is enabled
        if not rule.enabled:
            state.current_state = AlertState.INACTIVE
            state.condition_cleared()
            return EvaluationResult(
                rule_id=rule.id,
                condition_met=False,
                previous_state=previous_state,
                new_state=AlertState.INACTIVE,
            )

        # Evaluate condition
        condition_met, actual_value, threshold = ConditionParser.evaluate(
            rule.condition, metrics
        )

        if condition_met:
            state.condition_met()

            # Check duration requirement
            if state.duration_elapsed(rule.duration_seconds):
                state.current_state = AlertState.FIRING
            else:
                state.current_state = AlertState.PENDING
        else:
            # Condition not met
            if state.current_state == AlertState.FIRING:
                state.current_state = AlertState.RESOLVED
            else:
                state.current_state = AlertState.INACTIVE

            state.condition_cleared()

        return EvaluationResult(
            rule_id=rule.id,
            condition_met=condition_met,
            previous_state=previous_state,
            new_state=state.current_state,
            evaluated_value=actual_value,
            threshold_value=threshold,
        )

    def get_state(self, rule_id: str) -> Optional[RuleEvaluationState]:
        """Get evaluation state for a rule."""
        return self._states.get(rule_id)

    def reset_state(self, rule_id: str) -> None:
        """Reset evaluation state for a rule."""
        self._states.pop(rule_id, None)

    def clear_all_states(self) -> None:
        """Clear all evaluation states."""
        self._states.clear()
