"""
Log Manager Service

Manages log collection and broadcasting to WebSocket clients.
Captures Python logging output and streams to connected frontends.
"""

import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import Set, Dict, Any, Optional
from collections import deque
from fastapi import WebSocket

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class LogEntry:
    """Single log entry"""

    def __init__(
        self,
        level: str,
        message: str,
        logger_name: str,
        timestamp: Optional[datetime] = None
    ):
        """Initialize a log entry with level, message, logger name, and optional timestamp."""
        self.level = level
        self.message = message
        self.logger_name = logger_name
        self.timestamp = timestamp or _utc_now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to a serializable dictionary."""
        return {
            "level": self.level,
            "message": self.message,
            "logger": self.logger_name,
            "timestamp": self.timestamp.isoformat()
        }


class WebSocketLogHandler(logging.Handler):
    """Custom logging handler that sends logs to WebSocket clients"""

    def __init__(self, log_manager: "LogManager"):
        """Initialize handler with a reference to the LogManager for broadcasting."""
        super().__init__()
        self.log_manager = log_manager
        self.setFormatter(logging.Formatter('%(message)s'))

    def emit(self, record: logging.LogRecord):
        """Emit a log record by scheduling a broadcast to WebSocket clients."""
        try:
            entry = LogEntry(
                level=record.levelname,
                message=self.format(record),
                logger_name=record.name
            )
            # Schedule broadcast in event loop
            asyncio.create_task(self.log_manager.broadcast(entry))
        except Exception:
            self.handleError(record)


class LogManager:
    """
    Singleton manager for log streaming

    Usage:
        manager = LogManager.get_instance()
        manager.install_handler()  # Start capturing logs
        await manager.add_client(websocket)  # Add WebSocket client
    """

    _instance: Optional["LogManager"] = None

    def __init__(self):
        """Initialize the log manager with empty client set and log buffer."""
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._buffer: deque = deque(maxlen=500)  # Keep last 500 logs
        self._handler: Optional[WebSocketLogHandler] = None
        self._installed = False

    @classmethod
    def get_instance(cls) -> "LogManager":
        """Return the singleton LogManager instance, creating it if needed."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def install_handler(self, level: int = logging.DEBUG):
        """Install log handler to capture logs"""
        if self._installed:
            return

        self._handler = WebSocketLogHandler(self)
        self._handler.setLevel(level)

        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(self._handler)

        self._installed = True
        logger.info("WebSocket log handler installed")

    def uninstall_handler(self):
        """Remove log handler"""
        if not self._installed or not self._handler:
            return

        root_logger = logging.getLogger()
        root_logger.removeHandler(self._handler)

        self._installed = False
        logger.info("WebSocket log handler removed")

    async def add_client(self, websocket: WebSocket):
        """Add a WebSocket client"""
        async with self._lock:
            self._clients.add(websocket)
            logger.info(f"Log client connected. Total: {len(self._clients)}")

        # Send buffered logs to new client
        await self._send_buffer(websocket)

    async def remove_client(self, websocket: WebSocket):
        """Remove a WebSocket client"""
        async with self._lock:
            self._clients.discard(websocket)
            logger.info(f"Log client disconnected. Total: {len(self._clients)}")

    async def _send_buffer(self, websocket: WebSocket):
        """Send buffered logs to a client"""
        try:
            for entry in list(self._buffer):
                await websocket.send_json({
                    "type": "log",
                    "data": entry.to_dict()
                })
        except Exception:
            pass

    async def broadcast(self, entry: LogEntry):
        """Broadcast log entry to all connected clients"""
        # Add to buffer
        self._buffer.append(entry)

        # Skip if no clients
        if not self._clients:
            return

        message = {
            "type": "log",
            "data": entry.to_dict()
        }

        # Broadcast to all clients
        disconnected = set()
        for client in list(self._clients):
            try:
                await client.send_json(message)
            except Exception:
                disconnected.add(client)

        # Remove disconnected clients
        if disconnected:
            async with self._lock:
                self._clients -= disconnected

    def add_log(self, level: str, message: str, logger_name: str = "system"):
        """Manually add a log entry"""
        entry = LogEntry(level, message, logger_name)
        asyncio.create_task(self.broadcast(entry))

    def get_buffer(self) -> list:
        """Get buffered logs"""
        return [entry.to_dict() for entry in self._buffer]

    def clear_buffer(self):
        """Clear log buffer"""
        self._buffer.clear()


def get_log_manager() -> LogManager:
    """Get the singleton log manager instance"""
    return LogManager.get_instance()
