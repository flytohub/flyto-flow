"""Feature usage provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class FeatureUsageProvider(ABC):
    """Provider interface for per-user feature usage counters."""

    @abstractmethod
    async def get_usage(self, user_id: str, feature_id: str, period_key: str) -> float:
        """Return current usage for a feature in a period."""
        pass

    @abstractmethod
    async def increment_usage(
        self,
        user_id: str,
        feature_id: str,
        period_key: str,
        amount: float,
        now_iso: str,
    ) -> float:
        """Increment feature usage atomically and return the new count."""
        pass
