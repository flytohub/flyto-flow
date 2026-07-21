"""
Collaboration Quota Provider Interface

Abstract interface for per-user collaboration usage minutes.
"""

from abc import ABC, abstractmethod


class CollaborationQuotaProvider(ABC):
    """Abstract collaboration quota provider."""

    @abstractmethod
    async def get_used_minutes(self, user_id: str, month_key: str) -> int:
        """Get collaboration minutes used by a user in a UTC month."""
        pass

    @abstractmethod
    async def add_minutes(
        self,
        user_id: str,
        minutes: int,
        month_key: str,
        updated_at: str,
    ) -> int:
        """Add collaboration minutes and return the new monthly total."""
        pass
