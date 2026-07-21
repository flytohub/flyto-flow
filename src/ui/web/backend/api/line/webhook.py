"""
LINE Webhook Handler

Receives LINE webhook events and stores them through the data provider
for desktop app to process.
"""
import os
import hmac
import hashlib
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Header

from api.line.models import (
    LineWebhookRequest,
    LineEvent,
)
from gateway.providers.data.providers import LineProvider
from gateway.providers.hub import get_line_provider

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_line_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    """
    Verify LINE webhook signature.

    LINE uses HMAC-SHA256 with channel secret to sign the request body.
    """
    if not signature or not channel_secret:
        return False

    hash_value = hmac.new(
        channel_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()

    expected_signature = base64.b64encode(hash_value).decode('utf-8')

    return hmac.compare_digest(signature, expected_signature)


def _model_dict(model) -> dict:
    """Return a pydantic model as a plain dict across v1/v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)


@router.post("/webhook/line")
async def line_webhook(
    request: Request,
    x_line_signature: Optional[str] = Header(None, alias="X-Line-Signature")
):
    """
    LINE Webhook Endpoint

    Receives events from LINE Platform and stores them through the data provider
    for desktop app to process.

    Flow:
    1. Verify LINE signature
    2. Parse events
    3. Store messages for desktop processing
    4. Return 200 OK immediately (LINE requires fast response)
    """
    # Get raw body for signature verification
    body = await request.body()

    # Get channel secret from environment
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")

    if not channel_secret:
        logger.error("LINE_CHANNEL_SECRET not configured")
        raise HTTPException(status_code=500, detail="LINE webhook not configured")

    # Verify signature
    if not verify_line_signature(body, x_line_signature, channel_secret):
        logger.warning("Invalid LINE signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Parse webhook body
    try:
        import json
        data = json.loads(body)
        webhook = LineWebhookRequest(**data)
    except Exception as e:
        logger.error(f"Failed to parse LINE webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    line_provider = get_line_provider()

    # Process each event
    processed_count = 0
    for event in webhook.events:
        try:
            await process_line_event(line_provider, event)
            processed_count += 1
        except Exception as e:
            logger.error(f"Failed to process LINE event: {e}")
            # Continue processing other events

    logger.info(f"Processed {processed_count}/{len(webhook.events)} LINE events")

    # Return 200 OK immediately (LINE requires this)
    return {"ok": True, "processed": processed_count}


async def process_line_event(line_provider: LineProvider, event: LineEvent):
    """
    Process a single LINE event.

    Stores message events through the active data provider for desktop pickup.
    """
    # Only process message and postback events
    if event.type not in ("message", "postback"):
        logger.debug(f"Ignoring event type: {event.type}")
        return

    user_id = event.source.userId
    if not user_id:
        logger.warning("Event has no userId, skipping")
        return

    # Build message document
    now = datetime.now(timezone.utc)
    reply_token_expires = now + timedelta(seconds=30) if event.replyToken else None

    # Determine content based on event type
    if event.type == "message" and event.message:
        msg_type = event.message.type
        if msg_type == "text":
            content = event.message.text
        else:
            # For non-text messages, store the message object
            content = _model_dict(event.message)
    elif event.type == "postback" and event.postback:
        msg_type = "postback"
        content = event.postback.data
    else:
        logger.warning(f"Unknown event structure: {event.type}")
        return

    message_doc = {
        "user_id": user_id,
        "reply_token": event.replyToken,
        "type": msg_type,
        "content": content,
        "timestamp": now,
        "status": "pending",
        "processed_by": None,
        "reply_token_expires_at": reply_token_expires,
        "line_timestamp": event.timestamp,
        "source_type": event.source.type,
        "group_id": event.source.groupId,
        "room_id": event.source.roomId,
    }

    message_id = await line_provider.store_incoming_message(
        user_id=user_id,
        message=message_doc,
        user_update={
            "last_active_at": now,
            "source_type": event.source.type,
        },
    )
    logger.info(f"Stored LINE message: {message_id} from user {user_id[:8]}...")


@router.get("/webhook/line/health")
async def line_webhook_health():
    """Health check for LINE webhook endpoint"""
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    channel_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    try:
        provider_name = get_line_provider().__class__.__name__
    except Exception:
        provider_name = None

    return {
        "ok": True,
        "line_configured": bool(channel_secret and channel_token),
        "line_provider": provider_name,
        "status": "ready" if (channel_secret and channel_token) else "not_configured"
    }
