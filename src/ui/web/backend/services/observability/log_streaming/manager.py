"""
Log Stream Manager

Central manager for multiple log streaming backends.
Supports failover, buffering, and async dispatch.
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from services.observability.log_streaming.interface import LogEvent, LogStreamInterface, StreamConfig

logger = logging.getLogger(__name__)

# Global manager instance
_manager_instance: Optional["LogStreamManager"] = None


@dataclass
class StreamStatus:
    """Status of a registered stream."""
    name: str
    stream_type: str
    enabled: bool
    healthy: bool
    last_push: Optional[str] = None
    events_pushed: int = 0
    events_failed: int = 0
    last_error: Optional[str] = None


@dataclass
class ManagerConfig:
    """Configuration for the log stream manager."""
    buffer_size: int = 1000
    flush_interval_seconds: float = 5.0
    dispatch_timeout_seconds: float = 10.0
    retry_failed_streams: bool = True
    failover_enabled: bool = True


class LogStreamManager:
    """
    Central manager for log streaming.

    Features:
    - Multiple backend support (webhook, elasticsearch, syslog, file)
    - Buffering with configurable size
    - Async dispatch to all enabled streams
    - Health monitoring and failover
    - Graceful shutdown with flush
    """

    def __init__(self, config: Optional[ManagerConfig] = None):
        """
        Initialize manager.

        Args:
            config: Manager configuration
        """
        self.config = config or ManagerConfig()
        self._streams: Dict[str, LogStreamInterface] = {}
        self._buffer: deque = deque(maxlen=self.config.buffer_size)
        self._status: Dict[str, StreamStatus] = {}
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()

        logger.info(f"LogStreamManager initialized with buffer_size={self.config.buffer_size}")

    def register_stream(
        self,
        name: str,
        stream: LogStreamInterface,
    ) -> None:
        """
        Register a log stream backend.

        Args:
            name: Unique name for the stream
            stream: Stream implementation
        """
        self._streams[name] = stream
        self._status[name] = StreamStatus(
            name=name,
            stream_type=type(stream).__name__,
            enabled=stream.config.enabled,
            healthy=True,
        )
        logger.info(f"Registered stream: {name} ({type(stream).__name__})")

    def unregister_stream(self, name: str) -> bool:
        """
        Unregister a log stream.

        Args:
            name: Stream name

        Returns:
            True if removed
        """
        if name in self._streams:
            del self._streams[name]
            del self._status[name]
            logger.info(f"Unregistered stream: {name}")
            return True
        return False

    async def push(self, event: LogEvent) -> Dict[str, bool]:
        """
        Push event to all enabled streams.

        Args:
            event: Log event to push

        Returns:
            Dict of stream name -> success status
        """
        results = {}

        for name, stream in self._streams.items():
            if not stream.should_stream(event):
                continue

            try:
                success = await asyncio.wait_for(
                    stream.push(event),
                    timeout=self.config.dispatch_timeout_seconds,
                )
                results[name] = success

                if success:
                    self._status[name].events_pushed += 1
                    self._status[name].last_push = datetime.now(timezone.utc).isoformat()
                    self._status[name].healthy = True
                else:
                    self._status[name].events_failed += 1

            except asyncio.TimeoutError:
                logger.warning(f"Timeout pushing to stream: {name}")
                results[name] = False
                self._status[name].events_failed += 1
                self._status[name].last_error = "Timeout"

            except Exception as e:
                logger.error(f"Error pushing to stream {name}: {e}")
                results[name] = False
                self._status[name].events_failed += 1
                self._status[name].last_error = str(e)
                self._status[name].healthy = False

        return results

    async def push_buffered(self, event: LogEvent) -> None:
        """
        Add event to buffer for batch dispatch.

        Args:
            event: Log event to buffer
        """
        async with self._lock:
            self._buffer.append(event)

            # Flush if buffer is full
            if len(self._buffer) >= self.config.buffer_size:
                await self._flush_buffer()

    async def _flush_buffer(self) -> int:
        """
        Flush buffered events to all streams.

        Returns:
            Number of events flushed
        """
        if not self._buffer:
            return 0

        async with self._lock:
            events = list(self._buffer)
            self._buffer.clear()

        if not events:
            return 0

        total_pushed = 0

        for name, stream in self._streams.items():
            if not stream.config.enabled:
                continue

            # Filter events for this stream
            filtered = [e for e in events if stream.should_stream(e)]
            if not filtered:
                continue

            try:
                pushed = await asyncio.wait_for(
                    stream.push_batch(filtered),
                    timeout=self.config.dispatch_timeout_seconds * 2,
                )
                total_pushed += pushed
                self._status[name].events_pushed += pushed
                self._status[name].last_push = datetime.now(timezone.utc).isoformat()

            except Exception as e:
                logger.error(f"Error flushing to stream {name}: {e}")
                self._status[name].events_failed += len(filtered)
                self._status[name].last_error = str(e)

        logger.debug(f"Flushed {total_pushed} events to streams")
        return total_pushed

    async def flush_all(self) -> Dict[str, int]:
        """
        Flush all streams.

        Returns:
            Dict of stream name -> events flushed
        """
        # First flush buffer
        await self._flush_buffer()

        # Then flush each stream's internal buffer
        results = {}
        for name, stream in self._streams.items():
            try:
                flushed = await stream.flush()
                results[name] = flushed
            except Exception as e:
                logger.error(f"Error flushing stream {name}: {e}")
                results[name] = 0

        return results

    async def start(self) -> None:
        """Start the manager's background tasks."""
        if self._running:
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("LogStreamManager started")

    async def stop(self) -> None:
        """Stop the manager and flush remaining events."""
        if not self._running:
            return

        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self.flush_all()

        # Close all streams
        for name, stream in self._streams.items():
            try:
                await stream.close()
            except Exception as e:
                logger.error(f"Error closing stream {name}: {e}")

        logger.info("LogStreamManager stopped")

    async def _periodic_flush(self) -> None:
        """Background task for periodic buffer flush."""
        while self._running:
            try:
                await asyncio.sleep(self.config.flush_interval_seconds)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all streams.

        Returns:
            Health status dict
        """
        stream_health = {}
        all_healthy = True

        for name, stream in self._streams.items():
            try:
                health = await stream.health_check()
                stream_health[name] = health
                if not health.get("healthy", False):
                    all_healthy = False
                    self._status[name].healthy = False
                else:
                    self._status[name].healthy = True
            except Exception as e:
                stream_health[name] = {"healthy": False, "error": str(e)}
                self._status[name].healthy = False
                all_healthy = False

        return {
            "healthy": all_healthy,
            "running": self._running,
            "buffer_size": len(self._buffer),
            "buffer_capacity": self.config.buffer_size,
            "streams": stream_health,
        }

    def get_status(self) -> Dict[str, StreamStatus]:
        """
        Get status of all registered streams.

        Returns:
            Dict of stream name -> status
        """
        return dict(self._status)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregated statistics.

        Returns:
            Statistics dict
        """
        total_pushed = sum(s.events_pushed for s in self._status.values())
        total_failed = sum(s.events_failed for s in self._status.values())

        return {
            "total_streams": len(self._streams),
            "enabled_streams": sum(1 for s in self._status.values() if s.enabled),
            "healthy_streams": sum(1 for s in self._status.values() if s.healthy),
            "total_events_pushed": total_pushed,
            "total_events_failed": total_failed,
            "buffer_size": len(self._buffer),
            "running": self._running,
        }


def get_log_stream_manager() -> LogStreamManager:
    """
    Get or create the global log stream manager.

    Returns:
        LogStreamManager instance
    """
    global _manager_instance

    if _manager_instance is None:
        _manager_instance = LogStreamManager()

    return _manager_instance


def reset_log_stream_manager() -> None:
    """Reset the global manager instance."""
    global _manager_instance
    _manager_instance = None


async def configure_streams_from_env() -> LogStreamManager:
    """
    Configure streams from environment variables.

    Environment variables:
    - LOG_STREAM_WEBHOOK_URL: Webhook endpoint
    - LOG_STREAM_ELASTICSEARCH_URL: Elasticsearch URL
    - LOG_STREAM_SYSLOG_HOST: Syslog server host
    - LOG_STREAM_FILE_PATH: File output path

    Returns:
        Configured manager
    """
    import os

    manager = get_log_stream_manager()

    # Webhook stream
    webhook_url = os.getenv("LOG_STREAM_WEBHOOK_URL")
    if webhook_url:
        from services.observability.log_streaming.webhook_stream import WebhookStream
        stream = WebhookStream(url=webhook_url)
        manager.register_stream("webhook", stream)

    # Elasticsearch stream
    es_url = os.getenv("LOG_STREAM_ELASTICSEARCH_URL")
    if es_url:
        from services.observability.log_streaming.elasticsearch_stream import ElasticsearchStream
        stream = ElasticsearchStream(url=es_url)
        manager.register_stream("elasticsearch", stream)

    # Syslog stream
    syslog_host = os.getenv("LOG_STREAM_SYSLOG_HOST")
    if syslog_host:
        from services.observability.log_streaming.syslog_stream import SyslogStream
        port = int(os.getenv("LOG_STREAM_SYSLOG_PORT", "514"))
        stream = SyslogStream(host=syslog_host, port=port)
        manager.register_stream("syslog", stream)

    # File stream
    file_path = os.getenv("LOG_STREAM_FILE_PATH")
    if file_path:
        from services.observability.log_streaming.file_stream import FileStream
        stream = FileStream(file_path=file_path)
        manager.register_stream("file", stream)

    return manager
