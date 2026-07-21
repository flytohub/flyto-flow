"""
WebSocket Breakpoint Notifier

Pushes breakpoint events (pending/resolved) to connected frontend clients.
Enables real-time interact dialog without polling.
"""

import asyncio
import json
import logging
from typing import Dict, List, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class BreakpointWSManager:
    """
    Manages WebSocket connections for breakpoint notifications.

    Clients connect to /ws/breakpoints and receive:
    - {"type": "breakpoint.pending", "breakpoint": {...}}
    - {"type": "breakpoint.resolved", "breakpoint_id": "...", "status": "..."}
    """

    def __init__(self):
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)
        logger.debug("Breakpoint WS client connected (%d total)", len(self._clients))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)
        logger.debug("Breakpoint WS client disconnected (%d total)", len(self._clients))

    async def broadcast(self, message: dict) -> None:
        """Send message to all connected clients."""
        async with self._lock:
            clients = list(self._clients)

        dead = []
        for ws in clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.discard(ws)

    async def notify_pending(self, breakpoint_data: dict) -> None:
        """Notify all clients of a new pending breakpoint."""
        await self.broadcast({
            "type": "breakpoint.pending",
            "breakpoint": breakpoint_data,
        })

    async def notify_resolved(self, breakpoint_id: str, status: str) -> None:
        """Notify all clients that a breakpoint was resolved."""
        await self.broadcast({
            "type": "breakpoint.resolved",
            "breakpoint_id": breakpoint_id,
            "status": status,
        })

    @property
    def client_count(self) -> int:
        return len(self._clients)


# Global instance
_bp_ws_manager: BreakpointWSManager = None


def get_breakpoint_ws_manager() -> BreakpointWSManager:
    global _bp_ws_manager
    if _bp_ws_manager is None:
        _bp_ws_manager = BreakpointWSManager()
    return _bp_ws_manager
