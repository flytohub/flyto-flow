"""
Alert Manager

Single responsibility: Manage alert lifecycle and state transitions.
"""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, Dict, List, Optional
from uuid import uuid4

from services.observability.alerts.evaluator import AlertEvaluator, EvaluationResult
from services.observability.alerts.repository import Alert, AlertRepository, AlertRuleRepository
from services.observability.alerts.rule import AlertRule, AlertSeverity, AlertState

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from services.observability.alerts.notifier import AlertNotifier


class AlertManager:
    """
    Manage alert lifecycle.

    Coordinates evaluation, state transitions, and notifications.
    """

    def __init__(
        self,
        notifier: Optional["AlertNotifier"] = None,
    ):
        """
        Initialize alert manager.

        Args:
            notifier: Optional notifier for sending alerts
        """
        self._evaluator = AlertEvaluator()
        self._notifier = notifier
        self._active_alerts: Dict[str, Alert] = {}  # rule_id -> Alert

    def evaluate_all(self, metrics: Dict[str, float]) -> List[EvaluationResult]:
        """
        Evaluate all enabled rules against metrics.

        Args:
            metrics: Current metric values

        Returns:
            List of evaluation results
        """
        rules = AlertRuleRepository.list_all(enabled_only=True)
        results = []

        for rule in rules:
            result = self.evaluate_rule(rule, metrics)
            results.append(result)

        return results

    def evaluate_rule(
        self,
        rule: AlertRule,
        metrics: Dict[str, float],
    ) -> EvaluationResult:
        """
        Evaluate a single rule.

        Args:
            rule: Alert rule
            metrics: Current metric values

        Returns:
            Evaluation result
        """
        result = self._evaluator.evaluate(rule, metrics)

        # Handle state transitions
        if result.state_changed():
            self._handle_state_change(rule, result)

        return result

    def _handle_state_change(
        self,
        rule: AlertRule,
        result: EvaluationResult,
    ) -> None:
        """Handle alert state change."""
        if result.new_state == AlertState.FIRING:
            self._fire_alert(rule, result)
        elif result.new_state == AlertState.RESOLVED:
            self._resolve_alert(rule, result)

    def _fire_alert(
        self,
        rule: AlertRule,
        result: EvaluationResult,
    ) -> None:
        """Create and fire an alert."""
        now = datetime.now(timezone.utc).isoformat()

        alert = Alert(
            id=str(uuid4()),
            rule_id=rule.id,
            status="firing",
            severity=rule.severity,
            started_at=now,
            labels=rule.labels.copy(),
            annotations=rule.annotations.copy(),
            evaluated_value=result.evaluated_value,
            threshold_value=result.threshold_value,
        )

        # Add rule info to labels
        alert.labels["alertname"] = rule.name
        alert.labels["severity"] = rule.severity.value

        # Store in database
        AlertRepository.create(alert)

        # Track active alert
        self._active_alerts[rule.id] = alert

        logger.info(f"Alert fired: {rule.name} ({alert.id})")

        # Send notification
        if self._notifier:
            try:
                self._notifier.notify(alert, "firing")
            except Exception as e:
                logger.error(f"Failed to send alert notification: {e}")

    def _resolve_alert(
        self,
        rule: AlertRule,
        result: EvaluationResult,
    ) -> None:
        """Resolve an active alert."""
        alert = self._active_alerts.get(rule.id)
        if not alert:
            return

        # Update in database
        AlertRepository.resolve(alert.id)

        # Remove from active
        del self._active_alerts[rule.id]

        logger.info(f"Alert resolved: {rule.name} ({alert.id})")

        # Send notification
        if self._notifier:
            try:
                alert.status = "resolved"
                alert.ended_at = datetime.now(timezone.utc).isoformat()
                self._notifier.notify(alert, "resolved")
            except Exception as e:
                logger.error(f"Failed to send resolution notification: {e}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self._active_alerts.values())

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        return AlertRepository.get(alert_id)

    def silence_alert(self, alert_id: str, until: str) -> bool:
        """
        Silence an alert until specified time.

        Args:
            alert_id: Alert ID
            until: ISO timestamp to silence until

        Returns:
            True if silenced
        """
        result = AlertRepository.silence(alert_id, until)
        if result:
            logger.info(f"Alert silenced: {alert_id} until {until}")
        return result

    def get_alert_history(
        self,
        rule_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """
        Get alert history.

        Args:
            rule_id: Optional rule ID to filter by
            limit: Maximum alerts to return

        Returns:
            List of alerts
        """
        if rule_id:
            return AlertRepository.get_by_rule(rule_id, limit)

        return AlertRepository.get_active()

    def set_notifier(self, notifier: "AlertNotifier") -> None:
        """Set the notifier."""
        self._notifier = notifier


# Re-export Alert for convenience
__all__ = ["AlertManager", "Alert"]
