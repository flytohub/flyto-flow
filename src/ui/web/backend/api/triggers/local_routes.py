"""
Local trigger routes — utility endpoints and webhook test mode.

These run on the Desktop app (Local Runner). No Firestore dependency.
"""

import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.auth import get_current_user
from services.infra.scheduler import CronParser
from services.webhook import WebhookRepository

from .models import CronValidateRequest

logger = logging.getLogger(__name__)

local_router = APIRouter(prefix="/triggers", tags=["triggers"])


# ============================================================================
# Cron Utility Endpoints
# ============================================================================


@local_router.post("/cron/validate")
async def validate_cron_expression(request: CronValidateRequest) -> Dict[str, Any]:
    """
    Validate a cron expression.

    Returns validation result with next run time if valid.
    """
    result = CronParser.validate(request.expression)

    if not result.valid:
        return {
            "ok": False,
            "valid": False,
            "error": result.error,
        }

    try:
        next_run = CronParser.get_next_run(request.expression)
        return {
            "ok": True,
            "valid": True,
            "expression": request.expression,
            "next_run_at": next_run.isoformat(),
        }
    except Exception:
        logger.exception("Failed to calculate next cron run")
        return {
            "ok": False,
            "valid": False,
            "error": "Unable to calculate next cron run",
        }


@local_router.get("/cron/next")
async def get_cron_next_run(
    expression: str,
    timezone: str = "UTC",
    count: int = Query(5, ge=1, le=20)
) -> Dict[str, Any]:
    """
    Calculate next run times for a cron expression.

    Useful for testing cron expressions.
    """
    try:
        next_runs = []
        current = None
        for _ in range(count):
            current = CronParser.get_next_run(expression, current, timezone_str=timezone)
            next_runs.append(current.isoformat())

        return {
            "ok": True,
            "expression": expression,
            "timezone": timezone,
            "next_runs": next_runs,
            # Also include single next_run_at for backwards compatibility
            "next_run_at": next_runs[0] if next_runs else None,
        }
    except Exception:
        logger.exception("Invalid cron expression")
        raise HTTPException(
            status_code=400,
            detail="Invalid cron expression",
        )


# ============================================================================
# Webhook Test Mode
# ============================================================================

# In-memory test listeners: { webhook_id: asyncio.Future }
_test_listeners: Dict[str, asyncio.Future] = {}


def _verify_webhook_owner(webhook, user_id: str) -> None:
    """Verify the current user owns this webhook."""
    if webhook.user_id and webhook.user_id != user_id:
        raise HTTPException(status_code=404, detail="Webhook not found")


@local_router.post("/webhooks/{webhook_id}/test/start")
async def start_webhook_test(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Start a 30-second test listener for a webhook.

    Returns the trigger URL and cURL example. The frontend should then
    poll /test/result to get the received payload.
    """
    webhook = WebhookRepository.get(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    _verify_webhook_owner(webhook, current_user["id"])

    # Cancel any existing test listener for this webhook
    if webhook_id in _test_listeners:
        old = _test_listeners.pop(webhook_id)
        if not old.done():
            old.cancel()

    # Create a new future for this test
    loop = asyncio.get_event_loop()
    _test_listeners[webhook_id] = loop.create_future()

    trigger_url = f"/api/triggers/webhooks/{webhook_id}/trigger"

    return {
        "ok": True,
        "webhook_id": webhook_id,
        "trigger_url": trigger_url,
        "curl_example": f'curl -X POST http://localhost:8000{trigger_url} -H "Content-Type: application/json" -d \'{{"test": true}}\'',
        "timeout_seconds": 30,
    }


@local_router.get("/webhooks/{webhook_id}/test/result")
async def get_webhook_test_result(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Wait for test webhook payload (long-poll, max 30 seconds).

    Returns the received payload or timeout.
    """
    webhook = WebhookRepository.get(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    _verify_webhook_owner(webhook, current_user["id"])

    future = _test_listeners.get(webhook_id)
    if not future:
        return {"ok": False, "error": "No active test listener"}

    try:
        payload = await asyncio.wait_for(future, timeout=30.0)
        return {"ok": True, "received": True, "payload": payload}
    except asyncio.TimeoutError:
        return {"ok": True, "received": False, "message": "Test timed out (30s)"}
    finally:
        _test_listeners.pop(webhook_id, None)


@local_router.post("/webhooks/{webhook_id}/test/receive")
async def receive_webhook_test(
    webhook_id: str,
    request: Request,
) -> Dict[str, Any]:
    """
    Receive a test webhook payload (called by external services or cURL).

    No signature verification — test mode only.
    """
    future = _test_listeners.get(webhook_id)
    if not future or future.done():
        raise HTTPException(status_code=404, detail="No active test listener for this webhook")

    body = await request.body()
    try:
        import json
        payload = json.loads(body) if body else {}
    except Exception:
        payload = {"raw": body.decode("utf-8", errors="replace")}

    future.set_result({
        "headers": dict(request.headers),
        "body": payload,
        "method": request.method,
    })

    return {"ok": True, "message": "Test payload received"}
