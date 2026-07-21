"""
Collaboration Request Store

Encapsulates collaboration request persistence used by the collab-request
routes. Routes should call these helpers instead of touching provider details.
"""

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

async def get_template(template_id: str) -> Optional[Dict[str, Any]]:
    """Return template dict with 'id' key, or None if not found."""
    return await _request_provider().get_template(template_id)


def get_template_owner(template_data: Dict[str, Any]) -> Optional[str]:
    """Extract owner ID from template data."""
    return template_data.get("creator_id") or template_data.get("author_id")


async def add_collaboration_member(
    template_id: str,
    user_id: str,
    current_members: List[str],
) -> None:
    """Append *user_id* to the template's collaboration_members list."""
    await _request_provider().add_collaboration_member(
        template_id,
        user_id,
        current_members,
    )


# ---------------------------------------------------------------------------
# Request helpers
# ---------------------------------------------------------------------------

async def find_pending_request(
    template_id: str,
    requester_id: str,
) -> Optional[Dict[str, Any]]:
    """Return the first pending request for this user+template, or None."""
    return await _request_provider().find_pending_request(template_id, requester_id)


async def create_request(request_data: Dict[str, Any]) -> str:
    """Create a new collaboration request. Returns the new document ID."""
    return await _request_provider().create_request(request_data)


async def list_requests(
    template_id: str,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List collaboration requests for a template, optionally filtered by status."""
    return await _request_provider().list_requests(template_id, status)


async def get_latest_request(
    template_id: str,
    requester_id: str,
) -> Optional[Dict[str, Any]]:
    """Return the most recent request for a user+template, or None."""
    return await _request_provider().get_latest_request(template_id, requester_id)


async def get_request(request_id: str) -> Optional[Dict[str, Any]]:
    """Return a single collaboration request by ID, or None."""
    return await _request_provider().get_request(request_id)


async def resolve_request(request_id: str, status: str, resolved_by: str) -> None:
    """Mark a request as approved/rejected."""
    await _request_provider().resolve_request(request_id, status, resolved_by)


def _request_provider():
    from gateway.providers.hub import get_data_provider

    return get_data_provider().collaboration_requests
