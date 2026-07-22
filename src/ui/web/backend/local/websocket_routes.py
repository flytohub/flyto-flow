"""Same-origin WebSocket endpoints for the local Flyto2 Flow process."""

from fastapi import FastAPI, WebSocket


def register_websocket_routes(app: FastAPI) -> None:
    """Register local runtime WebSockets; no account or sidecar secret exists."""

    @app.websocket("/ws/modules")
    async def websocket_modules(websocket: WebSocket):
        from websocket.module_sync import handle_module_sync_websocket

        await handle_module_sync_websocket(websocket)

    @app.websocket("/ws/logs")
    async def websocket_logs(websocket: WebSocket):
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
        from services.websocket_manager import manager

        await manager.connect(websocket, execution_id)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            manager.disconnect(websocket, execution_id)

    @app.websocket("/ws/browser/{execution_id}")
    async def websocket_browser(websocket: WebSocket, execution_id: str):
        from api.browser.routes import handle_browser_websocket

        await handle_browser_websocket(websocket, execution_id)

    @app.websocket("/ws/breakpoints")
    async def websocket_breakpoints(websocket: WebSocket):
        from websocket.breakpoint_ws import get_breakpoint_ws_manager

        manager = get_breakpoint_ws_manager()
        await manager.connect(websocket)
        try:
            while True:
                if await websocket.receive_text() == "ping":
                    await websocket.send_json({"type": "pong"})
        except Exception:
            pass
        finally:
            await manager.disconnect(websocket)
