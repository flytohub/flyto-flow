"""Local-only alert output."""

from abc import ABC, abstractmethod

from services.observability.alerts.repository import Alert


class AlertNotifier(ABC):
    @abstractmethod
    def notify(self, alert: Alert, state: str) -> bool:
        raise NotImplementedError

    def shutdown(self) -> None:
        return None


class ConsoleNotifier(AlertNotifier):
    def notify(self, alert: Alert, state: str) -> bool:
        severity = alert.severity.value if hasattr(alert.severity, "value") else alert.severity
        name = alert.labels.get("alertname", "unknown")
        print(f"[ALERT {state.upper()}] [{str(severity).upper()}] {name}")
        return True
