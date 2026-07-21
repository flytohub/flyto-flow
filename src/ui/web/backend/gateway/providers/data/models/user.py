"""User Profile DTO Models"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserProfileDTO(BaseModel):
    """User profile"""
    id: str
    email: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None

    # Profile
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    website: Optional[str] = None

    # Stats
    followers_count: int = 0
    following_count: int = 0
    templates_count: int = 0

    # Status
    is_verified: bool = False
    is_creator: bool = False

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserProfileUpdateDTO(BaseModel):
    """DTO for updating user profile"""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    website: Optional[str] = None


class FollowDTO(BaseModel):
    """Follow relationship"""
    follower_id: str
    following_id: str
    created_at: datetime
