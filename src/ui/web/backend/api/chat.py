"""
Chat API Routes

Provides chat conversation and messaging endpoints.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from api.auth import get_current_user
from gateway.providers.hub import get_data_provider
from gateway.providers.data.models import (
    ConversationDTO,
    ConversationCreateDTO,
    MessageDTO,
    MessageCreateDTO,
    MessageType,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

# Simple in-memory cache for user profiles (display_name + avatar_url)
_profile_cache: dict[str, dict] = {}
_PROFILE_CACHE_MAX = 200


def _profile_value(profile, *names: str):
    for name in names:
        value = (
            profile.get(name)
            if isinstance(profile, dict)
            else getattr(profile, name, None)
        )
        if value:
            return value
    return None


async def _get_user_profiles(provider, user_ids: list[str]) -> dict[str, dict]:
    """Batch-fetch user profiles, with in-memory cache."""
    result = {}
    missing = []
    for uid in user_ids:
        if uid in _profile_cache:
            result[uid] = _profile_cache[uid]
        else:
            missing.append(uid)

    if missing:
        users_provider = getattr(provider, "users", None)
        for uid in missing:
            profile = {}
            if users_provider is not None:
                try:
                    profile_dto = await users_provider.get_profile(uid)
                    if profile_dto:
                        profile = {
                            "display_name": _profile_value(
                                profile_dto,
                                "display_name",
                                "username",
                            ),
                            "avatar_url": _profile_value(
                                profile_dto,
                                "avatar_url",
                                "photo_url",
                            ),
                        }
                except NotImplementedError:
                    profile = {}
                except Exception as e:
                    logger.debug("Failed to fetch user profile %s: %s", uid, e)

            result[uid] = profile
            _profile_cache[uid] = profile

    # Evict oldest if cache too large
    if len(_profile_cache) > _PROFILE_CACHE_MAX:
        excess = len(_profile_cache) - _PROFILE_CACHE_MAX
        for key in list(_profile_cache.keys())[:excess]:
            del _profile_cache[key]

    return result


# =============================================================================
# Health & Utility Endpoints
# =============================================================================


@router.get("/health")
async def chat_health():
    """Health check endpoint for chat service."""
    return {
        "ok": True,
        "status": "healthy",
        "service": "chat",
        "version": "1.0.0",
    }


@router.get("/suggestions")
async def get_chat_suggestions():
    """Get chat suggestions/quick replies."""
    return {
        "ok": True,
        "suggestions": [
            {"id": "1", "text": "Hello", "category": "greeting"},
            {"id": "2", "text": "Thank you", "category": "gratitude"},
            {"id": "3", "text": "How can I help?", "category": "assistance"},
        ],
    }


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateConversationRequest(BaseModel):
    """Create conversation request"""
    participant_ids: List[str] = Field(..., min_length=1)


class SendMessageRequest(BaseModel):
    """Send message request"""
    conversation_id: str
    message_type: MessageType = MessageType.TEXT
    content: str = Field(..., min_length=1, max_length=2000)
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_size: Optional[int] = None
    order_id: Optional[str] = None
    # Collaboration persistence only: the real author and the full set of room
    # participants, threaded through from an authenticated WebSocket session.
    # Honored solely for collab_* conversations so chat is attributed to the
    # actual sender (not the session host) and every guest can load history.
    sender_id: Optional[str] = None
    participants: Optional[List[str]] = None


# =============================================================================
# Conversation Endpoints
# =============================================================================


@router.get("/conversations", response_model=PaginatedResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List user's conversations"""
    provider = get_data_provider()
    result = await provider.chat.list_conversations(
        user_id=current_user["id"],
        page=page,
        page_size=page_size,
    )
    return result


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get single conversation with participant info"""
    provider = get_data_provider()
    result = await provider.chat.get_conversation(
        user_id=current_user["id"],
        conversation_id=conversation_id,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Return enriched conversation data with ok flag
    return {"ok": True, **result}


@router.post("/conversations")
async def create_conversation(
    data: CreateConversationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Get existing or create new conversation"""
    provider = get_data_provider()
    result = await provider.chat.create_conversation(
        user_id=current_user["id"],
        data=ConversationCreateDTO(participant_ids=data.participant_ids),
    )
    return {"ok": True, **result}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete conversation"""
    provider = get_data_provider()
    success = await provider.chat.delete_conversation(
        user_id=current_user["id"],
        conversation_id=conversation_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"ok": True, "message": "Conversation deleted"}


# =============================================================================
# Message Endpoints
# =============================================================================


@router.get("/messages", response_model=List[MessageDTO])
async def list_messages(
    conversation_id: str = Query(...),
    before: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List messages in conversation, enriched with sender profiles."""
    provider = get_data_provider()
    messages = await provider.chat.list_messages(
        user_id=current_user["id"],
        conversation_id=conversation_id,
        before=before,
        limit=limit,
    )

    # Enrich with sender profile data (best-effort)
    if messages:
        try:
            sender_ids = list({m.sender_id for m in messages})
            profiles = await _get_user_profiles(provider, sender_ids)
            for msg in messages:
                profile = profiles.get(msg.sender_id)
                if profile:
                    msg.sender_name = profile.get("display_name") or profile.get("username")
                    msg.sender_avatar = profile.get("avatar_url")
        except Exception:
            pass  # Return messages without profile enrichment

    return messages


@router.post("/messages", response_model=MessageDTO)
async def send_message(
    data: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
):
    """Send message"""
    provider = get_data_provider()

    # Collaboration persistence (collab_* conversations) is written by the
    # session host's backend on behalf of guests, so honor the explicit author
    # and participant set. The caller is already authenticated; sender_id is a
    # trusted hint for attribution, never used to impersonate a 1:1 DM.
    is_collab = data.conversation_id.startswith("collab_")
    sender_id = data.sender_id if is_collab else None
    room_participants = data.participants if is_collab else None
    author_id = sender_id or current_user["id"]

    try:
        result = await provider.chat.send_message(
            user_id=current_user["id"],
            data=MessageCreateDTO(
                conversation_id=data.conversation_id,
                message_type=data.message_type,
                content=data.content,
                attachment_url=data.attachment_url,
                attachment_name=data.attachment_name,
                attachment_size=data.attachment_size,
                order_id=data.order_id,
            ),
            sender_id=sender_id,
            room_participants=room_participants,
        )
        # Enrich with sender profile (best-effort, don't fail the message send)
        try:
            profiles = await _get_user_profiles(provider, [author_id])
            profile = profiles.get(author_id, {})
            result.sender_name = profile.get("display_name") or current_user.get("display_name")
            result.sender_avatar = profile.get("avatar_url") or current_user.get("avatar_url")
        except Exception:
            result.sender_name = current_user.get("display_name")
            result.sender_avatar = current_user.get("avatar_url")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/conversations/{conversation_id}/read")
async def mark_as_read(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark all messages in conversation as read"""
    provider = get_data_provider()
    success = await provider.chat.mark_as_read(
        user_id=current_user["id"],
        conversation_id=conversation_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"ok": True, "message": "Messages marked as read"}


@router.delete("/messages/{conversation_id}/{message_id}")
async def delete_message(
    conversation_id: str,
    message_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a message. Only the sender can delete their own messages."""
    provider = get_data_provider()
    success = await provider.chat.delete_message(
        user_id=current_user["id"],
        conversation_id=conversation_id,
        message_id=message_id,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Message not found or you don't have permission to delete it",
        )

    return {"ok": True, "message": "Message deleted"}


# File Upload — see chat_upload.py (registered separately, needs multipart form support)
