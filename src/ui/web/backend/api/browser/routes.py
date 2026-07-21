"""
Browser Screencast Routes

WebSocket: /ws/browser/{execution_id}  — binary JPEG frames + JSON control
REST:      /browser/{execution_id}/screencast/status
"""

import asyncio
import logging
import os
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/browser", tags=["Browser"])


@router.get("/{execution_id}/screencast/status")
async def screencast_status(execution_id: str):
    """Get screencast status for an execution."""
    from services.screencast import get_screencast_manager
    manager = get_screencast_manager()
    return {"ok": True, **manager.get_status(execution_id)}


async def _verify_ws_token(token: str) -> Optional[str]:
    """Verify a token via auth provider and return the user ID, or None on failure.

    Accepts both Firebase ID tokens and worker API keys (worker:<key>).
    """
    if not token:
        return None

    # Worker API key: "worker:<key>" — used by cloud workers for frame push
    if token.startswith("worker:"):
        import hmac
        worker_key = os.environ.get("WORKER_API_KEY", "")
        if worker_key and hmac.compare_digest(token[len("worker:"):], worker_key):
            return "cloud-worker"
        return None

    # Firebase ID token
    try:
        from gateway.providers.hub import get_auth_provider
        auth_provider = get_auth_provider()
        result = await auth_provider.verify_token(token)
        if result.ok and result.user:
            return result.user.id
    except Exception:
        pass
    return None


async def handle_browser_websocket(
    websocket: WebSocket,
    execution_id: str,
    user_id: str = "",
    user_name: str = "Anonymous",
    token: str = "",
):
    """
    WebSocket handler for browser screencast.

    Requires a valid Firebase ID token in the `token` query parameter.

    Server → Client:
      - Binary: JPEG frame data
      - JSON: screencast.started, screencast.stopped, control.state,
              control.granted, control.released, control.requested, viewer.count

    Client → Server (JSON):
      - mouse.click, mouse.move, mouse.down, mouse.up, mouse.wheel
      - key.down, key.up, key.type
      - control.request, control.release, control.transfer
    """
    from services.screencast import get_screencast_manager

    # Authenticate: require a valid Firebase token (cloud mode)
    # In local mode, sidecar auth middleware already validates requests,
    # so accept the connection with the client-supplied user_id.
    from gateway.config import get_gateway_config
    is_local = get_gateway_config().is_local
    verified_uid = await _verify_ws_token(token) if token else None
    if not verified_uid and not is_local:
        await websocket.close(code=4001, reason="Authentication required")
        logger.warning(f"Browser WS rejected: no valid token, exec={execution_id}")
        return
    if not verified_uid:
        verified_uid = user_id or "anonymous"

    manager = get_screencast_manager()
    await websocket.accept()

    # Use verified UID, ignore client-supplied user_id
    user_id = verified_uid

    await manager.add_viewer(execution_id, websocket, user_id)
    logger.info(f"Browser viewer connected: exec={execution_id} user={user_id}")

    # Send assigned user_id back so client knows its identity
    # (important when server generates anon ID)
    try:
        await websocket.send_json({"type": "welcome", "user_id": user_id})
    except Exception:
        pass

    try:
        while True:
            data = await websocket.receive_text()
            try:
                import json
                msg = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                continue

            msg_type = msg.get("type", "")

            if msg_type == "control.request":
                await manager.request_control(
                    execution_id, user_id,
                    user_name=msg.get("user_name", user_name),
                )
            elif msg_type == "control.release":
                await manager.release_control(execution_id, user_id)
            elif msg_type == "control.transfer":
                to_user = msg.get("to_user_id", "")
                if to_user:
                    await manager.transfer_control(execution_id, to_user)
            elif msg_type == "browser.close":
                # Client requests browser close — stop screencast + close page
                from services.runtime.execution.workflow_runner import cancel_browser_idle_timer
                cancel_browser_idle_timer(execution_id)
                await manager.close_browser(execution_id)
            elif msg_type.startswith(("mouse.", "key.")):
                # Fire-and-forget: don't block WS receive loop on CDP dispatch
                asyncio.ensure_future(
                    manager.handle_input(execution_id, user_id, msg)
                )
                # Reset idle timer on user interaction
                from services.runtime.execution.workflow_runner import reset_browser_idle_timer
                reset_browser_idle_timer(execution_id)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"Browser WS error: {e}")
    finally:
        await manager.remove_viewer(execution_id, websocket)
        logger.info(f"Browser viewer disconnected: exec={execution_id} user={user_id}")
