"""Collaboration data provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Optional


class CollaborationError(Exception):
    """Base collaboration provider error."""


class CollaborationTemplateNotFoundError(CollaborationError):
    """Raised when a workflow/template cannot be found."""


class CollaborationPermissionError(CollaborationError):
    """Raised when a user cannot perform a collaboration operation."""


class CollaborationInviteCodeExhaustedError(CollaborationError):
    """Raised when a unique invite code cannot be generated."""


class CollaborationProvider(ABC):
    """Provider interface for collaboration invite and membership data."""

    @abstractmethod
    async def get_or_create_invite_code(
        self,
        *,
        workflow_id: str,
        owner_id: str,
        code_factory: Callable[[], str],
        max_attempts: int = 10,
    ) -> str:
        """Return an existing raw invite code or create a new one."""
        pass

    @abstractmethod
    async def regenerate_invite_code(
        self,
        *,
        workflow_id: str,
        owner_id: str,
        code_factory: Callable[[], str],
        max_attempts: int = 10,
    ) -> str:
        """Revoke existing invite codes and create a new raw invite code."""
        pass

    @abstractmethod
    async def resolve_invite_code(self, raw_code: str) -> Optional[dict[str, Any]]:
        """Resolve an invite code to workflow metadata, if it exists."""
        pass

    @abstractmethod
    async def join_by_invite_code(self, *, raw_code: str, user_id: str) -> Optional[dict[str, Any]]:
        """Add a user to collaboration members via invite code."""
        pass

    @abstractmethod
    async def get_members(self, workflow_id: str) -> Optional[dict[str, Any]]:
        """Return collaboration members and owner metadata for a workflow."""
        pass

    @abstractmethod
    async def remove_member(
        self,
        *,
        workflow_id: str,
        owner_id: str,
        member_id: str,
    ) -> bool:
        """Remove a collaboration member. Returns whether a member was removed."""
        pass

    @abstractmethod
    async def get_owner_id(self, workflow_id: str) -> Optional[str]:
        """Return the workflow owner id."""
        pass

    @abstractmethod
    async def get_websocket_user_context(self, user_id: str) -> Optional[dict[str, Any]]:
        """Return user display and subscription context for collaboration websockets."""
        pass
