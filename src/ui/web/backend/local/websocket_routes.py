"""
WebSocket Route Registration

All WebSocket endpoint handlers for the local runner,
plus the sidecar secret check helper.

Extracted from main_local.py.
"""

import hmac
import logging

from fastapi import FastAPI, WebSocket, Query

logger = logging.getLogger(__name__)


async def _ws_check_secret(websocket: WebSocket, sidecar_secret: str) -> bool:
    """Validate sidecar secret on WebSocket upgrade. Returns True if authorized."""
    if not sidecar_secret:
        return True
    token = (
        websocket.query_params.get("_secret")
        or websocket.cookies.get("_flyto_secret")
    )
    if not token or not hmac.compare_digest(token, sidecar_secret):
        await websocket.close(code=4403)
        return False
    return True


def register_websocket_routes(app: FastAPI, *, sidecar_secret: str) -> None:
    """Register all WebSocket endpoints on the given app.

    Args:
        app: The FastAPI application instance.
        sidecar_secret: The sidecar secret for auth validation (empty string = skip).
    """

    @app.websocket("/ws/modules")
    async def websocket_modules(websocket: WebSocket):
        if not await _ws_check_secret(websocket, sidecar_secret):
            return
        from websocket.module_sync import handle_module_sync_websocket
        await handle_module_sync_websocket(websocket)

    @app.websocket("/ws/logs")
    async def websocket_logs(websocket: WebSocket):
        if not await _ws_check_secret(websocket, sidecar_secret):
            return
        from services.observability.log_manager import get_log_manager
        await websocket.accept()
        log_manager = get_log_manager()
        await log_manager.add_client(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data == "clear":
                    log_manager.clear_buffer()
                    await websocket.send_json({"type": "cleared"})
        except Exception:
            pass
        finally:
            await log_manager.remove_client(websocket)

    @app.websocket("/ws/executions/{execution_id}")
    async def websocket_executions(websocket: WebSocket, execution_id: str):
        """WebSocket endpoint for real-time execution status updates."""
        if not await _ws_check_secret(websocket, sidecar_secret):
            return
        from api.workflows.websocket import manager
        await manager.connect(websocket, execution_id)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            manager.disconnect(websocket, execution_id)

    @app.websocket("/ws/browser/{execution_id}")
    async def websocket_browser(
        websocket: WebSocket,
        execution_id: str,
        user_id: str = Query(default=""),
        user_name: str = Query(default="Anonymous"),
        token: str = Query(default=""),
    ):
        """WebSocket endpoint for real-time browser screencast streaming."""
        if not await _ws_check_secret(websocket, sidecar_secret):
            return
        from api.browser.routes import handle_browser_websocket
        await handle_browser_websocket(websocket, execution_id, user_id=user_id, user_name=user_name, token=token)

    @app.websocket("/ws/breakpoints")
    async def websocket_breakpoints(websocket: WebSocket):
        """WebSocket endpoint for real-time breakpoint notifications (interact dialogs)."""
        if not await _ws_check_secret(websocket, sidecar_secret):
            return
        from websocket.breakpoint_ws import get_breakpoint_ws_manager
        manager = get_breakpoint_ws_manager()
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
        except Exception:
            pass
        finally:
            await manager.disconnect(websocket)

    @app.websocket("/ws/collaboration/{workflow_id}")
    async def websocket_collaboration(
        websocket: WebSocket,
        workflow_id: str,
        org_id: str = Query(default=""),
        user_id: str = Query(default=""),
        user_name: str = Query(default="Anonymous"),
        user_avatar: str = Query(default=""),
    ):
        """WebSocket for real-time collaboration (runs locally for low latency)."""
        if not await _ws_check_secret(websocket, sidecar_secret):
            return
        from websocket.collaboration import collaboration_websocket_endpoint

        await collaboration_websocket_endpoint(
            websocket=websocket,
            workflow_id=workflow_id,
            org_id=org_id,
            user_id=user_id,
            user_name=user_name,
            user_avatar=user_avatar,
        )
