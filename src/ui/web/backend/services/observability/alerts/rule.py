"""
Alert Rule

Single responsibility: Alert rule definition and state.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertState(str, Enum):
    """Alert evaluation state."""

    INACTIVE = "inactive"  # Rule disabled
    PENDING = "pending"  # Condition true, waiting for duration
    FIRING = "firing"  # Condition true for duration
    RESOLVED = "resolved"  # Was firing, now condition false


@dataclass
class AlertRule:
    """
    Alert rule definition.

    Defines conditions under which an alert should fire.
    """

    id: str
    name: str
    condition: str  # e.g., "queue_depth > 100"
    severity: AlertSeverity
    duration_seconds: int = 0  # Must be true for N seconds
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        """Set created_at to current UTC time if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "condition": self.condition,
            "severity": self.severity.value,
            "duration_seconds": self.duration_seconds,
            "labels": self.labels,
            "annotations": self.annotations,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertRule":
        """Create from dictionary."""
        severity = data.get("severity", "info")
        if isinstance(severity, str):
            severity = AlertSeverity(severity)

        return cls(
            id=data["id"],
            name=data["name"],
            condition=data["condition"],
            severity=severity,
            duration_seconds=data.get("duration_seconds", 0),
            labels=data.get("labels", {}),
            annotations=data.get("annotations", {}),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


@dataclass
class RuleEvaluationState:
    """
    Tracks the evaluation state of a rule.

    Used to implement duration-based alerting.
    """

    rule_id: str
    condition_met_at: Optional[str] = None  # When condition first became true
    last_evaluation: Optional[str] = None
    current_state: AlertState = AlertState.INACTIVE

    def condition_met(self) -> None:
        """Record that condition is now met."""
        now = datetime.now(timezone.utc).isoformat()
        if self.condition_met_at is None:
            self.condition_met_at = now
        self.last_evaluation = now

    def condition_cleared(self) -> None:
        """Record that condition is no longer met."""
        self.condition_met_at = None
        self.last_evaluation = datetime.now(timezone.utc).isoformat()

    def duration_elapsed(self, required_seconds: int) -> bool:
        """Check if condition has been true for required duration."""
        if self.condition_met_at is None:
            return False

        met_time = datetime.fromisoformat(self.condition_met_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        elapsed = (now - met_time).total_seconds()

        return elapsed >= required_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "condition_met_at": self.condition_met_at,
            "last_evaluation": self.last_evaluation,
            "current_state": self.current_state.value,
        }
