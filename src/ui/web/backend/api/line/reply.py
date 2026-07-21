"""
LINE Reply Handler

Endpoints for desktop app to send messages back to LINE users.
"""
import os
import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException

from api.line.models import (
    LineReplyRequest,
    LineReplyResponse,
    LinePushRequest,
)
from api.errors import safe_error_response
from gateway.providers.hub import get_line_provider

logger = logging.getLogger(__name__)
router = APIRouter()

# LINE API endpoints
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
LINE_PROFILE_URL = "https://api.line.me/v2/bot/profile"

# Explicit timeout for outbound LINE Messaging API calls. Without this httpx
# has no timeout, so a hung LINE endpoint would hang the user-facing request
# indefinitely. 10s overall, 5s to establish the connection.
LINE_HTTP_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


def get_line_headers() -> Dict[str, str]:
    """Get headers for LINE API requests"""
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="LINE_CHANNEL_ACCESS_TOKEN not configured")

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


@router.post("/line/reply", response_model=LineReplyResponse)
async def reply_to_line(request: LineReplyRequest):
    """
    Reply to LINE user.

    If reply_token is provided and still valid (within 30s), uses reply API (free).
    Otherwise, uses push API (costs money but no time limit).

    Called by desktop app after processing a message.
    """
    headers = get_line_headers()

    # Determine which API to use
    if request.reply_token:
        # Try reply first (free)
        url = LINE_REPLY_URL
        payload = {
            "replyToken": request.reply_token,
            "messages": request.messages,
        }
    else:
        # Use push (costs money)
        url = LINE_PUSH_URL
        payload = {
            "to": request.user_id,
            "messages": request.messages,
        }

    try:
        async with httpx.AsyncClient(timeout=LINE_HTTP_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                logger.info(f"Successfully sent LINE message to {request.user_id[:8]}...")
                return LineReplyResponse(ok=True)

            # If reply failed (token expired), try push
            if request.reply_token and response.status_code == 400:
                error_data = response.json()
                if "Invalid reply token" in str(error_data):
                    logger.info("Reply token expired, falling back to push")
                    # Retry with push API
                    push_payload = {
                        "to": request.user_id,
                        "messages": request.messages,
                    }
                    push_response = await client.post(
                        LINE_PUSH_URL, json=push_payload, headers=headers
                    )
                    if push_response.status_code == 200:
                        return LineReplyResponse(ok=True)
                    else:
                        error = push_response.json()
                        logger.error(f"LINE push failed: {error}")
                        return LineReplyResponse(ok=False, error="Failed to send message")

            # Other errors
            error_data = response.json() if response.text else {"message": response.reason_phrase}
            logger.error(f"LINE API error: {error_data}")
            return LineReplyResponse(ok=False, error="Failed to send message")

    except Exception as e:
        logger.error(f"Failed to send LINE message: {e}", exc_info=True)
        return LineReplyResponse(ok=False, error="Failed to send message")


@router.post("/line/push", response_model=LineReplyResponse)
async def push_to_line(request: LinePushRequest):
    """
    Push message to LINE user (no reply token needed).

    Use this for proactive messages, not in response to user actions.
    Note: Push messages cost money on LINE's pricing tier.
    """
    headers = get_line_headers()

    payload = {
        "to": request.user_id,
        "messages": request.messages,
    }

    try:
        async with httpx.AsyncClient(timeout=LINE_HTTP_TIMEOUT) as client:
            response = await client.post(LINE_PUSH_URL, json=payload, headers=headers)

            if response.status_code == 200:
                logger.info(f"Successfully pushed LINE message to {request.user_id[:8]}...")
                return LineReplyResponse(ok=True)

            error_data = response.json() if response.text else {"message": response.reason_phrase}
            logger.error(f"LINE push error: {error_data}")
            return LineReplyResponse(ok=False, error="Failed to push message")

    except Exception as e:
        logger.error(f"Failed to push LINE message: {e}", exc_info=True)
        return LineReplyResponse(ok=False, error="Failed to push message")


@router.get("/line/messages/pending")
async def get_pending_messages(user_id: Optional[str] = None, limit: int = 20):
    """
    Get pending messages from Firestore.

    Desktop app can poll this endpoint or use Firestore realtime listener directly.
    """
    messages = await get_line_provider().list_pending_messages(
        user_id=user_id,
        limit=limit,
    )

    return {"ok": True, "messages": messages, "count": len(messages)}


@router.post("/line/messages/{message_id}/claim")
async def claim_message(message_id: str, device_id: str):
    """
    Claim a message for processing.

    Desktop app should call this before processing to prevent
    duplicate processing by multiple devices.
    """
    try:
        return await get_line_provider().claim_message(message_id, device_id)

    except Exception as e:
        return safe_error_response(e, "Failed to claim message")


@router.post("/line/messages/{message_id}/complete")
async def complete_message(message_id: str):
    """
    Mark a message as processed.

    Desktop app should call this after successfully sending a reply.
    """
    try:
        return await get_line_provider().complete_message(message_id)
    except Exception as e:
        return safe_error_response(e, "Failed to complete message")


@router.get("/line/profile/{user_id}")
async def get_line_profile(user_id: str):
    """
    Get LINE user profile.

    Returns display name and profile picture URL.
    """
    headers = get_line_headers()

    try:
        async with httpx.AsyncClient(timeout=LINE_HTTP_TIMEOUT) as client:
            response = await client.get(
                f"{LINE_PROFILE_URL}/{user_id}",
                headers=headers
            )

            if response.status_code == 200:
                profile = response.json()
                return {
                    "ok": True,
                    "profile": {
                        "user_id": profile.get("userId"),
                        "display_name": profile.get("displayName"),
                        "picture_url": profile.get("pictureUrl"),
                        "status_message": profile.get("statusMessage"),
                    }
                }

            return {"ok": False, "error": f"Failed to get profile: {response.status_code}"}

    except Exception as e:
        return safe_error_response(e, "Failed to get LINE profile")


@router.get("/line/conversations/{user_id}")
async def get_conversation_state(user_id: str):
    """
    Get conversation state for a user.

    Returns the current step in the conversation flow.
    """
    conversation = await get_line_provider().get_conversation_state(user_id)
    return {
        "ok": True,
        "conversation": conversation,
    }


@router.put("/line/conversations/{user_id}")
async def update_conversation_state(user_id: str, state: Dict[str, Any]):
    """
    Update conversation state for a user.

    Desktop app should call this to track conversation progress.
    """
    try:
        return await get_line_provider().update_conversation_state(user_id, state)
    except Exception as e:
        return safe_error_response(e, "Failed to update conversation state")
