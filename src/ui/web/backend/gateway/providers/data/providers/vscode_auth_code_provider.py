"""VSCode auth-code provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class VscodeAuthCodeProvider(ABC):
    """Provider interface for one-time VSCode extension auth codes."""

    @abstractmethod
    def create_code(
        self,
        user_data: dict,
        token: str,
        refresh_token: Optional[str],
        ttl_seconds: int,
    ) -> str:
        """Create a one-time auth code and return it."""
        pass

    @abstractmethod
    def consume_code(self, code: str) -> Optional[dict]:
        """Consume a one-time auth code, returning its payload when valid."""
        pass
