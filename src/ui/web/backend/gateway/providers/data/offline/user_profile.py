"""
Offline User Profile Provider

SQLite-backed user profile operations for offline/desktop mode.
Social features (follow/unfollow) are not available offline.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from gateway.providers.data.base import UserProfileProvider
from gateway.providers.data.models import (
    UserProfileDTO,
    UserProfileUpdateDTO,
    PaginatedResponse,
)
from gateway.storage.offline_db import get_offline_cursor

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso() -> str:
    return _utc_now().isoformat()


def _parse_dt(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class OfflineUserProfileProvider(UserProfileProvider):
    """Offline implementation — SQLite-backed user profiles."""

    async def get_profile(self, user_id: str) -> Optional[UserProfileDTO]:
        with get_offline_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
            )
            profile_row = cursor.fetchone()

        if not user_row:
            return None

        return UserProfileDTO(
            id=user_row["id"],
            email=user_row.get("email"),
            username=user_row.get("username"),
            display_name=user_row.get("display_name"),
            bio=profile_row.get("bio") if profile_row else None,
            avatar_url=user_row.get("avatar_url") or (profile_row.get("avatar_url") if profile_row else None),
            website=profile_row.get("website") if profile_row else None,
            followers_count=0,
            following_count=0,
            templates_count=0,
            is_verified=False,
            is_creator=False,
            created_at=_parse_dt(user_row.get("created_at")),
            updated_at=_parse_dt(
                (profile_row.get("updated_at") if profile_row else None)
                or user_row.get("updated_at")
            ),
        )

    async def update_profile(
        self,
        user_id: str,
        data: UserProfileUpdateDTO,
    ) -> Optional[UserProfileDTO]:
        now = _utc_iso()

        # Upsert into user_profiles table
        with get_offline_cursor() as cursor:
            cursor.execute(
                "SELECT user_id FROM user_profiles WHERE user_id = ?",
                (user_id,),
            )
            exists = cursor.fetchone() is not None

            if exists:
                sets: list[str] = []
                params: list = []
                if data.display_name is not None:
                    sets.append("display_name = ?")
                    params.append(data.display_name)
                    # Also update in users table
                    cursor.execute(
                        "UPDATE users SET display_name = ?, updated_at = ? WHERE id = ?",
                        (data.display_name, now, user_id),
                    )
                if data.bio is not None:
                    sets.append("bio = ?")
                    params.append(data.bio)
                if data.avatar_url is not None:
                    sets.append("avatar_url = ?")
                    params.append(data.avatar_url)
                if data.website is not None:
                    sets.append("website = ?")
                    params.append(data.website)

                if sets:
                    sets.append("updated_at = ?")
                    params.append(now)
                    params.append(user_id)
                    cursor.execute(
                        f"UPDATE user_profiles SET {', '.join(sets)} WHERE user_id = ?",
                        tuple(params),
                    )
            else:
                cursor.execute(
                    """
                    INSERT INTO user_profiles (user_id, bio, website, avatar_url, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        data.bio,
                        data.website,
                        data.avatar_url,
                        now,
                    ),
                )
                if data.display_name is not None:
                    cursor.execute(
                        "UPDATE users SET display_name = ?, updated_at = ? WHERE id = ?",
                        (data.display_name, now, user_id),
                    )

        return await self.get_profile(user_id)

    # ------------------------------------------------------------------
    # Social features — not available offline
    # ------------------------------------------------------------------

    async def follow_user(self, follower_id: str, following_id: str) -> bool:
        raise NotImplementedError(
            "Social features (follow) are not available in offline mode."
        )

    async def unfollow_user(self, follower_id: str, following_id: str) -> bool:
        raise NotImplementedError(
            "Social features (unfollow) are not available in offline mode."
        )

    async def list_followers(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse:
        return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)

    async def list_following(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse:
        return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)

    async def is_following(self, follower_id: str, following_id: str) -> bool:
        return False
