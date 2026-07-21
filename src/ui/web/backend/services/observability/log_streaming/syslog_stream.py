"""
Syslog Log Stream

RFC 5424 compliant syslog implementation for log streaming.
Supports TCP, UDP, and TLS connections.
"""

import asyncio
import logging
import socket
import ssl
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.observability.log_streaming.interface import LogEvent, LogStreamInterface, StreamConfig

logger = logging.getLogger(__name__)


@dataclass
class SyslogConfig(StreamConfig):
    """Syslog-specific configuration."""
    host: str = "localhost"
    port: int = 514
    protocol: str = "udp"  # udp, tcp, tls
    facility: int = 1  # user-level (1)
    app_name: str = "flyto"
    use_rfc5424: bool = True  # False for RFC 3164 (BSD)
    use_framing: bool = True  # Octet counting for TCP
    tls_verify: bool = True
    tls_ca_cert: Optional[str] = None
    timeout_seconds: float = 10.0


class SyslogStream(LogStreamInterface):
    """
    Syslog log stream.

    Features:
    - RFC 5424 (modern) and RFC 3164 (BSD) formats
    - UDP, TCP, and TLS transports
    - Octet counting framing for TCP
    - Connection pooling and reconnection
    - Structured data support
    """

    # Severity mapping (RFC 5424)
    SEVERITY_MAP = {
        0: 0,  # EMERGENCY
        1: 1,  # ALERT
        2: 2,  # CRITICAL
        3: 3,  # ERROR
        4: 4,  # WARNING
        5: 5,  # NOTICE
        6: 6,  # INFO
        7: 7,  # DEBUG
    }

    def __init__(
        self,
        host: str = "localhost",
        port: int = 514,
        config: Optional[SyslogConfig] = None,
        **kwargs,
    ):
        """
        Initialize syslog stream.

        Args:
            host: Syslog server host
            port: Syslog server port
            config: Stream configuration
            **kwargs: Additional config options
        """
        if config is None:
            config = SyslogConfig(host=host, port=port, **kwargs)
        else:
            config.host = host
            config.port = port

        super().__init__(config)
        self.syslog_config = config
        self._buffer: deque = deque(maxlen=config.batch_size * 2)
        self._socket: Optional[socket.socket] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()
        self._connected = False

    async def _connect(self) -> bool:
        """
        Establish connection to syslog server.

        Returns:
            True if connected
        """
        if self._connected:
            return True

        try:
            protocol = self.syslog_config.protocol.lower()

            if protocol == "udp":
                # UDP is connectionless
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._socket.setblocking(False)
                self._connected = True

            elif protocol in ("tcp", "tls"):
                ssl_context = None

                if protocol == "tls":
                    ssl_context = ssl.create_default_context()
                    if not self.syslog_config.tls_verify:
                        ssl_context.check_hostname = False
                        ssl_context.verify_mode = ssl.CERT_NONE
                    elif self.syslog_config.tls_ca_cert:
                        ssl_context.load_verify_locations(
                            self.syslog_config.tls_ca_cert
                        )

                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(
                        self.syslog_config.host,
                        self.syslog_config.port,
                        ssl=ssl_context,
                    ),
                    timeout=self.syslog_config.timeout_seconds,
                )
                self._connected = True

            logger.info(
                f"Connected to syslog server: "
                f"{self.syslog_config.host}:{self.syslog_config.port} ({protocol})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to connect to syslog server: {e}")
            self._connected = False
            return False

    async def _disconnect(self) -> None:
        """Disconnect from syslog server."""
        try:
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()
                self._writer = None
                self._reader = None

            if self._socket:
                self._socket.close()
                self._socket = None

            self._connected = False

        except Exception as e:
            logger.warning(f"Error disconnecting: {e}")

    def _format_rfc5424(self, event: LogEvent) -> str:
        """
        Format event as RFC 5424 syslog message.

        Args:
            event: Log event

        Returns:
            Formatted syslog message
        """
        # Priority = Facility * 8 + Severity
        severity = self.SEVERITY_MAP.get(event.level.value, 6)
        priority = self.syslog_config.facility * 8 + severity

        # Version
        version = 1

        # Timestamp (RFC 3339)
        timestamp = event.timestamp

        # Hostname
        hostname = "-"

        # App name
        app_name = self.syslog_config.app_name

        # Process ID
        procid = event.execution_id or "-"

        # Message ID
        msgid = event.event_type or "-"

        # Structured data
        sd = self._format_structured_data(event)

        # Message
        msg = event.message

        return f"<{priority}>{version} {timestamp} {hostname} {app_name} {procid} {msgid} {sd} {msg}"

    def _format_rfc3164(self, event: LogEvent) -> str:
        """
        Format event as RFC 3164 (BSD) syslog message.

        Args:
            event: Log event

        Returns:
            Formatted syslog message
        """
        severity = self.SEVERITY_MAP.get(event.level.value, 6)
        priority = self.syslog_config.facility * 8 + severity

        # Timestamp (Mmm dd hh:mm:ss)
        now = datetime.now()
        timestamp = now.strftime("%b %d %H:%M:%S")

        # Hostname
        hostname = "flyto"

        # Tag (app[pid])
        tag = self.syslog_config.app_name
        if event.execution_id:
            tag = f"{tag}[{event.execution_id[:8]}]"

        # Message
        msg = event.message

        return f"<{priority}>{timestamp} {hostname} {tag}: {msg}"

    def _format_structured_data(self, event: LogEvent) -> str:
        """
        Format structured data element.

        Args:
            event: Log event

        Returns:
            SD-ELEMENT string
        """
        parts = []

        # flyto@enterprise SD-ID
        sd_params = []

        if event.actor_id:
            sd_params.append(f'actor="{self._escape_sd_value(event.actor_id)}"')
        if event.org_id:
            sd_params.append(f'org="{self._escape_sd_value(event.org_id)}"')
        if event.resource_type:
            sd_params.append(f'resource="{self._escape_sd_value(event.resource_type)}"')
        if event.outcome:
            sd_params.append(f'outcome="{self._escape_sd_value(event.outcome)}"')
        if event.event_action:
            sd_params.append(f'action="{self._escape_sd_value(event.event_action)}"')

        if sd_params:
            parts.append(f'[flyto@0 {" ".join(sd_params)}]')

        # Add metadata as separate SD-ELEMENT
        if event.metadata:
            meta_params = []
            for key, value in event.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    meta_params.append(
                        f'{key}="{self._escape_sd_value(str(value))}"'
                    )
            if meta_params:
                parts.append(f'[meta@0 {" ".join(meta_params)}]')

        return "".join(parts) if parts else "-"

    def _escape_sd_value(self, value: str) -> str:
        """Escape special characters in SD-PARAM value."""
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("]", "\\]")

    def _format_message(self, event: LogEvent) -> bytes:
        """
        Format event as syslog message bytes.

        Args:
            event: Log event

        Returns:
            Message bytes
        """
        if self.syslog_config.use_rfc5424:
            msg = self._format_rfc5424(event)
        else:
            msg = self._format_rfc3164(event)

        msg_bytes = msg.encode("utf-8")

        # Add octet counting for TCP (RFC 5425)
        if (
            self.syslog_config.protocol.lower() in ("tcp", "tls")
            and self.syslog_config.use_framing
        ):
            msg_bytes = f"{len(msg_bytes)} ".encode("utf-8") + msg_bytes

        return msg_bytes

    async def push(self, event: LogEvent) -> bool:
        """
        Push a single log event.

        Args:
            event: Log event to push

        Returns:
            True if successfully pushed
        """
        try:
            if not await self._connect():
                return False

            msg = self._format_message(event)
            protocol = self.syslog_config.protocol.lower()

            if protocol == "udp":
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self._socket.sendto,
                    msg,
                    (self.syslog_config.host, self.syslog_config.port),
                )
                return True

            elif protocol in ("tcp", "tls"):
                self._writer.write(msg)
                await self._writer.drain()
                return True

        except (ConnectionError, BrokenPipeError) as e:
            logger.warning(f"Syslog connection error: {e}")
            await self._disconnect()
            return False

        except Exception as e:
            logger.error(f"Syslog error: {e}")
            return False

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

        if not await self._connect():
            return 0

        success_count = 0
        protocol = self.syslog_config.protocol.lower()

        try:
            if protocol == "udp":
                # UDP: send each message separately
                for event in events:
                    if await self.push(event):
                        success_count += 1

            elif protocol in ("tcp", "tls"):
                # TCP: batch write
                for event in events:
                    msg = self._format_message(event)
                    self._writer.write(msg)
                    success_count += 1

                await self._writer.drain()

        except Exception as e:
            logger.error(f"Syslog batch error: {e}")
            await self._disconnect()

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
        Check syslog connection health.

        Returns:
            Health status dict
        """
        protocol = self.syslog_config.protocol.lower()

        if protocol == "udp":
            # UDP is connectionless, just check socket exists
            return {
                "healthy": True,
                "protocol": protocol,
                "host": self.syslog_config.host,
                "port": self.syslog_config.port,
            }

        # TCP/TLS: try to connect
        try:
            was_connected = self._connected
            if not was_connected:
                await self._connect()

            return {
                "healthy": self._connected,
                "protocol": protocol,
                "host": self.syslog_config.host,
                "port": self.syslog_config.port,
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "protocol": protocol,
                "host": self.syslog_config.host,
                "port": self.syslog_config.port,
            }

    async def close(self) -> None:
        """Close the stream and cleanup resources."""
        await self.flush()
        await self._disconnect()
        logger.info(
            f"Syslog stream closed: "
            f"{self.syslog_config.host}:{self.syslog_config.port}"
        )
