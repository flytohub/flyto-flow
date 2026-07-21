"""Webhook Provider Interface"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class WebhookProvider(ABC):
    """
    Webhook data provider interface.

    Implementations may use hosted or self-managed persistence without exposing
    that storage choice to callers.
    """

    @abstractmethod
    async def create(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a webhook. Returns created webhook dict with generated ID + secret."""
        ...

    @abstractmethod
    async def get(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook by ID."""
        ...

    @abstractmethod
    async def list_webhooks(self, user_id: str, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List webhooks for a user, optionally filtered by workflow_id."""
        ...

    @abstractmethod
    async def update(self, webhook_id: str, **kwargs) -> bool:
        """Update webhook fields."""
        ...

    @abstractmethod
    async def delete(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        ...

    @abstractmethod
    async def regenerate_secret(self, webhook_id: str) -> Optional[str]:
        """Generate new secret for webhook. Returns new secret."""
        ...

    @abstractmethod
    async def record_trigger(self, webhook_id: str) -> None:
        """Increment trigger count and update last_triggered_at."""
        ...

    async def import_legacy(
        self,
        webhook_id: str,
        webhook_data: Dict[str, Any],
        dry_run: bool = False,
    ) -> bool:
        """Import one legacy webhook if the provider supports store migration."""
        raise NotImplementedError("Legacy webhook import is not supported by this provider")

    @abstractmethod
    async def check_nonce(self, nonce: str) -> bool:
        """Check if nonce was already used (replay prevention). Returns True if exists."""
        ...

    @abstractmethod
    async def store_nonce(self, nonce: str, webhook_id: str, ttl_seconds: int = 600) -> None:
        """Store nonce with TTL for replay prevention."""
        ...

    async def cleanup_expired_nonces(self, limit: int = 500) -> int:
        """Clean up expired nonce records. Defaults to no-op for non-SaaS providers."""
        return 0
