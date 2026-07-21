"""
Local Collaboration REST Endpoints

REST endpoints for local collaboration session management.
These need the in-memory room manager (WebSocket-based), so they
live in the local runner rather than the cloud routes.

Extracted from main_local.py.
"""

from fastapi import APIRouter


def create_collaboration_local_router() -> APIRouter:
    """Create the local collaboration router."""
    r = APIRouter(prefix="/api/collaboration", tags=["collaboration-local"])

    @r.get("/session/{workflow_id}/info")
    async def collaboration_session_info(workflow_id: str):
        """Get info about an active local collaboration session."""
        from websocket.collaboration import collaboration_manager
        room = collaboration_manager.rooms.get(workflow_id)
        if not room:
            return {"active": False, "participant_count": 0, "participants": []}
        return {
            "active": True,
            "participant_count": len(room.presence),
            "participants": [
                {
                    "user_id": p.user_id,
                    "display_name": p.user_name,
                    "user_avatar": p.user_avatar,
                    "presence": "active",
                    "color": p.color,
                }
                for p in room.presence.values()
            ],
        }

    @r.post("/{workflow_id}/terminate")
    async def collaboration_terminate(workflow_id: str):
        """Terminate a local collaboration session (broadcasts to all participants)."""
        from websocket.collaboration import collaboration_manager
        room = collaboration_manager.rooms.get(workflow_id)
        if not room:
            return {"ok": True, "message": "No active session"}
        await collaboration_manager.terminate_room(workflow_id, "The owner ended the collaboration session.")
        return {"ok": True}

    return r
