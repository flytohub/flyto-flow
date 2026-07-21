"""
Notifications API Routes

Provides notification endpoints.
"""

import logging

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from api.auth import get_current_user
from gateway.providers.hub import get_data_provider
from gateway.providers.data.models import (
    NotificationDTO,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


# =============================================================================
# Response Models
# =============================================================================


class UnreadCountResponse(BaseModel):
    """Unread count response"""
    count: int


class MarkAllReadResponse(BaseModel):
    """Mark all read response"""
    ok: bool
    count: int


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/", response_model=PaginatedResponse)
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List user's notifications"""
    provider = get_data_provider()
    result = await provider.notifications.list_notifications(
        user_id=current_user["id"],
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )
    return result


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
):
    """Get unread notification count"""
    provider = get_data_provider()
    count = await provider.notifications.get_unread_count(current_user["id"])
    return UnreadCountResponse(count=count)


@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get single notification by ID"""
    provider = get_data_provider()
    notification = await provider.notifications.get_notification(
        user_id=current_user["id"],
        notification_id=notification_id,
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"ok": True, "notification": notification}


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark notification as read"""
    provider = get_data_provider()
    success = await provider.notifications.mark_as_read(
        user_id=current_user["id"],
        notification_id=notification_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"ok": True, "message": "Notification marked as read"}


@router.post("/read-all", response_model=MarkAllReadResponse)
async def mark_all_as_read(
    current_user: dict = Depends(get_current_user),
):
    """Mark all notifications as read"""
    provider = get_data_provider()
    count = await provider.notifications.mark_all_as_read(current_user["id"])
    return MarkAllReadResponse(ok=True, count=count)


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete notification"""
    provider = get_data_provider()
    success = await provider.notifications.delete_notification(
        user_id=current_user["id"],
        notification_id=notification_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"ok": True, "message": "Notification deleted"}
