"""
Breakpoint API Routes

Human-in-the-loop breakpoint management endpoints:
- List pending breakpoints
- Approve/reject breakpoints
- Get breakpoint details
- Cancel breakpoints
- Create breakpoints (cloud workers)
- Screenshot upload (cloud workers)
- Resolution result (cloud workers polling)
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/breakpoints", tags=["breakpoints"])


# --- Auth dependency for worker endpoints ---

async def _require_worker_or_user(request: Request):
    """Require authentication — mode-aware.

    Cloud Run (K_SERVICE set):
      - Workers: Authorization: Bearer worker:<api_key>
      - Users: Authorization: Bearer <firebase_token>
      - No token → 401

    Local/Desktop (no K_SERVICE):
      - sidecar_auth middleware already validated → trust it
      - Still attempt Firebase verification if Bearer token present (best-effort)
    """
    import os

    _is_cloud_run = bool(os.environ.get("K_SERVICE"))
    auth = request.headers.get("authorization", "")

    # Worker auth (cloud workers only)
    if auth.startswith("Bearer worker:"):
        import hmac
        worker_key = os.environ.get("WORKER_API_KEY", "")
        if not worker_key:
            raise HTTPException(401, "Worker auth not configured")
        key = auth[len("Bearer worker:"):]
        if hmac.compare_digest(key, worker_key):
            return {"id": "cloud-worker", "role": "worker"}
        raise HTTPException(401, "Invalid worker API key")

    # Firebase auth
    if auth.startswith("Bearer ") and len(auth) > 20:
        try:
            from gateway.auth import get_current_user
            return await get_current_user(auth)
        except Exception:
            if _is_cloud_run:
                raise HTTPException(401, "Invalid or expired token")
            # Local mode: Cloud API might be unreachable, fall through

    # Local/Desktop mode: sidecar_auth middleware already validated the request.
    # No additional auth needed — the sidecar secret prevents unauthorized access.
    if not _is_cloud_run:
        return {"id": "local-user", "role": "user"}

    raise HTTPException(401, "Authentication required")


# =============================================================================
# Request/Response Models
# =============================================================================

class ApprovalRequest(BaseModel):
    """Request to approve or reject a breakpoint"""
    approved: bool = Field(..., description="Whether to approve or reject")
    user_id: Optional[str] = Field(
        None,
        description="Deprecated client-supplied user id; authenticated identity is authoritative",
    )
    comment: Optional[str] = Field(None, description="Optional comment")
    custom_inputs: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Values for custom input fields"
    )


class BreakpointResponse(BaseModel):
    """Breakpoint details response"""
    breakpoint_id: str
    execution_id: str
    step_id: str
    workflow_id: Optional[str]
    title: str
    description: str
    status: str
    required_approvers: List[str]
    approval_mode: str
    timeout_seconds: Optional[int]
    created_at: str
    expires_at: Optional[str]
    is_expired: bool
    custom_fields: List[Dict[str, Any]]
    context_snapshot: Dict[str, Any]
    responses: List[Dict[str, Any]] = Field(default_factory=list)


class BreakpointListResponse(BaseModel):
    """List of breakpoints response"""
    breakpoints: List[BreakpointResponse]
    total: int


class UpdateBreakpointStatusRequest(BaseModel):
    """Request to update breakpoint status"""
    status: str = Field("pending", description="New breakpoint status")


class ApprovalResultResponse(BaseModel):
    """Result of approval action"""
    breakpoint_id: str
    status: str
    approved: bool
    resolved_at: Optional[str]
    message: str


# =============================================================================
# Helper Functions
# =============================================================================

def _is_cloud_mode() -> bool:
    """Check if running as cloud control plane (not worker)."""
    from gateway.config import get_gateway_config
    return get_gateway_config().is_cloud


def _is_cloud_run() -> bool:
    import os

    return bool(os.environ.get("K_SERVICE"))


def _is_worker_auth(auth: dict | None) -> bool:
    return bool(auth and auth.get("role") == "worker")


def _is_local_fallback_auth(auth: dict | None) -> bool:
    return bool(auth and auth.get("id") == "local-user" and not _is_cloud_run())


def _auth_user_id(auth: dict | None) -> Optional[str]:
    if not auth:
        return None
    value = auth.get("id") or auth.get("uid") or auth.get("user_id")
    return str(value) if value else None


def _effective_approver_id(auth: dict | None, claimed_user_id: Optional[str] = None) -> Optional[str]:
    """Return the user id allowed to make user-facing breakpoint decisions."""
    if _is_worker_auth(auth):
        return claimed_user_id
    if _is_local_fallback_auth(auth):
        return claimed_user_id or _auth_user_id(auth)

    actual_user_id = _auth_user_id(auth)
    if not actual_user_id:
        raise HTTPException(401, "Authentication required")
    if claimed_user_id and claimed_user_id != actual_user_id:
        raise HTTPException(403, "Cannot act as a different breakpoint approver")
    return actual_user_id


def _require_cloud_worker(auth: dict | None) -> None:
    """Restrict worker-only endpoints in Cloud Run while keeping local sidecar mode usable."""
    if _is_worker_auth(auth) or _is_local_fallback_auth(auth):
        return
    raise HTTPException(403, "Worker authorization required")


def _ensure_user_can_access_breakpoint(request, auth: dict | None) -> Optional[str]:
    """Authorize user-facing access to a breakpoint by required approver membership."""
    if _is_worker_auth(auth) or _is_local_fallback_auth(auth):
        return _auth_user_id(auth)

    user_id = _effective_approver_id(auth)
    if not request.required_approvers or user_id not in request.required_approvers:
        raise HTTPException(403, "Breakpoint is not assigned to this user")
    return user_id


def get_manager():
    """Get breakpoint manager — cloud uses Firestore, local uses flyto-core."""
    if _is_cloud_mode():
        from services.cloud.breakpoint_manager import get_cloud_breakpoint_manager
        return get_cloud_breakpoint_manager()

    # Local/worker mode uses the installed flyto-core runtime package.
    try:
        from core.engine.breakpoints import get_breakpoint_manager
        return get_breakpoint_manager()
    except ImportError:
        logger.warning("Breakpoint manager unavailable; install flyto-core for local execution")

    logger.warning("Breakpoint manager not available - using stub implementation")
    return StubBreakpointManager()


class StubBreakpointManager:
    """Stub breakpoint manager for when flyto-core is not available"""

    async def list_pending(self, execution_id=None, user_id=None, include_unassigned=True):
        return []

    async def get_status(self, breakpoint_id):
        return None

    @property
    def store(self):
        return StubBreakpointStore()


class StubBreakpointStore:
    async def load(self, breakpoint_id):
        return None

    async def get_responses(self, breakpoint_id):
        return []

    async def delete(self, breakpoint_id):
        pass


async def request_to_response(
    request,
    include_responses: bool = False
) -> BreakpointResponse:
    """Convert BreakpointRequest to response model"""
    manager = get_manager()

    responses = []
    if include_responses:
        raw_responses = await manager.store.get_responses(request.breakpoint_id)
        responses = [r.to_dict() for r in raw_responses]

    return BreakpointResponse(
        breakpoint_id=request.breakpoint_id,
        execution_id=request.execution_id,
        step_id=request.step_id,
        workflow_id=request.workflow_id,
        title=request.title,
        description=request.description,
        status="pending",
        required_approvers=request.required_approvers,
        approval_mode=request.approval_mode.value,
        timeout_seconds=request.timeout_seconds,
        created_at=request.created_at.isoformat(),
        expires_at=request.expires_at.isoformat() if request.expires_at else None,
        is_expired=request.is_expired,
        custom_fields=request.custom_fields,
        context_snapshot=request.context_snapshot,
        responses=responses,
    )


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("/pending", response_model=BreakpointListResponse)
async def list_pending_breakpoints(
    execution_id: Optional[str] = Query(None, description="Filter by execution ID"),
    user_id: Optional[str] = Query(None, description="Filter by authorized approver"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    _auth=Depends(_require_worker_or_user),
):
    """
    List all pending breakpoints.

    Optionally filter by execution ID or user authorization.
    """
    manager = get_manager()
    effective_user_id = user_id
    include_unassigned = True
    if not _is_worker_auth(_auth):
        effective_user_id = _effective_approver_id(_auth, user_id)
        include_unassigned = _is_local_fallback_auth(_auth)

    pending = await manager.list_pending(
        execution_id=execution_id,
        user_id=effective_user_id,
        include_unassigned=include_unassigned,
    )

    # Apply pagination
    total = len(pending)
    pending = pending[offset:offset + limit]

    breakpoints = [
        await request_to_response(req)
        for req in pending
    ]

    return BreakpointListResponse(
        breakpoints=breakpoints,
        total=total,
    )


@router.get("/{breakpoint_id}", response_model=BreakpointResponse)
async def get_breakpoint(breakpoint_id: str, _auth=Depends(_require_worker_or_user)):
    """
    Get details of a specific breakpoint.

    Includes all responses if any have been submitted.
    """
    manager = get_manager()

    request = await manager.store.load(breakpoint_id)
    if not request:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")
    _ensure_user_can_access_breakpoint(request, _auth)

    return await request_to_response(request, include_responses=True)


@router.post("/{breakpoint_id}/respond", response_model=ApprovalResultResponse)
async def respond_to_breakpoint(
    breakpoint_id: str,
    approval: ApprovalRequest,
    _auth=Depends(_require_worker_or_user),
):
    """
    Approve or reject a breakpoint.

    The breakpoint may not be immediately resolved if it requires
    multiple approvals (all/majority mode).
    """
    manager = get_manager()

    request = await manager.store.load(breakpoint_id)
    if not request:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")

    if request.is_expired:
        raise HTTPException(400, "Breakpoint has expired")
    user_id = _effective_approver_id(_auth, approval.user_id)
    if not _is_worker_auth(_auth):
        _ensure_user_can_access_breakpoint(request, _auth)

    try:
        result = await manager.respond(
            breakpoint_id=breakpoint_id,
            approved=approval.approved,
            user_id=user_id,
            comment=approval.comment,
            custom_inputs=approval.custom_inputs or {},
        )

        if result:
            return ApprovalResultResponse(
                breakpoint_id=breakpoint_id,
                status=result.status.value,
                approved=result.approved,
                resolved_at=result.resolved_at.isoformat(),
                message=f"Breakpoint {result.status.value}",
            )
        else:
            return ApprovalResultResponse(
                breakpoint_id=breakpoint_id,
                status="pending",
                approved=False,
                resolved_at=None,
                message="Response recorded, waiting for more approvals",
            )

    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{breakpoint_id}/approve", response_model=ApprovalResultResponse)
async def approve_breakpoint(
    breakpoint_id: str,
    user_id: Optional[str] = Query(None, description="Deprecated user id; auth token is authoritative"),
    comment: Optional[str] = Query(None, description="Optional comment"),
    _auth=Depends(_require_worker_or_user),
):
    """
    Shorthand to approve a breakpoint.
    """
    return await respond_to_breakpoint(
        breakpoint_id,
        ApprovalRequest(
            approved=True,
            user_id=user_id,
            comment=comment,
        ),
        _auth=_auth,
    )


@router.post("/{breakpoint_id}/reject", response_model=ApprovalResultResponse)
async def reject_breakpoint(
    breakpoint_id: str,
    user_id: Optional[str] = Query(None, description="Deprecated user id; auth token is authoritative"),
    comment: Optional[str] = Query(None, description="Optional comment"),
    _auth=Depends(_require_worker_or_user),
):
    """
    Shorthand to reject a breakpoint.
    """
    return await respond_to_breakpoint(
        breakpoint_id,
        ApprovalRequest(
            approved=False,
            user_id=user_id,
            comment=comment,
        ),
        _auth=_auth,
    )


@router.post("/{breakpoint_id}/cancel", response_model=ApprovalResultResponse)
async def cancel_breakpoint(breakpoint_id: str, _auth=Depends(_require_worker_or_user)):
    """
    Cancel a pending breakpoint.

    The breakpoint will be resolved with 'cancelled' status.
    """
    manager = get_manager()

    request = await manager.store.load(breakpoint_id)
    if not request:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")
    _ensure_user_can_access_breakpoint(request, _auth)

    result = await manager.cancel(breakpoint_id)

    return ApprovalResultResponse(
        breakpoint_id=breakpoint_id,
        status=result.status.value,
        approved=False,
        resolved_at=result.resolved_at.isoformat(),
        message="Breakpoint cancelled",
    )


@router.get("/{breakpoint_id}/status")
async def get_breakpoint_status(breakpoint_id: str, _auth=Depends(_require_worker_or_user)):
    """
    Get the current status of a breakpoint.

    Lightweight endpoint for polling.
    """
    manager = get_manager()
    request = await manager.store.load(breakpoint_id)
    if not request:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")
    _ensure_user_can_access_breakpoint(request, _auth)

    status = await manager.get_status(breakpoint_id)
    if status is None:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")

    return {
        "ok": True,
        "breakpoint_id": breakpoint_id,
        "status": status.value,
        "is_resolved": status.value != "pending",
    }


@router.get("/execution/{execution_id}", response_model=BreakpointListResponse)
async def get_execution_breakpoints(
    execution_id: str,
    include_resolved: bool = Query(False, description="Include resolved breakpoints"),
    _auth=Depends(_require_worker_or_user),
):
    """
    Get all breakpoints for a specific execution.
    """
    manager = get_manager()
    include_unassigned = _is_worker_auth(_auth) or _is_local_fallback_auth(_auth)
    effective_user_id = None if _is_worker_auth(_auth) else _effective_approver_id(_auth)

    if include_resolved:
        # For now, we only support pending breakpoints in the store
        # A full implementation would need historical storage
        pending = await manager.list_pending(
            execution_id=execution_id,
            user_id=effective_user_id,
            include_unassigned=include_unassigned,
        )
    else:
        pending = await manager.list_pending(
            execution_id=execution_id,
            user_id=effective_user_id,
            include_unassigned=include_unassigned,
        )

    breakpoints = [
        await request_to_response(req, include_responses=True)
        for req in pending
    ]

    return BreakpointListResponse(
        breakpoints=breakpoints,
        total=len(breakpoints),
    )


@router.delete("/{breakpoint_id}")
async def delete_breakpoint(breakpoint_id: str, _auth=Depends(_require_worker_or_user)):
    """
    Delete a breakpoint and all its data.

    Use with caution - this permanently removes the breakpoint.
    """
    _require_cloud_worker(_auth)
    manager = get_manager()

    request = await manager.store.load(breakpoint_id)
    if not request:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")

    await manager.store.delete(breakpoint_id)

    return {
        "ok": True,
        "breakpoint_id": breakpoint_id,
        "deleted": True,
        "message": "Breakpoint deleted successfully",
    }


# =============================================================================
# Cloud Worker Endpoints
# These are used by cloud workers to create breakpoints and wait for resolution.
# =============================================================================

class CreateBreakpointRequest(BaseModel):
    """Request from cloud worker to create a breakpoint"""
    breakpoint_id: str
    execution_id: str
    step_id: str
    workflow_id: Optional[str] = None
    title: str = "Approval Required"
    description: str = ""
    required_approvers: List[str] = Field(default_factory=list)
    approval_mode: str = "single"
    timeout_seconds: Optional[int] = None
    context_snapshot: Dict[str, Any] = Field(default_factory=dict)
    custom_fields: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("/create", response_model=BreakpointResponse)
async def create_breakpoint_from_worker(
    req: CreateBreakpointRequest,
    _auth=Depends(_require_worker_or_user),
):
    """
    Create a breakpoint from a cloud worker.

    Workers POST here instead of using in-memory breakpoint creation.
    The control plane stores the breakpoint and notifies connected frontends.
    """
    _require_cloud_worker(_auth)
    manager = get_manager()

    # Import ApprovalMode from cloud models (no flyto-core dependency)
    from services.cloud.breakpoint_models import ApprovalMode

    request = await manager.create_breakpoint(
        execution_id=req.execution_id,
        step_id=req.step_id,
        title=req.title,
        description=req.description,
        workflow_id=req.workflow_id,
        required_approvers=req.required_approvers,
        approval_mode=ApprovalMode(req.approval_mode),
        timeout_seconds=req.timeout_seconds,
        context_snapshot=req.context_snapshot,
        custom_fields=req.custom_fields,
        metadata=req.metadata,
    )

    # Override the auto-generated ID with the worker's ID
    if req.breakpoint_id and req.breakpoint_id != request.breakpoint_id:
        old_id = request.breakpoint_id
        request.breakpoint_id = req.breakpoint_id
        await manager.store.save(request)
        await manager.store.delete(old_id)
        # In-process events only exist for local/worker mode
        if hasattr(manager, '_resolution_events'):
            import asyncio
            manager._resolution_events[req.breakpoint_id] = manager._resolution_events.pop(old_id, None) or asyncio.Event()

    # Push to WebSocket clients (local mode only, cloud uses Firestore notifier)
    try:
        from services.breakpoint_notifier import WebSocketBreakpointNotifier
        notifier = WebSocketBreakpointNotifier()
        await notifier.notify_pending(request)
    except Exception as e:
        logger.debug("WS notify failed: %s", e)

    return await request_to_response(request)


@router.patch("/{breakpoint_id}/status")
async def update_breakpoint_status(
    breakpoint_id: str,
    body: UpdateBreakpointStatusRequest,
    _auth=Depends(_require_worker_or_user),
):
    """
    Update breakpoint status (used by cloud workers).
    """
    _require_cloud_worker(_auth)
    manager = get_manager()

    request = await manager.store.load(breakpoint_id)
    if not request:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")

    from services.cloud.breakpoint_models import BreakpointStatus as BS

    status = BS(body.status)
    await manager.store.update_status(breakpoint_id, status)

    return {"ok": True, "breakpoint_id": breakpoint_id, "status": status.value}


@router.get("/{breakpoint_id}/result")
async def get_breakpoint_result(
    breakpoint_id: str,
    _auth=Depends(_require_worker_or_user),
):
    """
    Get the resolution result of a breakpoint.

    Cloud workers poll this after creating a breakpoint to get
    the user's response (action, selector, value for interact).
    """
    _require_cloud_worker(_auth)
    manager = get_manager()

    # Check in-memory cache first (same-instance resolution)
    result = manager._results.get(breakpoint_id)
    if result:
        return result.to_dict()

    # Check Firestore for cross-instance resolution (Cloud Run has multiple instances).
    # Another instance may have resolved this breakpoint while this one has an empty _results cache.
    if hasattr(manager.store, 'get_resolved_result'):
        resolved = await manager.store.get_resolved_result(breakpoint_id)
        if resolved:
            return resolved.to_dict()

    # Check if request exists and is still pending
    request = await manager.store.load(breakpoint_id)
    if not request:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")

    if request.is_expired:
        from services.cloud.breakpoint_models import BreakpointStatus
        result = await manager._resolve(breakpoint_id, BreakpointStatus.TIMEOUT)
        return result.to_dict()

    return {
        "ok": True,
        "breakpoint_id": breakpoint_id,
        "status": "pending",
        "is_resolved": False,
    }


@router.post("/{breakpoint_id}/screenshot")
async def upload_breakpoint_screenshot(
    breakpoint_id: str,
    request: Request,
    _auth=Depends(_require_worker_or_user),
):
    """
    Upload a screenshot for a breakpoint.

    Cloud workers POST raw JPEG/PNG bytes here.
    Returns the URL where the screenshot can be accessed.
    """
    _require_cloud_worker(_auth)
    body = await request.body()
    if not body:
        raise HTTPException(400, "No screenshot data")

    content_type = request.headers.get("content-type", "image/jpeg")
    ext = "jpg" if "jpeg" in content_type else "png"

    # Save to screenshots directory
    screenshots_dir = Path.home() / ".flyto" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{breakpoint_id}.{ext}"
    filepath = screenshots_dir / filename
    filepath.write_bytes(body)

    url = f"/api/screenshots/{filename}"

    # Update the breakpoint's context_snapshot with the URL
    manager = get_manager()
    bp_request = await manager.store.load(breakpoint_id)
    if bp_request and bp_request.context_snapshot:
        bp_request.context_snapshot["screenshot_url"] = url
        bp_request.context_snapshot.pop("screenshot_base64", None)
        await manager.store.save(bp_request)

    logger.debug("Screenshot saved for %s: %s (%d bytes)", breakpoint_id, filepath, len(body))

    return {"ok": True, "url": url, "size": len(body)}
