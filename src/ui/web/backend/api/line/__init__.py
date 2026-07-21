"""
LINE Bot API

Webhook receiver and reply endpoints for LINE Bot integration.
Desktop app processes messages and calls reply endpoint.
"""
from fastapi import APIRouter

from api.line.webhook import router as webhook_router
from api.line.reply import router as reply_router

router = APIRouter()

# Include webhook routes (no prefix - uses /webhook/line)
router.include_router(webhook_router)

# Include reply routes (no prefix - uses /line/*)
router.include_router(reply_router)

__all__ = ["router"]
