"""
Alert Notifier

Single responsibility: Send alert notifications to various channels.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

from services.observability.alerts.repository import Alert

logger = logging.getLogger(__name__)


class AlertNotifier(ABC):
    """
    Abstract base class for alert notifiers.

    Notifiers are responsible for sending alerts to external systems.
    """

    @abstractmethod
    def notify(self, alert: Alert, state: str) -> bool:
        """
        Send notification for an alert.

        Args:
            alert: Alert to notify about
            state: Alert state (firing, resolved)

        Returns:
            True if notification sent successfully
        """
        pass

    def shutdown(self) -> None:
        """Shutdown the notifier (cleanup resources)."""
        pass


class WebhookNotifier(AlertNotifier):
    """
    Send alert notifications via webhook.

    Posts JSON payload to configured URL.
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 30,
    ):
        """
        Initialize webhook notifier.

        Args:
            url: Webhook URL
            headers: Optional headers to include
            timeout_seconds: Request timeout
        """
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout_seconds

    def notify(self, alert: Alert, state: str) -> bool:
        """Send webhook notification."""
        payload = self._build_payload(alert, state)

        try:
            data = json.dumps(payload).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                **self.headers,
            }

            request = Request(
                self.url,
                data=data,
                headers=headers,
                method="POST",
            )

            with urlopen(request, timeout=self.timeout) as response:
                success = 200 <= response.status < 300

            if success:
                logger.info(f"Webhook notification sent for alert {alert.id}")
            else:
                logger.warning(f"Webhook returned non-success status for alert {alert.id}")

            return success

        except URLError as e:
            logger.error(f"Failed to send webhook: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending webhook: {e}")
            return False

    def _build_payload(self, alert: Alert, state: str) -> Dict[str, Any]:
        """Build webhook payload."""
        return {
            "version": "1",
            "status": state,
            "alert": {
                "id": alert.id,
                "rule_id": alert.rule_id,
                "severity": alert.severity.value if hasattr(alert.severity, "value") else alert.severity,
                "started_at": alert.started_at,
                "ended_at": alert.ended_at,
                "labels": alert.labels,
                "annotations": alert.annotations,
                "evaluated_value": alert.evaluated_value,
                "threshold_value": alert.threshold_value,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class ConsoleNotifier(AlertNotifier):
    """
    Print alert notifications to console.

    Useful for development and debugging.
    """

    def notify(self, alert: Alert, state: str) -> bool:
        """Print notification to console."""
        severity = alert.severity.value if hasattr(alert.severity, "value") else alert.severity
        message = f"[ALERT {state.upper()}] [{severity.upper()}] "
        message += f"{alert.labels.get('alertname', 'unknown')} "
        message += f"(rule: {alert.rule_id})"

        if alert.evaluated_value is not None:
            message += f" value={alert.evaluated_value}"

        print(message)
        return True


class MultiNotifier(AlertNotifier):
    """
    Send notifications to multiple channels.

    Combines multiple notifiers.
    """

    def __init__(self, notifiers: List[AlertNotifier]):
        """
        Initialize multi-notifier.

        Args:
            notifiers: List of notifiers to use
        """
        self.notifiers = notifiers

    def notify(self, alert: Alert, state: str) -> bool:
        """Send to all notifiers."""
        success = True

        for notifier in self.notifiers:
            try:
                if not notifier.notify(alert, state):
                    success = False
            except Exception as e:
                logger.error(f"Notifier {type(notifier).__name__} failed: {e}")
                success = False

        return success

    def shutdown(self) -> None:
        """Shutdown all notifiers."""
        for notifier in self.notifiers:
            try:
                notifier.shutdown()
            except Exception as e:
                logger.error(f"Failed to shutdown {type(notifier).__name__}: {e}")


@dataclass
class EmailConfig:
    """Email configuration."""

    smtp_host: str
    smtp_port: int
    sender: str
    recipients: List[str]
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True


class EmailNotifier(AlertNotifier):
    """
    Send alert notifications via email.

    Note: Requires smtplib to be available.
    """

    def __init__(self, config: EmailConfig):
        """
        Initialize email notifier.

        Args:
            config: Email configuration
        """
        self.config = config

    def notify(self, alert: Alert, state: str) -> bool:
        """Send email notification."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
        except ImportError:
            logger.error("smtplib not available")
            return False

        try:
            subject = self._build_subject(alert, state)
            body = self._build_body(alert, state)

            msg = MIMEMultipart()
            msg["From"] = self.config.sender
            msg["To"] = ", ".join(self.config.recipients)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()
                if self.config.username and self.config.password:
                    server.login(self.config.username, self.config.password)
                server.sendmail(
                    self.config.sender,
                    self.config.recipients,
                    msg.as_string(),
                )

            logger.info(f"Email notification sent for alert {alert.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _build_subject(self, alert: Alert, state: str) -> str:
        """Build email subject."""
        severity = alert.severity.value if hasattr(alert.severity, "value") else alert.severity
        alertname = alert.labels.get("alertname", "Alert")
        return f"[{state.upper()}] [{severity.upper()}] {alertname}"

    def _build_body(self, alert: Alert, state: str) -> str:
        """Build email body."""
        lines = [
            f"Alert Status: {state.upper()}",
            f"Alert ID: {alert.id}",
            f"Rule ID: {alert.rule_id}",
            f"Severity: {alert.severity.value if hasattr(alert.severity, 'value') else alert.severity}",
            f"Started: {alert.started_at}",
        ]

        if alert.ended_at:
            lines.append(f"Ended: {alert.ended_at}")

        if alert.evaluated_value is not None:
            lines.append(f"Value: {alert.evaluated_value}")

        if alert.threshold_value is not None:
            lines.append(f"Threshold: {alert.threshold_value}")

        if alert.labels:
            lines.append("")
            lines.append("Labels:")
            for key, value in alert.labels.items():
                lines.append(f"  {key}: {value}")

        if alert.annotations:
            lines.append("")
            lines.append("Annotations:")
            for key, value in alert.annotations.items():
                lines.append(f"  {key}: {value}")

        return "\n".join(lines)
