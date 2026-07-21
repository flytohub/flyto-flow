"""Breakpoint persistence provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class BreakpointRecord:
    """Provider-neutral persisted breakpoint state."""

    breakpoint_id: str
    execution_id: str
    step_id: str
    workflow_id: Optional[str] = None
    title: str = "Approval Required"
    description: str = ""
    required_approvers: list[str] = field(default_factory=list)
    approval_mode: str = "single"
    timeout_seconds: Optional[int] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    context_snapshot: dict[str, Any] = field(default_factory=dict)
    custom_fields: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    resolved_at: Optional[datetime] = None


@dataclass
class BreakpointResponseRecord:
    """Provider-neutral persisted approval response."""

    breakpoint_id: str
    approved: bool
    user_id: str
    comment: Optional[str] = None
    custom_inputs: dict[str, Any] = field(default_factory=dict)
    responded_at: Optional[datetime] = None


class DuplicateBreakpointResponseError(ValueError):
    """Raised when the same user responds to a breakpoint more than once."""


class BreakpointProvider(ABC):
    """Persistence contract for durable breakpoint state."""

    @abstractmethod
    async def save(self, record: BreakpointRecord) -> None:
        """Persist a new breakpoint record."""

    @abstractmethod
    async def get(self, breakpoint_id: str) -> Optional[BreakpointRecord]:
        """Return a breakpoint record when it exists."""

    @abstractmethod
    async def list_pending(
        self,
        execution_id: Optional[str] = None,
    ) -> list[BreakpointRecord]:
        """List pending breakpoints, optionally for one execution."""

    @abstractmethod
    async def update_status(
        self,
        breakpoint_id: str,
        status: str,
        resolved_at: datetime,
    ) -> None:
        """Persist a terminal breakpoint status."""

    @abstractmethod
    async def create_response(self, response: BreakpointResponseRecord) -> None:
        """Create a response, rejecting duplicate users atomically."""

    @abstractmethod
    async def replace_response(self, response: BreakpointResponseRecord) -> None:
        """Create or replace a user's response."""

    @abstractmethod
    async def list_responses(
        self,
        breakpoint_id: str,
    ) -> list[BreakpointResponseRecord]:
        """List responses in response-time order."""

    @abstractmethod
    async def delete(self, breakpoint_id: str) -> None:
        """Delete a breakpoint and its responses."""
