"""Local human-checkpoint API for CE workflow executions."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


router = APIRouter(prefix="/breakpoints", tags=["breakpoints"])
LOCAL_ACTOR_ID = "local-workspace"


class ApprovalRequest(BaseModel):
    approved: bool
    comment: Optional[str] = None
    custom_inputs: Dict[str, Any] = Field(default_factory=dict)


class BreakpointResponse(BaseModel):
    breakpoint_id: str
    execution_id: str
    step_id: str
    workflow_id: Optional[str] = None
    title: str
    description: str
    status: str
    timeout_seconds: Optional[int] = None
    created_at: str
    expires_at: Optional[str] = None
    is_expired: bool
    custom_fields: List[Dict[str, Any]] = Field(default_factory=list)
    context_snapshot: Dict[str, Any] = Field(default_factory=dict)
    responses: List[Dict[str, Any]] = Field(default_factory=list)


class BreakpointListResponse(BaseModel):
    breakpoints: List[BreakpointResponse]
    total: int


class ApprovalResultResponse(BaseModel):
    breakpoint_id: str
    status: str
    approved: bool
    resolved_at: Optional[str]
    message: str


def get_manager():
    """Return the in-process manager bundled with flyto-core."""
    try:
        from core.engine.breakpoints import get_breakpoint_manager

        return get_breakpoint_manager()
    except (ImportError, RuntimeError) as exc:
        raise HTTPException(503, "The bundled breakpoint runtime is unavailable") from exc


async def request_to_response(request, include_responses: bool = False) -> BreakpointResponse:
    responses: List[Dict[str, Any]] = []
    if include_responses:
        raw_responses = await get_manager().store.get_responses(request.breakpoint_id)
        responses = [item.to_dict() for item in raw_responses]

    status = getattr(request, "status", "pending")
    if hasattr(status, "value"):
        status = status.value
    return BreakpointResponse(
        breakpoint_id=request.breakpoint_id,
        execution_id=request.execution_id,
        step_id=request.step_id,
        workflow_id=getattr(request, "workflow_id", None),
        title=request.title,
        description=request.description,
        status=str(status),
        timeout_seconds=getattr(request, "timeout_seconds", None),
        created_at=request.created_at.isoformat(),
        expires_at=request.expires_at.isoformat() if request.expires_at else None,
        is_expired=request.is_expired,
        custom_fields=getattr(request, "custom_fields", []),
        context_snapshot=getattr(request, "context_snapshot", {}),
        responses=responses,
    )


async def _pending(execution_id: Optional[str] = None):
    manager = get_manager()
    try:
        return await manager.list_pending(execution_id=execution_id, include_unassigned=True)
    except TypeError:
        return await manager.list_pending(execution_id=execution_id)


@router.get("/pending", response_model=BreakpointListResponse)
async def list_pending_breakpoints(
    execution_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    pending = await _pending(execution_id)
    total = len(pending)
    items = [await request_to_response(item) for item in pending[offset : offset + limit]]
    return BreakpointListResponse(breakpoints=items, total=total)


@router.get("/execution/{execution_id}", response_model=BreakpointListResponse)
async def get_execution_breakpoints(execution_id: str):
    pending = await _pending(execution_id)
    items = [await request_to_response(item, include_responses=True) for item in pending]
    return BreakpointListResponse(breakpoints=items, total=len(items))


@router.get("/{breakpoint_id}", response_model=BreakpointResponse)
async def get_breakpoint(breakpoint_id: str):
    request = await get_manager().store.load(breakpoint_id)
    if not request:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")
    return await request_to_response(request, include_responses=True)


@router.post("/{breakpoint_id}/respond", response_model=ApprovalResultResponse)
async def respond_to_breakpoint(breakpoint_id: str, approval: ApprovalRequest):
    manager = get_manager()
    request = await manager.store.load(breakpoint_id)
    if not request:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")
    if request.is_expired:
        raise HTTPException(400, "Breakpoint has expired")
    try:
        result = await manager.respond(
            breakpoint_id=breakpoint_id,
            approved=approval.approved,
            workspace_id=LOCAL_ACTOR_ID,
            comment=approval.comment,
            custom_inputs=approval.custom_inputs,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if result is None:
        return ApprovalResultResponse(
            breakpoint_id=breakpoint_id,
            status="pending",
            approved=False,
            resolved_at=None,
            message="Response recorded",
        )
    return ApprovalResultResponse(
        breakpoint_id=breakpoint_id,
        status=result.status.value,
        approved=result.approved,
        resolved_at=result.resolved_at.isoformat(),
        message=f"Breakpoint {result.status.value}",
    )


@router.post("/{breakpoint_id}/approve", response_model=ApprovalResultResponse)
async def approve_breakpoint(breakpoint_id: str, comment: Optional[str] = Query(None)):
    return await respond_to_breakpoint(
        breakpoint_id,
        ApprovalRequest(approved=True, comment=comment),
    )


@router.post("/{breakpoint_id}/reject", response_model=ApprovalResultResponse)
async def reject_breakpoint(breakpoint_id: str, comment: Optional[str] = Query(None)):
    return await respond_to_breakpoint(
        breakpoint_id,
        ApprovalRequest(approved=False, comment=comment),
    )


@router.post("/{breakpoint_id}/cancel", response_model=ApprovalResultResponse)
async def cancel_breakpoint(breakpoint_id: str):
    manager = get_manager()
    request = await manager.store.load(breakpoint_id)
    if not request:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")
    result = await manager.cancel(breakpoint_id)
    return ApprovalResultResponse(
        breakpoint_id=breakpoint_id,
        status=result.status.value,
        approved=False,
        resolved_at=result.resolved_at.isoformat(),
        message="Breakpoint cancelled",
    )


@router.get("/{breakpoint_id}/status")
async def get_breakpoint_status(breakpoint_id: str):
    status = await get_manager().get_status(breakpoint_id)
    if status is None:
        raise HTTPException(404, f"Breakpoint not found: {breakpoint_id}")
    return {
        "ok": True,
        "breakpoint_id": breakpoint_id,
        "status": status.value,
        "is_resolved": status.value != "pending",
    }
