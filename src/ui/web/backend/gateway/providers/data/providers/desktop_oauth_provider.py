"""Desktop OAuth provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class DesktopOAuthProvider(ABC):
    """Provider interface for desktop OAuth flow state persistence."""

    @abstractmethod
    def create_flow(self, provider: str) -> str:
        """Create a pending desktop OAuth flow and return its state token."""
        pass

    @abstractmethod
    def get_flow(self, state: str) -> Optional[dict]:
        """Return a desktop OAuth flow entry by state token."""
        pass

    @abstractmethod
    def complete_flow(self, state: str, result: dict) -> bool:
        """Mark a desktop OAuth flow complete."""
        pass
