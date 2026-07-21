"""
Workflow WebSocket Management

Real-time execution log streaming.

NOTE: ConnectionManager and the global `manager` singleton now live in
services/websocket_manager.py (the canonical location).  This module
re-exports them for backward compatibility so existing imports from
api.workflows.websocket continue to work.
"""

from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# ── Re-exports from services layer (canonical location) ──────────────
from services.websocket_manager import (  # noqa: F401
    ConnectionManager,
    manager,
    get_connection_manager,
)

router = APIRouter()


@router.websocket("/ws/executions/{execution_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    execution_id: str,
    token: Optional[str] = None
):
    """
    WebSocket real-time execution logs.

    Authentication via query parameter: ?token=<bearer_token>
    """
    from gateway.providers.hub import get_auth_provider

    # Verify token if provided
    if token:
        auth_provider = get_auth_provider()
        try:
            result = await auth_provider.verify_token(token)
            if not result.ok:
                await websocket.close(code=4001, reason="Invalid token")
                return
        except Exception:
            await websocket.close(code=4001, reason="Token verification failed")
            return

    await manager.connect(websocket, execution_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, execution_id)
