"""
Reports API

Endpoints for content reports (moderation).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from api.auth import get_current_user
from gateway.providers.hub import get_provider_hub

router = APIRouter(prefix="/reports", tags=["reports"])


class CreateReportRequest(BaseModel):
    """Request body for creating a content report."""
    target_type: str  # template, user, review, message
    target_id: str
    reason: str
    details: Optional[str] = None


class UpdateReportRequest(BaseModel):
    """Request body for updating a report status."""
    status: Optional[str] = None  # pending, reviewing, resolved, dismissed
    resolution_note: Optional[str] = None
    action_taken: Optional[str] = None


# User endpoints

@router.post("/")
async def create_report(
    request: CreateReportRequest,
    user: dict = Depends(get_current_user),
):
    """Create a content report."""
    hub = get_provider_hub()

    try:
        from gateway.providers.data.models import ReportCreateDTO, ReportType

        report = await hub.data.reports.create_report(
            reporter_id=user["id"],
            data=ReportCreateDTO(
                target_type=ReportType(request.target_type),
                target_id=request.target_id,
                reason=request.reason,
                details=request.details,
            ),
        )

        return {"ok": True, "report": report.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-reports")
async def list_my_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """List reports I've submitted."""
    hub = get_provider_hub()

    result = await hub.data.reports.get_user_reports(
        user_id=user["id"],
        page=page,
        page_size=page_size,
    )

    return {
        "ok": True,
        "reports": [r.model_dump() for r in result.items],
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
    }


# Admin endpoints — MIGRATED to flyto-admin BFF on 2026-05-19.
#   GET    /reports            → flyto-admin GET    /admin/cloud/reports
#   GET    /reports/stats      → flyto-admin GET    /admin/cloud/reports/stats
#   GET    /reports/{id}       → flyto-admin GET    /admin/cloud/reports/{id}
#   PUT    /reports/{id}       → flyto-admin PATCH  /admin/cloud/reports/{id}
#   DELETE /reports/{id}       → flyto-admin DELETE /admin/cloud/reports/{id}
# Customer-facing endpoints above (POST /, GET /my-reports) stay here.
