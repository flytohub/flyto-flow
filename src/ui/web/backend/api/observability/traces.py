"""
Traces API

REST endpoints for distributed tracing.

NOTE: This is an Enterprise-only feature (Phase 8).
Requires OBSERVABILITY_TRACING capability.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.auth import get_current_user
from capabilities import Feature, require_any_feature
from gateway.storage.trace_repo import TraceRepository, TraceQuery, TraceSummary
from api.responses import to_camel_case

logger = logging.getLogger(__name__)

# Public router kept only for backward-compatible imports.
# NOTE: The stub GET /traces/ and /traces/search handlers were REMOVED. When
# mounted before the real (feature-gated) router they shadowed the real handlers
# (FastAPI serves the first route registered for an identical path), so the trace
# list and search were permanently empty — and because no traceId could ever be
# obtained, the working detail routes were unreachable. The real router below now
# serves those paths.
public_router = APIRouter(prefix="/traces", tags=["traces"])


# Feature-gated router for full functionality
router = APIRouter(
    prefix="/traces",
    tags=["traces"],
    dependencies=[Depends(require_any_feature(
        Feature.LOCAL_TRACING,
        Feature.HOSTED_OBSERVABILITY,
    ))],
)


# =============================================================================
# Response Models
# =============================================================================

class SpanEventResponse(BaseModel):
    """Response model for a span event."""

    name: str
    timestamp: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class SpanResponse(BaseModel):
    """Response model for a span."""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: str
    end_time: Optional[str]
    duration_ms: Optional[int]
    status: str
    status_message: Optional[str]
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[SpanEventResponse] = Field(default_factory=list)


class TraceSummaryResponse(BaseModel):
    """Response model for trace summary."""

    trace_id: str
    root_operation: str
    service_name: str
    start_time: str
    end_time: Optional[str]
    duration_ms: Optional[int]
    span_count: int
    error_count: int
    status: str


class TraceDetailResponse(BaseModel):
    """Response model for trace with all spans."""

    trace_id: str
    spans: List[SpanResponse]
    span_count: int
    error_count: int


# =============================================================================
# Helper Functions
# =============================================================================

def _span_to_response(span_data: Dict[str, Any]) -> SpanResponse:
    """Convert span data to response model."""
    events = []
    for event in span_data.get("events", []):
        events.append(SpanEventResponse(
            name=event.get("name", ""),
            timestamp=event.get("timestamp", ""),
            attributes=event.get("attributes", {}),
        ))

    return SpanResponse(
        trace_id=span_data.get("trace_id", ""),
        span_id=span_data.get("span_id", ""),
        parent_span_id=span_data.get("parent_span_id"),
        operation_name=span_data.get("operation_name", ""),
        service_name=span_data.get("service_name", "flyto"),
        start_time=span_data.get("start_time", ""),
        end_time=span_data.get("end_time"),
        duration_ms=span_data.get("duration_ms"),
        status=span_data.get("status", "unset"),
        status_message=span_data.get("status_message"),
        attributes=span_data.get("attributes", {}),
        events=events,
    )


def _summary_to_response(summary: TraceSummary) -> TraceSummaryResponse:
    """Convert TraceSummary to response model."""
    return TraceSummaryResponse(
        trace_id=summary.trace_id,
        root_operation=summary.root_operation,
        service_name=summary.service_name,
        start_time=summary.start_time,
        end_time=summary.end_time,
        duration_ms=summary.duration_ms,
        span_count=summary.span_count,
        error_count=summary.error_count,
        status=summary.status,
    )


def _build_span_tree(spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build hierarchical span tree for waterfall view.
    S-Grade: Tree traversal computed on backend.
    """
    if not spans:
        return []

    # Create map with children arrays
    span_map = {s["span_id"]: {**s, "children": []} for s in spans}
    roots = []

    # Build tree structure
    for span in spans:
        span_id = span["span_id"]
        parent_id = span.get("parent_span_id")

        if parent_id and parent_id in span_map:
            span_map[parent_id]["children"].append(span_map[span_id])
        else:
            roots.append(span_map[span_id])

    return roots


def _parse_time(time_str: Optional[str]) -> float:
    """Parse ISO timestamp to milliseconds."""
    if not time_str:
        return 0
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        return dt.timestamp() * 1000
    except (ValueError, AttributeError):
        return 0


def _compute_timeline_data(spans: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute timeline visualization data.
    S-Grade: Timeline calculations done on backend.
    Note: Returns camelCase keys for frontend compatibility.
    """
    if not spans:
        return {
            "spans": [],
            "minTime": 0,
            "maxTime": 0,
            "totalDuration": 0
        }

    # Collect all timestamps
    times = []
    for s in spans:
        start = _parse_time(s.get("start_time"))
        end = _parse_time(s.get("end_time"))
        if start > 0:
            times.append(start)
        if end > 0:
            times.append(end)

    if not times:
        return {
            "spans": spans,
            "min_time": 0,
            "max_time": 0,
            "total_duration": 0
        }

    min_time = min(times)
    max_time = max(times)
    total_duration = max_time - min_time if max_time > min_time else 1

    # Compute relative positions for each span
    timeline_spans = []
    for s in spans:
        start = _parse_time(s.get("start_time"))
        duration_ms = s.get("duration_ms") or 0

        relative_start = ((start - min_time) / total_duration * 100) if start > 0 else 0
        relative_width = (duration_ms / total_duration * 100) if duration_ms > 0 else 0

        timeline_spans.append({
            **s,
            "relative_start": round(relative_start, 2),
            "relative_width": round(relative_width, 2)
        })

    return {
        "spans": timeline_spans,
        "minTime": min_time,
        "maxTime": max_time,
        "totalDuration": total_duration
    }


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/", response_model=List[TraceSummaryResponse])
async def list_traces(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    operation_name: Optional[str] = Query(None, description="Filter by operation name"),
    start_time: Optional[str] = Query(None, description="Filter by start time (ISO)"),
    end_time: Optional[str] = Query(None, description="Filter by end time (ISO)"),
    min_duration_ms: Optional[int] = Query(None, ge=0, description="Minimum duration"),
    max_duration_ms: Optional[int] = Query(None, ge=0, description="Maximum duration"),
    has_error: Optional[bool] = Query(None, description="Filter by error status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum traces to return"),
    current_user: dict = Depends(get_current_user),
):
    """
    List traces with optional filtering.

    Returns trace summaries (root span info + span counts).
    """
    query = TraceQuery(
        service_name=service_name,
        operation_name=operation_name,
        start_time=start_time,
        end_time=end_time,
        min_duration_ms=min_duration_ms,
        max_duration_ms=max_duration_ms,
        has_error=has_error,
        user_id=current_user["id"],
        limit=limit,
    )

    summaries = TraceRepository.query_traces(query)

    return [_summary_to_response(s) for s in summaries]


@router.get("/{trace_id}", response_model=TraceDetailResponse)
async def get_trace(trace_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get a trace by ID.

    Returns the trace with all its spans.
    """
    spans = TraceRepository.get_trace(trace_id, user_id=current_user["id"])

    if not spans:
        raise HTTPException(status_code=404, detail="Trace not found")

    span_responses = [_span_to_response(s) for s in spans]
    error_count = sum(1 for s in spans if s.get("status") == "error")

    return TraceDetailResponse(
        trace_id=trace_id,
        spans=span_responses,
        span_count=len(spans),
        error_count=error_count,
    )


@router.get("/{trace_id}/spans")
async def get_trace_spans(trace_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get all spans for a trace with computed tree and timeline data.

    Returns:
        - spans: List of spans ordered by start time
        - span_tree: Hierarchical tree structure for waterfall view
        - timeline_data: Pre-computed relative positions for visualization
    """
    spans = TraceRepository.get_trace(trace_id, user_id=current_user["id"])

    if not spans:
        raise HTTPException(status_code=404, detail="Trace not found")

    span_responses = [_span_to_response(s).model_dump() for s in spans]

    # Build span tree (S-Grade: backend computation)
    span_tree = _build_span_tree(span_responses)

    # Compute timeline data (S-Grade: backend computation)
    timeline_data = _compute_timeline_data(span_responses)

    # Convert to camelCase for frontend compatibility
    return {
        "ok": True,
        "spans": to_camel_case(span_responses),
        "spanTree": to_camel_case(span_tree),
        "timelineData": timeline_data  # Already camelCase
    }


@router.get("/spans/{span_id}", response_model=SpanResponse)
async def get_span(span_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific span by ID."""
    span = TraceRepository.get_span(span_id)

    if not span:
        raise HTTPException(status_code=404, detail="Span not found")

    return _span_to_response(span)


@router.get("/search")
async def search_traces(
    q: Optional[str] = Query(None, description="Search query"),
    service_name: Optional[str] = Query(None, description="Filter by service"),
    operation_name: Optional[str] = Query(None, description="Filter by operation"),
    start_time: Optional[str] = Query(None, description="Start time (ISO)"),
    end_time: Optional[str] = Query(None, description="End time (ISO)"),
    min_duration_ms: Optional[int] = Query(None, ge=0, description="Minimum duration"),
    max_duration_ms: Optional[int] = Query(None, ge=0, description="Maximum duration"),
    has_error: Optional[bool] = Query(None, description="Filter by error status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum traces"),
    current_user: dict = Depends(get_current_user),
):
    """
    Search traces with flexible query options.

    Returns trace summaries matching the search criteria.
    """
    # Use q as operation_name if provided
    search_operation = operation_name or q

    query = TraceQuery(
        service_name=service_name,
        operation_name=search_operation,
        start_time=start_time,
        end_time=end_time,
        min_duration_ms=min_duration_ms,
        max_duration_ms=max_duration_ms,
        has_error=has_error,
        user_id=current_user["id"],
        limit=limit,
    )

    summaries = TraceRepository.query_traces(query)

    return {
        "ok": True,
        "count": len(summaries),
        "traces": [_summary_to_response(s).model_dump() for s in summaries],
    }


@router.get("/search/operations")
async def search_operations(
    prefix: str = Query(..., min_length=1, description="Operation name prefix"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_user: dict = Depends(get_current_user),
):
    """
    Search for operation names.

    Useful for autocomplete in trace search UI.
    """
    # Query traces with operation name filter
    query = TraceQuery(
        operation_name=prefix,
        user_id=current_user["id"],
        limit=limit,
    )

    summaries = TraceRepository.query_traces(query)

    # Extract unique operation names
    operations = list({s.root_operation for s in summaries})

    return {
        "ok": True,
        "operations": operations[:limit],
    }


@router.delete("/cleanup")
async def cleanup_old_traces(
    before: str = Query(..., description="Delete traces before this timestamp (ISO)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete traces older than specified timestamp.

    Args:
        before: Delete traces before this timestamp (ISO format)

    Returns:
        Number of deleted spans.
    """
    deleted = TraceRepository.cleanup(before)

    return {
        "ok": True,
        "deleted": deleted,
        "message": f"Deleted {deleted} spans",
    }
