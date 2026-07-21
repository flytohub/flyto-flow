"""
WebSocket Module Sync

Provides real-time module update notifications to connected frontend clients.
"""
import asyncio
import logging
from typing import Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ModuleSyncManager:
    """
    Manages WebSocket connections for module sync.

    Features:
    - Connection management
    - Broadcast module updates
    - Heartbeat to keep connections alive
    """

    def __init__(self):
        """Initialize connection set and heartbeat task."""
        self.active_connections: Set[WebSocket] = set()
        self._heartbeat_task = None

    async def connect(self, websocket: WebSocket):
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Module sync client connected. Total: {len(self.active_connections)}")

        # Start heartbeat if first connection
        if len(self.active_connections) == 1 and self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"Module sync client disconnected. Total: {len(self.active_connections)}")

        # Stop heartbeat if no connections
        if len(self.active_connections) == 0 and self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Failed to send to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_module_update(self, version_info: dict):
        """Broadcast module update notification."""
        await self.broadcast({
            "type": "modules_updated",
            "version": version_info.get("version"),
            "updated_at": version_info.get("updated_at"),
            "module_count": version_info.get("module_count", 0),
            "composite_count": version_info.get("composite_count", 0),
        })

    async def _heartbeat_loop(self):
        """Send periodic heartbeat to keep connections alive."""
        while True:
            try:
                await asyncio.sleep(30)
                await self.broadcast({"type": "heartbeat"})
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break


# Singleton instance
_manager = ModuleSyncManager()


def get_module_sync_manager() -> ModuleSyncManager:
    """Get singleton ModuleSyncManager instance."""
    return _manager


async def handle_module_sync_websocket(websocket: WebSocket):
    """
    Handle a module sync WebSocket connection.

    Usage in FastAPI:
        @app.websocket("/ws/modules")
        async def websocket_endpoint(websocket: WebSocket):
            await handle_module_sync_websocket(websocket)
    """
    manager = get_module_sync_manager()
    await manager.connect(websocket)

    try:
        while True:
            # Wait for messages from client (for future features)
            data = await websocket.receive_json()

            # Handle client messages
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

            elif data.get("type") == "get_version":
                from services.infra.module_reloader import get_module_reloader
                reloader = get_module_reloader()
                await websocket.send_json({
                    "type": "version",
                    **reloader.version_info
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
