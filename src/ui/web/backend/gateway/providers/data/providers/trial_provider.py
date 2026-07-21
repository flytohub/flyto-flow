"""Cloud trial provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TrialProvider(ABC):
    """Provider interface for cloud trial user state."""

    @abstractmethod
    async def get_trial_user(self, user_id: str) -> Optional[dict]:
        """Return user subscription and cloud-trial fields."""
        pass

    @abstractmethod
    async def start_trial(self, user_id: str) -> str:
        """Set and return the cloud trial start timestamp."""
        pass
