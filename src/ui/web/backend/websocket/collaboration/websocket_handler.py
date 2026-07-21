"""
Collaboration WebSocket Handler

Standalone handler functions for the collaboration WebSocket endpoint.
Extracted from manager.py for maintainability.
"""

import asyncio
import logging
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from gateway.providers.hub import get_provider_hub
from websocket.collaboration.models import MessageType

logger = logging.getLogger(__name__)


async def check_collaboration_access(workflow_id: str, user_id: str):
    """
    Check if user is authorized to join a collaboration session.

    Returns (has_access: bool, owner_id: str | None).
    """
    try:
        from services.cloud_client import cloud_get
        data = await cloud_get(f"templates/{workflow_id}")
        if not data:
            # Cloud API unreachable — allow access (auth verified at WS handshake)
            return True, None

        # API returns {"ok": true, "template": {...}} — unwrap if needed
        template = data.get("template", data)

        owner = template.get("creator_id") or template.get("author_id")
        members = template.get("collaboration_members", [])
        return (user_id == owner or user_id in members), owner
    except Exception as e:
        logger.error(f"Error checking collaboration access: {e}")
        return True, None


async def _ensure_collab_conversation(conv_id: str, workflow_id: str, participant_ids: list):
    """Ensure a collaboration conversation exists via cloud API."""
    try:
        from services.cloud_client import cloud_post
        await cloud_post(
            "chat/conversations",
            json={
                "conversation_id": conv_id,
                "participants": participant_ids,
                "is_collab": True,
                "workflow_id": workflow_id,
            },
        )
    except Exception as e:
        logger.warning(f"Error ensuring collab conversation: {e}")


async def _quota_tick_loop(
    websocket: WebSocket,
    user_id: str,
    limit_hours: int,
    room,
) -> None:
    """Background task: every 60s, add 1 minute and push updated quota_info."""
    from services.collaboration.quota import add_minutes, build_quota_info

    try:
        while True:
            await asyncio.sleep(60)
            new_total = await add_minutes(user_id, 1)
            total_minutes = limit_hours * 60
            remaining = max(0, total_minutes - new_total)

            info = build_quota_info(
                is_pro=False,
                is_owner=True,
                used_minutes=new_total,
                limit_hours=limit_hours,
            )

            try:
                await asyncio.wait_for(websocket.send_json(info), timeout=5.0)
            except (asyncio.TimeoutError, Exception):
                break  # WebSocket closed or unresponsive

            if remaining <= 0:
                # Quota exceeded -- notify and disconnect
                await websocket.send_json({
                    "type": "error",
                    "code": "QUOTA_EXCEEDED",
                    "message": "Your free collaboration time has been used up this month. Upgrade to Pro for unlimited collaboration.",
                })
                await websocket.close(code=4008, reason="Quota exceeded")
                break
    except asyncio.CancelledError:
        pass


async def _enforce_quota(
    websocket: WebSocket,
    user_id: str,
    template_owner_id: Optional[str],
    is_pro: bool,
    is_owner: bool,
    room,
) -> tuple:
    """Enforce collaboration quota.

    Returns (should_disconnect: bool, quota_tick_task: Optional[asyncio.Task]).
    When should_disconnect is True the caller must return immediately.
    """
    if is_pro or not is_owner:
        # Pro users and guests -> unlimited
        await websocket.send_json({"type": "quota_info", "is_unlimited": True})
        return False, None

    # Free owner -> check and enforce quota
    from services.collaboration.quota import get_used_minutes, build_quota_info, get_configured_free_hours

    limit_hours = await get_configured_free_hours()
    used = await get_used_minutes(user_id)

    if limit_hours is not None:
        total_minutes = limit_hours * 60
        if used >= total_minutes:
            # Already exceeded
            await websocket.send_json({
                "type": "error",
                "code": "QUOTA_EXCEEDED",
                "message": "Your free collaboration time has been used up this month. Upgrade to Pro for unlimited collaboration.",
            })
            await websocket.close(code=4008, reason="Quota exceeded")
            return True, None

        info = build_quota_info(is_pro=False, is_owner=True, used_minutes=used, limit_hours=limit_hours)
        await websocket.send_json(info)

        # Start background tick loop
        task = asyncio.create_task(
            _quota_tick_loop(websocket, user_id, limit_hours, room)
        )
        return False, task

    # limit_hours is None -> unlimited (shouldn't happen for free, but safe fallback)
    await websocket.send_json({"type": "quota_info", "is_unlimited": True})
    return False, None


async def _cancel_task(task: Optional[asyncio.Task]) -> None:
    """Cancel an asyncio task and suppress CancelledError."""
    if not task or task.done():
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def handle_collaboration_websocket(
    websocket: WebSocket,
    workflow_id: str,
    organization_id: str,
    user_id: str,
    user_name: str,
    user_avatar: Optional[str] = None,
    is_pro: bool = False,
    already_accepted: bool = False,
) -> None:
    """Handle collaboration WebSocket connection."""
    from websocket.collaboration.manager import collaboration_manager

    if not already_accepted:
        await websocket.accept()

    # Authorization check
    has_access, template_owner_id = await check_collaboration_access(workflow_id, user_id)
    if not has_access:
        await websocket.send_json({
            "type": MessageType.ERROR.value,
            "code": "NOT_AUTHORIZED",
            "message": "You need an invite code to join this collaboration session.",
        })
        await websocket.close(code=4003, reason="Not authorized")
        return

    room = await collaboration_manager.join_room(
        workflow_id=workflow_id,
        organization_id=organization_id,
        user_id=user_id,
        user_name=user_name,
        websocket=websocket,
        user_avatar=user_avatar,
    )

    if template_owner_id and not room.owner_id:
        room.owner_id = template_owner_id

    # Quota enforcement
    is_owner = (template_owner_id is not None and user_id == template_owner_id)
    should_disconnect, quota_tick_task = await _enforce_quota(
        websocket, user_id, template_owner_id, is_pro, is_owner, room,
    )
    if should_disconnect:
        return

    try:
        await collaboration_manager.run_message_loop(
            websocket, room, user_id, user_name, user_avatar, workflow_id,
        )
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from workflow {workflow_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}")
    finally:
        await _cancel_task(quota_tick_task)
        await collaboration_manager.leave_room(workflow_id, user_id)


async def collaboration_websocket_endpoint(
    websocket: WebSocket,
    workflow_id: str,
    org_id: str,
    user_id: str,
    user_name: str,
    user_avatar: str,
) -> None:
    """Shared WebSocket endpoint logic for real-time collaboration.

    Validates user_id, fetches user data from the active provider, accepts the
    websocket, and delegates to handle_collaboration_websocket.
    Used by both main.py and main_local.py to avoid duplication.
    """
    # Validate user_id - reject if empty
    if not user_id or not user_id.strip():
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "code": "INVALID_USER",
            "message": "Invalid user ID. Please log in again.",
        })
        await websocket.close(code=4001, reason="Invalid user ID")
        return

    # Fetch user data from the active provider (authoritative source for subscription status)
    actual_user_name = user_name
    actual_user_avatar = user_avatar
    is_pro = True  # Default to unlimited; only restrict when provider confirms free plan
    try:
        user_data = await get_provider_hub().data.collaboration.get_websocket_user_context(user_id)
        if user_data:
            actual_user_name = user_data.get("display_name") or user_data.get("username") or user_name
            actual_user_avatar = user_data.get("avatar_url") or user_avatar
            plan = (user_data.get("subscription_plan") or "").lower()
            status = (user_data.get("subscription_status") or "").lower()
            is_pro = plan in ("pro", "team", "enterprise", "offline") and status in ("active", "trialing")
    except Exception as e:
        logger.warning(f"Collaboration: Failed to fetch user data, defaulting to unlimited: {e}")

    await websocket.accept()
    try:
        await handle_collaboration_websocket(
            websocket=websocket,
            workflow_id=workflow_id,
            organization_id=org_id,
            user_id=user_id,
            user_name=actual_user_name,
            user_avatar=actual_user_avatar if actual_user_avatar else None,
            is_pro=is_pro,
            already_accepted=True,
        )
    except WebSocketDisconnect:
        # Normal client disconnect — not an error.
        logger.debug(
            f"Collaboration WS disconnected: workflow={workflow_id} user={user_id}"
        )
    except Exception as e:
        # The socket is already accepted, so a swallowed setup-phase failure
        # (join_room / quota / send_json) leaves the client connected but
        # silently dead. Log it and close the socket so the client can react.
        logger.error(
            f"Collaboration WS handler crashed: workflow={workflow_id} user={user_id}: {e}",
            exc_info=True,
        )
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
