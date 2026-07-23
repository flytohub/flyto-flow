"""Local console and operator-configured webhook alert outputs."""

from abc import ABC, abstractmethod
import hashlib
import hmac
import json
import logging
import os
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from services.observability.alerts.repository import Alert
from services.observability.structured_logging import redact_sensitive_data


logger = logging.getLogger(__name__)


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        del req, fp, code, msg, headers, newurl
        return None


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


class WebhookNotifier(AlertNotifier):
    """Send bounded JSON notifications to an explicitly configured HTTPS URL."""

    def __init__(
        self,
        url: str,
        *,
        signing_secret: str | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        parsed = urlparse(url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "Alert webhook must be an HTTPS URL without credentials, "
                "query parameters, or fragments"
            )
        allowed_hosts = {
            host.strip().lower()
            for host in os.environ.get("FLYTO_ALERT_WEBHOOK_ALLOWED_HOSTS", "").split(",")
            if host.strip()
        }
        if not allowed_hosts:
            raise ValueError("Alert webhook requires FLYTO_ALERT_WEBHOOK_ALLOWED_HOSTS")
        if allowed_hosts and parsed.hostname.lower() not in allowed_hosts:
            raise ValueError("Alert webhook host is not allowlisted")
        self._url = url
        self._signing_secret = signing_secret
        self._timeout_seconds = max(0.1, min(timeout_seconds, 30.0))

    def notify(self, alert: Alert, state: str) -> bool:
        payload = json.dumps(
            {
                "schema": "flyto.alert.v1",
                "state": state,
                "alert": {
                    "id": alert.id,
                    "rule_id": alert.rule_id,
                    "status": alert.status,
                    "severity": (
                        alert.severity.value
                        if hasattr(alert.severity, "value")
                        else str(alert.severity)
                    ),
                    "started_at": alert.started_at,
                    "ended_at": alert.ended_at,
                    "labels": redact_sensitive_data(alert.labels),
                    "annotations": redact_sensitive_data(alert.annotations),
                    "evaluated_value": alert.evaluated_value,
                    "threshold_value": alert.threshold_value,
                },
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Flyto2-Flow-Alert/1",
        }
        if self._signing_secret:
            headers["X-Flyto2-Signature"] = (
                "sha256="
                + hmac.new(
                    self._signing_secret.encode(),
                    payload,
                    hashlib.sha256,
                ).hexdigest()
            )
        request = Request(self._url, data=payload, headers=headers, method="POST")
        opener = build_opener(_NoRedirectHandler())
        with opener.open(request, timeout=self._timeout_seconds) as response:
            return 200 <= response.status < 300


class CompositeNotifier(AlertNotifier):
    def __init__(self, notifiers: list[AlertNotifier]) -> None:
        self._notifiers = tuple(notifiers)

    def notify(self, alert: Alert, state: str) -> bool:
        results: list[bool] = []
        for notifier in self._notifiers:
            try:
                results.append(notifier.notify(alert, state))
            except Exception:
                logger.exception("Alert notifier failed: %s", notifier.__class__.__name__)
                results.append(False)
        return all(results)

    def shutdown(self) -> None:
        for notifier in self._notifiers:
            notifier.shutdown()


def notifier_from_environment() -> AlertNotifier:
    notifiers: list[AlertNotifier] = [ConsoleNotifier()]
    url = os.environ.get("FLYTO_ALERT_WEBHOOK_URL", "").strip()
    if url:
        notifiers.append(
            WebhookNotifier(
                url,
                signing_secret=os.environ.get("FLYTO_ALERT_WEBHOOK_SECRET") or None,
            )
        )
    return CompositeNotifier(notifiers)
