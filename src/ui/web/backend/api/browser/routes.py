"""Local browser screencast routes."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/browser", tags=["Browser"])
@router.get("/{execution_id}/screencast/status")
async def screencast_status(execution_id: str):
    from services.screencast import get_screencast_manager

    manager = get_screencast_manager()
    return {"ok": True, **manager.get_status(execution_id)}


async def handle_browser_websocket(websocket: WebSocket, execution_id: str):
    """Handle the CE UI's same-origin browser frames and input events."""
    from services.screencast import get_screencast_manager

    manager = get_screencast_manager()
    await websocket.accept()
    await manager.add_connection(execution_id, websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue

            message_type = message.get("type", "")
            if message_type == "browser.close":
                from services.runtime.execution.workflow_runner import cancel_browser_idle_timer

                cancel_browser_idle_timer(execution_id)
                await manager.close_browser(execution_id)
            elif message_type.startswith(("mouse.", "key.")):
                asyncio.create_task(
                    manager.handle_input(execution_id, message)
                )
                from services.runtime.execution.workflow_runner import reset_browser_idle_timer

                reset_browser_idle_timer(execution_id)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("Local browser WebSocket closed: %s", exc)
    finally:
        await manager.remove_connection(execution_id, websocket)
