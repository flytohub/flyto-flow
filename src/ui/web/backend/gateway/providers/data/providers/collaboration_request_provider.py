"""
Collaboration Request Provider Interface

Abstract interface for collaboration access requests on templates.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class CollaborationRequestProvider(ABC):
    """Abstract collaboration request provider."""

    @abstractmethod
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Return template data with an id field."""
        pass

    @abstractmethod
    async def add_collaboration_member(
        self,
        template_id: str,
        user_id: str,
        current_members: List[str],
    ) -> None:
        """Append a user to template collaboration members."""
        pass

    @abstractmethod
    async def find_pending_request(
        self,
        template_id: str,
        requester_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Find a pending request for template and requester."""
        pass

    @abstractmethod
    async def create_request(self, request_data: Dict[str, Any]) -> str:
        """Create a collaboration request and return its id."""
        pass

    @abstractmethod
    async def list_requests(
        self,
        template_id: str,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List collaboration requests for a template."""
        pass

    @abstractmethod
    async def get_latest_request(
        self,
        template_id: str,
        requester_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Return most recent collaboration request for a user and template."""
        pass

    @abstractmethod
    async def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Return a collaboration request by id."""
        pass

    @abstractmethod
    async def resolve_request(
        self,
        request_id: str,
        status: str,
        resolved_by: str,
    ) -> None:
        """Mark a collaboration request approved or rejected."""
        pass
