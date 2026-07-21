"""
Collaboration Request Routes

Handles collaboration access requests for locked templates:
- Submit request (pending approval)
- List requests (owner only)
- Check own request status
- Approve / reject requests

Split from collaboration.py to keep each file focused.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import logging

from api.auth import get_current_user
from api.errors import bad_request, forbidden, internal_error, not_found
from services.collaboration.request_store import (
    get_template,
    get_template_owner,
    add_collaboration_member,
    find_pending_request,
    create_request,
    list_requests,
    get_latest_request,
    get_request,
    resolve_request,
)

logger = logging.getLogger(__name__)
requests_router = APIRouter()


# =============================================================================
# Pydantic Models
# =============================================================================


class CollabRequestBody(BaseModel):
    """Request body for submitting a collaboration access request."""

    message: str = ""  # Optional message from requester


class CollabRequestResponse(BaseModel):
    """Response after creating or retrieving a collaboration request."""

    id: str
    template_id: str
    status: str  # pending, approved, rejected


class CollabRequestItem(BaseModel):
    """A single collaboration request with requester details."""

    id: str
    template_id: str
    requester_id: str
    requester_name: str
    requester_avatar: str
    message: str
    status: str
    created_at: str


class ResolveRequestBody(BaseModel):
    """Request body for approving or rejecting a collaboration request."""

    action: str  # "approve" or "reject"


# =============================================================================
# Routes
# =============================================================================


@requests_router.post("/request/{template_id}")
async def request_collaboration(
    template_id: str,
    body: CollabRequestBody,
    current_user: dict = Depends(get_current_user),
) -> CollabRequestResponse:
    """
    Request collaboration access to a locked template.
    Creates a pending request that the owner can approve or reject.
    """
    user_id = current_user["id"]

    try:
        # Get template
        template_data = await get_template(template_id)
        if not template_data:
            not_found("Template not found")

        owner_id = get_template_owner(template_data)

        if user_id == owner_id:
            bad_request("You are the owner of this template")

        # Check if already a collaborator
        members = template_data.get("collaboration_members", [])
        if user_id in members:
            bad_request("You are already a collaborator")

        # Check for existing pending request
        existing = await find_pending_request(template_id, user_id)
        if existing:
            return CollabRequestResponse(
                id=existing["id"],
                template_id=template_id,
                status="pending",
            )

        # Create new request
        now = datetime.now(timezone.utc).isoformat()
        request_data = {
            "template_id": template_id,
            "requester_id": user_id,
            "requester_name": current_user.get("name", ""),
            "requester_avatar": current_user.get("avatar", ""),
            "owner_id": owner_id,
            "message": body.message[:500],  # Cap message length
            "status": "pending",
            "created_at": now,
            "resolved_at": None,
            "resolved_by": None,
        }

        request_id = await create_request(request_data)

        # Notify owner
        try:
            from gateway.providers.hub import get_notification_provider
            from services.collaboration.collaboration_notifications import notify_collab_requested
            template_name = template_data.get("template_name") or template_data.get("name") or "Untitled"
            await notify_collab_requested(
                get_notification_provider(),
                owner_id, user_id,
                current_user.get("name", "Someone"),
                template_name, template_id, request_id,
                body.message,
            )
        except Exception as e:
            logger.warning(f"Failed to send collab request notification: {e}")

        logger.info(f"User {user_id} requested collaboration for template {template_id}")
        return CollabRequestResponse(
            id=request_id,
            template_id=template_id,
            status="pending",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating collaboration request: {e}")
        internal_error("Failed to create collaboration request")


@requests_router.get("/requests/{template_id}")
async def list_collaboration_requests(
    template_id: str,
    status: Optional[str] = "pending",
    current_user: dict = Depends(get_current_user),
) -> Dict:
    """
    List collaboration requests for a template. Owner only.
    """
    user_id = current_user["id"]

    try:
        # Verify ownership
        template_data = await get_template(template_id)
        if not template_data:
            not_found("Template not found")

        owner_id = get_template_owner(template_data)
        if user_id != owner_id:
            forbidden("Only the owner can view requests")

        # Query requests
        docs = await list_requests(template_id, status)
        requests = []
        for d in docs:
            requests.append(CollabRequestItem(
                id=d["id"],
                template_id=d["template_id"],
                requester_id=d["requester_id"],
                requester_name=d.get("requester_name", ""),
                requester_avatar=d.get("requester_avatar", ""),
                message=d.get("message", ""),
                status=d["status"],
                created_at=d.get("created_at", ""),
            ))

        return {"ok": True, "requests": [r.model_dump() for r in requests]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing collaboration requests: {e}")
        internal_error("Failed to list requests")


@requests_router.get("/request/{template_id}/status")
async def get_my_request_status(
    template_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict:
    """
    Check current user's collaboration request status for a template.
    Returns the latest request status, or null if no request exists.
    """
    user_id = current_user["id"]

    try:
        latest = await get_latest_request(template_id, user_id)
        if latest:
            return {
                "ok": True,
                "request": {
                    "id": latest["id"],
                    "status": latest["status"],
                    "created_at": latest.get("created_at", ""),
                },
            }

        return {"ok": True, "request": None}

    except Exception as e:
        logger.error(f"Error checking request status: {e}")
        internal_error("Failed to check request status")


@requests_router.post("/requests/{request_id}/resolve")
async def resolve_collaboration_request(
    request_id: str,
    body: ResolveRequestBody,
    current_user: dict = Depends(get_current_user),
) -> Dict:
    """
    Approve or reject a collaboration request. Owner only.
    On approval, the requester is added to collaboration_members.
    """
    user_id = current_user["id"]

    if body.action not in ("approve", "reject"):
        bad_request("Action must be 'approve' or 'reject'")

    try:
        # Get request
        request_data = await get_request(request_id)
        if not request_data:
            not_found("Request not found")

        if request_data["status"] != "pending":
            bad_request(f"Request already {request_data['status']}")

        template_id = request_data["template_id"]

        # Verify ownership
        template_data = await get_template(template_id)
        if not template_data:
            not_found("Template not found")

        owner_id = get_template_owner(template_data)
        if user_id != owner_id:
            forbidden("Only the owner can resolve requests")

        approved = body.action == "approve"
        status_str = "approved" if approved else "rejected"

        # Update request status
        await resolve_request(request_id, status_str, user_id)

        # If approved, add to collaboration_members
        if approved:
            requester_id = request_data["requester_id"]
            members = template_data.get("collaboration_members", [])
            await add_collaboration_member(template_id, requester_id, members)

        # Notify requester
        try:
            from gateway.providers.hub import get_notification_provider
            from services.collaboration.collaboration_notifications import notify_collab_resolved
            template_name = template_data.get("template_name") or template_data.get("name") or "Untitled"
            await notify_collab_resolved(
                get_notification_provider(),
                request_data["requester_id"], user_id,
                current_user.get("name", "Someone"),
                template_name, template_id, request_id,
                approved,
            )
        except Exception as e:
            logger.warning(f"Failed to send collab resolve notification: {e}")

        logger.info(f"Owner {user_id} {status_str} collab request {request_id} for template {template_id}")
        return {"ok": True, "status": status_str}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving collaboration request: {e}")
        internal_error("Failed to resolve request")
