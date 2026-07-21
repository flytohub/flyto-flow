"""
User Profile Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional

from gateway.providers.data.models import (
    UserProfileDTO,
    UserProfileUpdateDTO,
    PaginatedResponse,
)


class UserProfileProvider(ABC):
    """
    User profile data provider interface.

    Deployment-specific implementations may use hosted, enterprise, or local
    persistence without exposing that storage choice to callers.
    """

    @abstractmethod
    async def get_profile(
        self,
        user_id: str,
    ) -> Optional[UserProfileDTO]:
        """Get user profile."""
        pass

    @abstractmethod
    async def update_profile(
        self,
        user_id: str,
        data: UserProfileUpdateDTO,
    ) -> Optional[UserProfileDTO]:
        """Update user profile."""
        pass

    @abstractmethod
    async def follow_user(
        self,
        follower_id: str,
        following_id: str,
    ) -> bool:
        """Follow a user."""
        pass

    @abstractmethod
    async def unfollow_user(
        self,
        follower_id: str,
        following_id: str,
    ) -> bool:
        """Unfollow a user."""
        pass

    @abstractmethod
    async def list_followers(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List user's followers."""
        pass

    @abstractmethod
    async def list_following(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List users being followed."""
        pass

    @abstractmethod
    async def is_following(
        self,
        follower_id: str,
        following_id: str,
    ) -> bool:
        """Check if user is following another user."""
        pass
