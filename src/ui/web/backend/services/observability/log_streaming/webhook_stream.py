"""
Webhook Log Stream

HTTP webhook implementation for log streaming.
Supports generic webhooks, Slack, Discord, and custom endpoints.
"""

import asyncio
import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp

from services.observability.log_streaming.interface import LogEvent, LogStreamInterface, StreamConfig

logger = logging.getLogger(__name__)


@dataclass
class WebhookConfig(StreamConfig):
    """Webhook-specific configuration."""
    url: str = ""
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    auth_token: Optional[str] = None
    auth_type: str = "Bearer"  # Bearer, Basic, Custom
    timeout_seconds: float = 10.0
    verify_ssl: bool = True
    format: str = "default"  # default, splunk, datadog, slack


class WebhookStream(LogStreamInterface):
    """
    HTTP webhook log stream.

    Supports:
    - Generic POST webhooks
    - Splunk HEC format
    - Datadog logs API format
    - Slack incoming webhooks
    - Custom authentication
    """

    def __init__(
        self,
        url: str,
        config: Optional[WebhookConfig] = None,
        **kwargs,
    ):
        """
        Initialize webhook stream.

        Args:
            url: Webhook endpoint URL
            config: Stream configuration
            **kwargs: Additional config options
        """
        if config is None:
            config = WebhookConfig(url=url, **kwargs)
        else:
            config.url = url

        super().__init__(config)
        self.webhook_config = config
        self._buffer: deque = deque(maxlen=config.batch_size * 2)
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            headers = dict(self.webhook_config.headers)
            headers["Content-Type"] = "application/json"

            if self.webhook_config.auth_token:
                if self.webhook_config.auth_type == "Bearer":
                    headers["Authorization"] = f"Bearer {self.webhook_config.auth_token}"
                elif self.webhook_config.auth_type == "Basic":
                    headers["Authorization"] = f"Basic {self.webhook_config.auth_token}"
                else:
                    headers["Authorization"] = self.webhook_config.auth_token

            connector = aiohttp.TCPConnector(
                ssl=self.webhook_config.verify_ssl,
            )
            timeout = aiohttp.ClientTimeout(
                total=self.webhook_config.timeout_seconds,
            )
            self._session = aiohttp.ClientSession(
                headers=headers,
                connector=connector,
                timeout=timeout,
            )

        return self._session

    def _format_event(self, event: LogEvent) -> Dict[str, Any]:
        """
        Format event based on configured format.

        Args:
            event: Log event

        Returns:
            Formatted dict
        """
        fmt = self.webhook_config.format

        if fmt == "splunk":
            return self._format_splunk(event)
        elif fmt == "datadog":
            return self._format_datadog(event)
        elif fmt == "slack":
            return self._format_slack(event)
        else:
            return event.to_dict()

    def _format_splunk(self, event: LogEvent) -> Dict[str, Any]:
        """Format for Splunk HEC."""
        return {
            "time": event.timestamp,
            "source": event.source_system,
            "sourcetype": f"flyto:{event.category.value}",
            "event": event.to_dict(),
        }

    def _format_datadog(self, event: LogEvent) -> Dict[str, Any]:
        """Format for Datadog logs API."""
        return {
            "ddsource": "flyto",
            "ddtags": ",".join(event.tags) if event.tags else "",
            "hostname": event.source_system,
            "message": event.message,
            "service": event.source_component or "flyto",
            "status": event.level.name.lower(),
            **event.metadata,
        }

    def _format_slack(self, event: LogEvent) -> Dict[str, Any]:
        """Format for Slack incoming webhook."""
        color = {
            "emergency": "#ff0000",
            "alert": "#ff0000",
            "critical": "#ff0000",
            "error": "#ff4444",
            "warning": "#ffaa00",
            "notice": "#00aaff",
            "info": "#00aa00",
            "debug": "#888888",
        }.get(event.level.name.lower(), "#888888")

        return {
            "attachments": [
                {
                    "color": color,
                    "title": f"[{event.level.name}] {event.category.value}",
                    "text": event.message,
                    "fields": [
                        {
                            "title": "Event ID",
                            "value": event.event_id,
                            "short": True,
                        },
                        {
                            "title": "Timestamp",
                            "value": event.timestamp,
                            "short": True,
                        },
                    ],
                    "footer": "Flyto2 Log Stream",
                    "ts": int(datetime.now(timezone.utc).timestamp()),
                }
            ]
        }

    async def push(self, event: LogEvent) -> bool:
        """
        Push a single log event.

        Args:
            event: Log event to push

        Returns:
            True if successfully pushed
        """
        try:
            session = await self._get_session()
            payload = self._format_event(event)

            async with session.request(
                self.webhook_config.method,
                self.webhook_config.url,
                json=payload,
            ) as response:
                if response.status >= 200 and response.status < 300:
                    return True
                else:
                    body = await response.text()
                    logger.warning(
                        f"Webhook returned {response.status}: {body[:200]}"
                    )
                    return False

        except asyncio.TimeoutError:
            logger.warning(f"Webhook timeout: {self.webhook_config.url}")
            return False

        except aiohttp.ClientError as e:
            logger.error(f"Webhook error: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected webhook error: {e}")
            return False

    async def push_batch(self, events: List[LogEvent]) -> int:
        """
        Push a batch of log events.

        Args:
            events: List of log events

        Returns:
            Number of successfully pushed events
        """
        if not events:
            return 0

        try:
            session = await self._get_session()

            # Format based on endpoint type
            if self.webhook_config.format == "splunk":
                # Splunk HEC supports NDJSON
                payload = "\n".join(
                    json.dumps(self._format_splunk(e)) for e in events
                )
                headers = {"Content-Type": "application/x-ndjson"}
            elif self.webhook_config.format == "datadog":
                # Datadog expects array
                payload = json.dumps([self._format_datadog(e) for e in events])
                headers = {"Content-Type": "application/json"}
            else:
                # Generic: send as array
                payload = json.dumps([self._format_event(e) for e in events])
                headers = {"Content-Type": "application/json"}

            async with session.request(
                self.webhook_config.method,
                self.webhook_config.url,
                data=payload,
                headers=headers,
            ) as response:
                if response.status >= 200 and response.status < 300:
                    return len(events)
                else:
                    logger.warning(f"Webhook batch returned {response.status}")
                    # Fall back to individual pushes
                    return await self._push_individually(events)

        except Exception as e:
            logger.error(f"Webhook batch error: {e}")
            return await self._push_individually(events)

    async def _push_individually(self, events: List[LogEvent]) -> int:
        """Push events one by one as fallback."""
        success_count = 0
        for event in events:
            if await self.push(event):
                success_count += 1
        return success_count

    async def flush(self) -> int:
        """
        Flush any buffered events.

        Returns:
            Number of flushed events
        """
        async with self._lock:
            if not self._buffer:
                return 0

            events = list(self._buffer)
            self._buffer.clear()

        return await self.push_batch(events)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check stream health.

        Returns:
            Health status dict
        """
        try:
            session = await self._get_session()

            # Try a lightweight request
            async with session.head(
                self.webhook_config.url,
                allow_redirects=True,
            ) as response:
                return {
                    "healthy": response.status < 500,
                    "status_code": response.status,
                    "url": self.webhook_config.url,
                }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "url": self.webhook_config.url,
            }

    async def close(self) -> None:
        """Close the stream and cleanup resources."""
        await self.flush()

        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        logger.info(f"Webhook stream closed: {self.webhook_config.url}")
