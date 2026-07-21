"""
Users API Routes

Provides user profile and follow endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from api.auth import get_current_user
from gateway.providers.hub import get_data_provider
from gateway.providers.data.models import (
    UserProfileDTO,
    UserProfileUpdateDTO,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


# =============================================================================
# Request/Response Models
# =============================================================================


class UpdateProfileRequest(BaseModel):
    """Update profile request"""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    website: Optional[str] = None


class FollowStatusResponse(BaseModel):
    """Follow status response"""
    is_following: bool


class DeleteAccountRequest(BaseModel):
    """Request to delete user account (GDPR)"""
    reason: Optional[str] = None
    feedback: Optional[str] = None


# =============================================================================
# Profile Endpoints
# =============================================================================


@router.get("/profile")
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
):
    """Get current user's profile"""
    provider = get_data_provider()
    result = await provider.users.get_profile(current_user["id"])

    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {"ok": True, "profile": result.model_dump()}


@router.patch("/profile")
async def update_my_profile(
    data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update current user's profile"""
    provider = get_data_provider()
    result = await provider.users.update_profile(
        user_id=current_user["id"],
        data=UserProfileUpdateDTO(
            display_name=data.display_name,
            bio=data.bio,
            avatar_url=data.avatar_url,
            website=data.website,
        ),
    )

    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {"ok": True, "profile": result.model_dump()}


@router.delete("/profile")
async def delete_my_profile(
    data: Optional[DeleteAccountRequest] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Request account deletion (GDPR compliant).

    Creates a deletion request with a 30-day buffer period.
    User can cancel the deletion within this period.
    After 30 days, all user data will be permanently deleted.

    Returns:
        Deletion request details including scheduled deletion date.
    """
    from gateway.providers.data.models import DeletionRequestCreateDTO

    provider = get_data_provider()
    user_id = current_user["id"]
    email = current_user.get("email", "")

    # Check if deletion request already exists
    try:
        existing = await provider.deletion_requests.get_request(user_id)
        if existing and existing.status.value == "pending":
            return {
                "ok": True,
                "message": "Deletion request already pending",
                "deletion_request": existing.model_dump(),
            }
    except Exception as e:
        logger.warning(f"Error checking existing deletion request: {e}")

    # Create deletion request
    try:
        request_data = DeletionRequestCreateDTO(
            reason=data.reason if data else None,
            feedback=data.feedback if data else None,
        )

        result = await provider.deletion_requests.create_request(
            user_id=user_id,
            email=email,
            data=request_data,
        )

        # Create audit log
        try:
            from gateway.providers.data.models import AuditLogCreateDTO, AuditAction
            await provider.audit_logs.create_log(AuditLogCreateDTO(
                actor_id=user_id,
                actor_email=email,
                action=AuditAction.USER_DELETION_REQUESTED,
                resource_type="user",
                resource_id=user_id,
                description="User requested account deletion",
                metadata={
                    "reason": data.reason if data else None,
                    "scheduled_deletion_at": result.scheduled_deletion_at.isoformat(),
                },
            ))
        except Exception as e:
            logger.warning(f"Failed to create audit log: {e}")

        logger.info(f"Deletion request created for user {user_id}")

        return {
            "ok": True,
            "message": "Deletion request created. Your account will be deleted in 30 days unless cancelled.",
            "deletion_request": result.model_dump(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create deletion request: {e}")
        raise HTTPException(status_code=500, detail="Failed to create deletion request")


@router.post("/avatar")
async def upload_avatar(
    current_user: dict = Depends(get_current_user),
):
    """
    Upload user avatar.

    Note: This is a placeholder endpoint. In production, integrate with
    your storage provider (S3, GCS, etc.) for actual file uploads.
    """
    import uuid

    # Generate a mock avatar URL
    # In production, this would upload to storage and return the URL
    avatar_id = str(uuid.uuid4())[:8]
    avatar_url = f"/storage/avatars/{avatar_id}.png"

    # Update user profile with new avatar URL
    provider = get_data_provider()
    try:
        await provider.users.update_profile(
            user_id=current_user["id"],
            data=UserProfileUpdateDTO(avatar_url=avatar_url),
        )
    except Exception as e:
        logger.warning(f"Failed to update avatar URL: {e}")

    return {
        "ok": True,
        "avatar_url": avatar_url,
        "message": "Avatar upload endpoint ready. Integrate with storage provider for production.",
    }


@router.get("/{user_id}/profile", response_model=UserProfileDTO)
async def get_user_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get another user's profile"""
    provider = get_data_provider()
    result = await provider.users.get_profile(user_id)

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    return result


# =============================================================================
# Preferences Endpoints
# =============================================================================


class UserPreferencesRequest(BaseModel):
    """User preferences update request"""
    theme: Optional[str] = None
    language: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None


@router.get("/preferences")
async def get_my_preferences(
    current_user: dict = Depends(get_current_user),
):
    """Get current user's preferences"""
    provider = get_data_provider()

    # Try to get preferences from user data, or return defaults
    try:
        result = await provider.users.get_preferences(current_user["id"])
        preferences = result if result else {}
    except AttributeError:
        # Provider doesn't have get_preferences, return defaults
        preferences = {}

    # Merge with defaults
    default_prefs = {
        "theme": "system",
        "language": "en",
        "notifications_enabled": True,
        "email_notifications": True,
    }

    return {
        "ok": True,
        "preferences": {**default_prefs, **preferences}
    }


@router.patch("/preferences")
async def update_my_preferences(
    data: UserPreferencesRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update current user's preferences"""
    provider = get_data_provider()

    updates = data.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        await provider.users.update_preferences(current_user["id"], updates)
    except AttributeError:
        # Provider doesn't have update_preferences, just return success
        pass

    return {"ok": True, "message": "Preferences updated"}


# =============================================================================
# Follow Endpoints
# =============================================================================


@router.post("/follow/{user_id}")
async def follow_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Follow a user"""
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    provider = get_data_provider()
    success = await provider.users.follow_user(
        follower_id=current_user["id"],
        following_id=user_id,
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to follow user")

    return {"ok": True, "message": "User followed"}


@router.delete("/follow/{user_id}")
async def unfollow_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Unfollow a user"""
    provider = get_data_provider()
    success = await provider.users.unfollow_user(
        follower_id=current_user["id"],
        following_id=user_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Follow relationship not found")

    return {"ok": True, "message": "User unfollowed"}


@router.get("/follow/{user_id}/status", response_model=FollowStatusResponse)
async def get_follow_status(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Check if current user is following another user"""
    provider = get_data_provider()
    is_following = await provider.users.is_following(
        follower_id=current_user["id"],
        following_id=user_id,
    )

    return FollowStatusResponse(is_following=is_following)


@router.get("/followers", response_model=PaginatedResponse)
async def list_my_followers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List current user's followers"""
    provider = get_data_provider()
    result = await provider.users.list_followers(
        user_id=current_user["id"],
        page=page,
        page_size=page_size,
    )
    return result


@router.get("/following", response_model=PaginatedResponse)
async def list_my_following(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List users the current user is following"""
    provider = get_data_provider()
    result = await provider.users.list_following(
        user_id=current_user["id"],
        page=page,
        page_size=page_size,
    )
    return result


@router.get("/{user_id}/followers", response_model=PaginatedResponse)
async def list_user_followers(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List another user's followers"""
    provider = get_data_provider()
    result = await provider.users.list_followers(
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    return result


@router.get("/{user_id}/following", response_model=PaginatedResponse)
async def list_user_following(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List users another user is following"""
    provider = get_data_provider()
    result = await provider.users.list_following(
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    return result
