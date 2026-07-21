"""AI insights provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class AIInsightsProvider(ABC):
    """Provider interface for AI insights settings and report persistence."""

    @abstractmethod
    def get_config(self) -> dict:
        """Return AI insights configuration."""
        pass

    @abstractmethod
    def update_config(self, settings: dict) -> None:
        """Update AI insights configuration fields."""
        pass

    @abstractmethod
    def load_user_config(self, user_id: str) -> dict:
        """Return one user's AI BYOK configuration."""
        pass

    @abstractmethod
    def save_user_config(self, user_id: str, config: dict) -> None:
        """Persist one user's AI BYOK configuration."""
        pass

    @abstractmethod
    def get_anthropic_api_key(self) -> str:
        """Return the configured Anthropic API key."""
        pass

    @abstractmethod
    def get_discord_webhook_url(self) -> Optional[str]:
        """Return the configured Discord webhook URL."""
        pass

    @abstractmethod
    def find_today_digest(self) -> Optional[dict]:
        """Return today's completed daily digest if one exists."""
        pass

    @abstractmethod
    def save_insight(self, insight: dict) -> None:
        """Persist an insight document."""
        pass

    @abstractmethod
    def list_insights(
        self,
        insight_type=None,
        limit: int = 20,
        offset: int = 0,
        include_dismissed: bool = False,
    ) -> dict:
        """List insights with optional filters and pagination."""
        pass

    @abstractmethod
    def get_insight(self, insight_id: str) -> Optional[dict]:
        """Return one insight by ID."""
        pass

    @abstractmethod
    def mark_read(self, insight_id: str) -> bool:
        """Mark an insight as read."""
        pass

    @abstractmethod
    def dismiss(self, insight_id: str) -> bool:
        """Dismiss an insight."""
        pass

    @abstractmethod
    def get_unread_count(self) -> int:
        """Return unread, non-dismissed insight count."""
        pass
