"""
WebSocket Connection Manager

Shared state for real-time execution log streaming.
Lives in services/ so both api/ and services/ can import without circular deps.
"""

from typing import Dict, List

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for execution streaming."""

    def __init__(self):
        """Initialize with empty connection registry."""
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, execution_id: str):
        """Accept and register a WebSocket connection for an execution."""
        await websocket.accept()
        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = []
        self.active_connections[execution_id].append(websocket)

    def disconnect(self, websocket: WebSocket, execution_id: str):
        """Remove a WebSocket connection from an execution."""
        if execution_id in self.active_connections:
            self.active_connections[execution_id].remove(websocket)

    async def send_log(self, execution_id: str, log: dict):
        """Broadcast a log entry to all connections for an execution."""
        if execution_id in self.active_connections:
            for connection in self.active_connections[execution_id]:
                try:
                    await connection.send_json(log)
                except Exception:
                    pass


# Global connection manager (singleton)
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager
