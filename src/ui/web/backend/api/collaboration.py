"""
Collaboration API Routes

Handles:
- Random invite code generation & resolution (stored in Firestore)
- Join request → pending approval flow
- Member management (approve / reject / remove)
- Session info
"""

import secrets
import string
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from api.auth import get_current_user
from api.errors import bad_request, forbidden, internal_error, not_found
from api.collab_requests import requests_router
from gateway.providers.data.providers.collaboration_provider import (
    CollaborationInviteCodeExhaustedError,
    CollaborationPermissionError,
    CollaborationTemplateNotFoundError,
)
from gateway.providers.hub import get_collaboration_provider
from services.audit.crud_logger import log_crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collaboration", tags=["collaboration"])
router.include_router(requests_router)


def _generate_random_code(length: int = 6) -> str:
    """Generate a cryptographically random invite code (uppercase alphanumeric)."""
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def _normalize_invite_code(code: str) -> str:
    """Accept FLY-ABC123 or ABC123 and return the raw code."""
    return code.strip().upper().replace("-", "").replace("FLY", "")


# =============================================================================
# Invite Code Generation & Resolution
# =============================================================================


class InviteCodeResponse(BaseModel):
    """Response containing a generated invite code for a workflow."""

    invite_code: str
    workflow_id: str


@router.get("/invite-code/{workflow_id}")
async def generate_invite_code(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
) -> InviteCodeResponse:
    """
    Get or generate a unique random invite code for a workflow.

    - First call: generates a random code, stores in `collaboration_invites` collection
    - Subsequent calls: returns the existing code
    - Only the owner can generate invite codes
    """
    user_id = current_user["id"]

    if not workflow_id:
        bad_request("Invalid workflow ID")

    try:
        code = await get_collaboration_provider().get_or_create_invite_code(
            workflow_id=workflow_id,
            owner_id=user_id,
            code_factory=_generate_random_code,
        )
        return InviteCodeResponse(invite_code=f"FLY-{code}", workflow_id=workflow_id)

    except HTTPException:
        raise
    except CollaborationTemplateNotFoundError:
        not_found("Template not found")
    except CollaborationPermissionError:
        forbidden("Only the owner can generate invite codes")
    except CollaborationInviteCodeExhaustedError:
        internal_error("Failed to generate unique code")
    except Exception:
        logger.exception("Error generating invite code")
        internal_error("Failed to generate invite code")


@router.post("/regenerate-code/{workflow_id}")
async def regenerate_invite_code(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
) -> InviteCodeResponse:
    """
    Regenerate the invite code for a workflow (revokes the old one).
    Only the owner can do this.
    """
    user_id = current_user["id"]

    try:
        code = await get_collaboration_provider().regenerate_invite_code(
            workflow_id=workflow_id,
            owner_id=user_id,
            code_factory=_generate_random_code,
        )
        logger.info("Regenerated collaboration invite code")
        return InviteCodeResponse(invite_code=f"FLY-{code}", workflow_id=workflow_id)

    except HTTPException:
        raise
    except CollaborationTemplateNotFoundError:
        not_found("Template not found")
    except CollaborationPermissionError:
        forbidden("Only the owner can regenerate invite codes")
    except CollaborationInviteCodeExhaustedError:
        internal_error("Failed to generate unique code")
    except Exception:
        logger.exception("Error regenerating invite code")
        internal_error("Failed to regenerate invite code")


class ResolveCodeResponse(BaseModel):
    """Response from resolving an invite code to a workflow."""

    workflow_id: str
    workflow_name: str


@router.get("/resolve-code/{code}")
async def resolve_invite_code(code: str) -> ResolveCodeResponse:
    """
    Resolve an invite code to a workflow ID.
    Looks up the code in the `collaboration_invites` collection.
    """
    # Clean: accept "FLY-ABC123" or "ABC123"
    raw = _normalize_invite_code(code)
    if not raw or len(raw) < 4:
        bad_request("Invalid invite code format")

    try:
        result = await get_collaboration_provider().resolve_invite_code(raw)
        if not result:
            not_found("Invalid invite code. Please check and try again.")

        return ResolveCodeResponse(
            workflow_id=result["workflow_id"],
            workflow_name=result["workflow_name"],
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error resolving invite code")
        internal_error("Failed to resolve invite code")


# =============================================================================
# Join Request (Pending Approval)
# =============================================================================


class JoinRequest(BaseModel):
    """Request body for joining a collaboration via invite code."""

    code: str


class JoinResponse(BaseModel):
    """Response after successfully joining a collaboration session."""

    workflow_id: str
    workflow_name: str
    status: str  # "approved"


@router.post("/join")
async def join_collaboration(
    data: JoinRequest,
    current_user: dict = Depends(get_current_user),
) -> JoinResponse:
    """
    Join a collaboration session via invite code.
    Having the code = authorized. Directly added to collaboration_members.
    """
    user_id = current_user["id"]

    # Resolve invite code
    raw = _normalize_invite_code(data.code)
    if not raw or len(raw) < 4:
        bad_request("Invalid invite code format")

    try:
        result = await get_collaboration_provider().join_by_invite_code(
            raw_code=raw,
            user_id=user_id,
        )
        if not result:
            not_found("Invalid invite code.")

        if result.get("added"):
            workflow_id = result["workflow_id"]
            logger.info("Collaboration member joined through invite code")
            log_crud(
                "create",
                "collaboration_member",
                workflow_id,
                current_user,
                details={"member_id": user_id},
            )

        return JoinResponse(
            workflow_id=result["workflow_id"],
            workflow_name=result["workflow_name"],
            status=result["status"],
        )

    except HTTPException:
        raise
    except CollaborationTemplateNotFoundError:
        not_found("Template not found")
    except Exception:
        logger.exception("Error joining collaboration")
        internal_error("Failed to join collaboration")


# =============================================================================
# Member Management (List / Remove)
# =============================================================================


class MembersResponse(BaseModel):
    """Response listing collaboration members and the workflow owner."""

    members: List[str]  # user_id list
    owner_id: Optional[str] = None


@router.get("/{workflow_id}/members")
async def get_members(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
) -> MembersResponse:
    """Get collaboration members for a workflow."""
    try:
        result = await get_collaboration_provider().get_members(workflow_id)
        if not result:
            not_found("Template not found")

        return MembersResponse(
            members=result["members"],
            owner_id=result["owner_id"],
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting collaboration members")
        internal_error("Failed to get members")


@router.delete("/{workflow_id}/members/{member_id}")
async def remove_member(
    workflow_id: str,
    member_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Remove an approved collaboration member. Only the owner can do this.
    """
    user_id = current_user["id"]

    try:
        removed = await get_collaboration_provider().remove_member(
            workflow_id=workflow_id,
            owner_id=user_id,
            member_id=member_id,
        )
        if removed:
            logger.info("Collaboration member removed")
            log_crud(
                "delete",
                "collaboration_member",
                workflow_id,
                current_user,
                details={"member_id": member_id},
            )

        return {"ok": True}

    except HTTPException:
        raise
    except CollaborationTemplateNotFoundError:
        not_found("Template not found")
    except CollaborationPermissionError:
        forbidden("Only the owner can remove members")
    except Exception:
        logger.exception("Error removing collaboration member")
        internal_error("Failed to remove member")


# =============================================================================
# Terminate Session (Owner only)
# =============================================================================


@router.post("/{workflow_id}/terminate")
async def terminate_session(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Terminate a collaboration session. Owner only.
    Broadcasts termination to all connected participants and closes their connections.
    """
    user_id = current_user["id"]

    try:
        owner_id = await get_collaboration_provider().get_owner_id(workflow_id)
        if owner_id is None:
            not_found("Template not found")

        if user_id != owner_id:
            forbidden("Only the owner can terminate the session")

        # Terminate room: broadcast, close connections, clean up Firestore
        from websocket.collaboration import collaboration_manager
        await collaboration_manager.terminate_room(workflow_id, "The owner ended the collaboration session.")

        logger.info("Collaboration session terminated")
        return {"ok": True}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error terminating collaboration session")
        internal_error("Failed to terminate session")


# =============================================================================
# Session Info
# =============================================================================


@router.get("/session/{workflow_id}/info")
async def get_session_info(workflow_id: str):
    """
    Get information about an active collaboration session.
    """
    from websocket.collaboration import collaboration_manager

    room = collaboration_manager.rooms.get(workflow_id)

    if not room:
        return {
            "active": False,
            "participant_count": 0,
            "participants": [],
        }

    return {
        "active": True,
        "participant_count": len(room.presence),
        "participants": [
            {
                "user_id": p.user_id,
                "display_name": p.user_name,
                "user_avatar": p.user_avatar,
                "presence": "active",
                "color": p.color,
            }
            for p in room.presence.values()
        ],
    }
