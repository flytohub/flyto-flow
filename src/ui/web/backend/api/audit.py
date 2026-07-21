"""
Audit API

REST endpoints for audit log access.

NOTE: This is an Enterprise-only feature (Phase 9).
Requires AUDIT_IMMUTABLE capability for basic access.
Archive/restore requires AUDIT_ARCHIVE capability.
Integrity verification requires AUDIT_VERIFY capability.

SECURITY: Audit logs contain sensitive information about all user actions.
Access is restricted to:
1. Admin users (via require_admin dependency)
2. Users with LOCAL_AUDIT feature capability
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from capabilities import Feature, require_feature
from services.audit.entry import ActorType, AuditAction, AuditEntry
from services.audit.service import AuditService
from services.audit.verifier import VerificationResult
from services.audit.archiver import AuditArchiver
from services.audit.security_checker import SecurityChecker
from api.admin_guard import require_admin

logger = logging.getLogger(__name__)

# Public router kept only for backward-compatible imports.
# NOTE: The stub GET /audit/ and /audit/stats handlers were REMOVED. When mounted
# before the real router they shadowed the real handlers (FastAPI serves the first
# route registered for an identical path), so the audit table/stats were always
# empty and the REQUIRED organization_id query param was silently ignored — even
# for Pro admins. The real router below (feature-gated + require_admin) now serves
# those paths.
public_router = APIRouter(prefix="/audit", tags=["audit"])


# Feature-gated router for full functionality
# All endpoints in this router require:
# 1. LOCAL_AUDIT feature capability (for subscription/license check)
# 2. Admin user (for RBAC check - only admins can view audit logs)
router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[
        Depends(require_feature(Feature.LOCAL_AUDIT)),
        Depends(require_admin),
    ],
)


# Request/Response Models

class AuditEntryResponse(BaseModel):
    """Response model for an audit entry."""

    id: str
    sequence_number: int
    organization_id: str
    actor_id: str
    actor_type: str
    actor_ip: Optional[str]
    actor_user_agent: Optional[str]
    action: str
    resource_type: str
    resource_id: str
    old_value_hash: Optional[str]
    new_value_hash: Optional[str]
    change_summary: Optional[str]
    timestamp: str
    prev_entry_hash: str
    entry_hash: str
    trace_id: Optional[str]
    metadata: Dict[str, Any]


class VerificationResponse(BaseModel):
    """Response model for verification result."""

    organization_id: str
    verified_at: str
    is_valid: bool
    entries_checked: int
    start_sequence: int
    end_sequence: int
    tampering_reports: List[Dict[str, Any]]
    error: Optional[str]


class ArchiveRequest(BaseModel):
    """Request model for archiving."""

    before_sequence: int = Field(..., description="Archive entries before this sequence")
    destination: str = Field(..., description="Directory path for archive")
    delete_after_archive: bool = Field(default=False, description="Delete entries after archiving")


class ArchiveResponse(BaseModel):
    """Response model for archive result."""

    id: str
    organization_id: str
    start_sequence: int
    end_sequence: int
    entries_archived: int
    archive_path: str
    checksum: str
    created_at: str
    success: bool
    error: Optional[str]


class ArchiveInfoResponse(BaseModel):
    """Response model for archive info."""

    id: str
    organization_id: str
    start_sequence: int
    end_sequence: int
    archive_path: str
    checksum: str
    created_at: str


def _entry_to_response(entry: AuditEntry) -> AuditEntryResponse:
    """Convert AuditEntry to response model."""
    return AuditEntryResponse(
        id=entry.id,
        sequence_number=entry.sequence_number,
        organization_id=entry.organization_id,
        actor_id=entry.actor_id,
        actor_type=entry.actor_type.value if hasattr(entry.actor_type, "value") else entry.actor_type,
        actor_ip=entry.actor_ip,
        actor_user_agent=entry.actor_user_agent,
        action=entry.action.value if hasattr(entry.action, "value") else entry.action,
        resource_type=entry.resource_type,
        resource_id=entry.resource_id,
        old_value_hash=entry.old_value_hash,
        new_value_hash=entry.new_value_hash,
        change_summary=entry.change_summary,
        timestamp=entry.timestamp,
        prev_entry_hash=entry.prev_entry_hash,
        entry_hash=entry.entry_hash,
        trace_id=entry.trace_id,
        metadata=entry.metadata,
    )


# Endpoints

@router.get("/", response_model=List[AuditEntryResponse])
async def query_audit_log(
    organization_id: str = Query(..., description="Organization ID"),
    actor_id: Optional[str] = Query(None, description="Filter by actor"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    start_time: Optional[str] = Query(None, description="Filter by start time (ISO)"),
    end_time: Optional[str] = Query(None, description="Filter by end time (ISO)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum entries"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """Query the audit log."""
    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    entries = AuditService.query(
        organization_id=organization_id,
        actor_id=actor_id,
        action=action_enum,
        resource_type=resource_type,
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )

    return [_entry_to_response(e) for e in entries]


@router.get("/count")
async def count_entries(
    organization_id: str = Query(..., description="Organization ID"),
):
    """Count audit entries for an organization."""
    count = AuditService.count(organization_id)
    return {"count": count}


@router.get("/stats")
async def get_audit_stats(
    organization_id: str = Query(..., description="Organization ID"),
):
    """Get audit log statistics."""
    count = AuditService.count(organization_id)

    # Get recent entries to compute action breakdown
    recent_entries = AuditService.query(
        organization_id=organization_id,
        limit=1000,
    )

    action_counts = {}
    resource_counts = {}
    actor_counts = {}

    for entry in recent_entries:
        action = entry.action.value if hasattr(entry.action, "value") else entry.action
        action_counts[action] = action_counts.get(action, 0) + 1

        resource_counts[entry.resource_type] = resource_counts.get(entry.resource_type, 0) + 1
        actor_counts[entry.actor_id] = actor_counts.get(entry.actor_id, 0) + 1

    return {
        "ok": True,
        "total_entries": count,
        "actions": action_counts,
        "resources": resource_counts,
        "top_actors": dict(sorted(actor_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
    }


@router.get("/{entry_id}", response_model=AuditEntryResponse)
async def get_audit_entry(entry_id: str):
    """Get a specific audit entry."""
    entry = AuditService.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return _entry_to_response(entry)


@router.get("/resource/{resource_type}/{resource_id}", response_model=List[AuditEntryResponse])
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    organization_id: str = Query(..., description="Organization ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum entries"),
):
    """Get audit history for a specific resource."""
    entries = AuditService.get_resource_history(
        organization_id=organization_id,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit,
    )

    return [_entry_to_response(e) for e in entries]


@router.get("/actor/{actor_id}", response_model=List[AuditEntryResponse])
async def get_actor_activity(
    actor_id: str,
    organization_id: str = Query(..., description="Organization ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum entries"),
):
    """Get activity for a specific actor."""
    entries = AuditService.get_actor_activity(
        organization_id=organization_id,
        actor_id=actor_id,
        limit=limit,
    )

    return [_entry_to_response(e) for e in entries]


@router.get(
    "/verify",
    response_model=VerificationResponse,
    dependencies=[Depends(require_feature(Feature.LOCAL_AUDIT_VERIFY))],
)
async def verify_integrity(
    organization_id: str = Query(..., description="Organization ID"),
    start_seq: Optional[int] = Query(None, description="Start sequence"),
    end_seq: Optional[int] = Query(None, description="End sequence"),
):
    """Verify audit log integrity. Requires AUDIT_VERIFY capability."""
    result = AuditService.verify_integrity(
        organization_id=organization_id,
        start_seq=start_seq,
        end_seq=end_seq,
    )

    return VerificationResponse(
        organization_id=result.organization_id,
        verified_at=result.verified_at,
        is_valid=result.is_valid,
        entries_checked=result.entries_checked,
        start_sequence=result.start_sequence,
        end_sequence=result.end_sequence,
        tampering_reports=[r.to_dict() for r in result.tampering_reports],
        error=result.error,
    )


@router.post("/verify", response_model=VerificationResponse)
async def verify_audit_log(
    organization_id: str = Query(..., description="Organization ID"),
    start_seq: Optional[int] = Query(None, description="Start sequence"),
    end_seq: Optional[int] = Query(None, description="End sequence"),
):
    """Verify audit log integrity (POST method for API consistency)."""
    result = AuditService.verify_integrity(
        organization_id=organization_id,
        start_seq=start_seq,
        end_seq=end_seq,
    )

    return VerificationResponse(
        organization_id=result.organization_id,
        verified_at=result.verified_at,
        is_valid=result.is_valid,
        entries_checked=result.entries_checked,
        start_sequence=result.start_sequence,
        end_sequence=result.end_sequence,
        tampering_reports=[r.to_dict() for r in result.tampering_reports],
        error=result.error,
    )


@router.get("/export")
async def export_audit_log(
    organization_id: str = Query(..., description="Organization ID"),
    format: str = Query(default="json", pattern="^(json|csv)$"),
    start_time: Optional[str] = Query(None, description="Start time (ISO)"),
    end_time: Optional[str] = Query(None, description="End time (ISO)"),
    limit: int = Query(10000, ge=1, le=100000, description="Maximum entries"),
):
    """Export audit log in specified format."""
    from fastapi.responses import Response

    entries = AuditService.query(
        organization_id=organization_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )

    if format == "csv":
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "sequence_number", "timestamp", "actor_id", "actor_type",
            "action", "resource_type", "resource_id", "change_summary"
        ])

        for entry in entries:
            writer.writerow([
                entry.id,
                entry.sequence_number,
                entry.timestamp,
                entry.actor_id,
                entry.actor_type.value if hasattr(entry.actor_type, "value") else entry.actor_type,
                entry.action.value if hasattr(entry.action, "value") else entry.action,
                entry.resource_type,
                entry.resource_id,
                entry.change_summary or "",
            ])

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_log_{organization_id}.csv"},
        )

    else:
        return {
            "ok": True,
            "organization_id": organization_id,
            "count": len(entries),
            "entries": [_entry_to_response(e).model_dump() for e in entries],
        }


@router.get("/security-scan")
async def security_scan(
    organization_id: str = Query(..., description="Organization ID"),
    hours_back: int = Query(24, ge=1, le=720, description="Hours of history to analyze"),
):
    """Run security scan on audit logs: brute force, bulk deletions, after-hours access, permission violations, credential usage."""
    findings = []
    findings.extend(SecurityChecker.check_suspicious_activity(organization_id, hours_back))
    findings.extend(SecurityChecker.check_permission_violations(organization_id, hours_back))
    findings.extend(SecurityChecker.check_credentials(organization_id, hours_back))

    return {
        "ok": True,
        "organization_id": organization_id,
        "hours_back": hours_back,
        "findings": [f.to_dict() for f in findings],
        "total": len(findings),
    }


@router.get("/security-scan/quick")
async def security_quick_check(
    organization_id: str = Query(..., description="Organization ID"),
):
    """Quick security health check: integrity + entry count."""
    return {
        "ok": True,
        **SecurityChecker.quick_check(organization_id),
    }


@router.post(
    "/archive",
    response_model=ArchiveResponse,
    dependencies=[Depends(require_feature(Feature.LOCAL_AUDIT_CHAIN))],
)
async def archive_entries(
    organization_id: str = Query(..., description="Organization ID"),
    request: ArchiveRequest = None,
):
    """Archive old audit entries. Requires AUDIT_ARCHIVE capability."""
    if not request:
        raise HTTPException(status_code=400, detail="Request body required")

    result = AuditArchiver.archive(
        organization_id=organization_id,
        before_sequence=request.before_sequence,
        destination=request.destination,
        delete_after_archive=request.delete_after_archive,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return ArchiveResponse(
        id=result.id,
        organization_id=result.organization_id,
        start_sequence=result.start_sequence,
        end_sequence=result.end_sequence,
        entries_archived=result.entries_archived,
        archive_path=result.archive_path,
        checksum=result.checksum,
        created_at=result.created_at,
        success=result.success,
        error=result.error,
    )


@router.get(
    "/archives",
    response_model=List[ArchiveInfoResponse],
    dependencies=[Depends(require_feature(Feature.LOCAL_AUDIT_CHAIN))],
)
async def list_archives(
    organization_id: str = Query(..., description="Organization ID"),
):
    """List archives for an organization. Requires AUDIT_ARCHIVE capability."""
    archives = AuditArchiver.list_archives(organization_id)

    return [
        ArchiveInfoResponse(
            id=a.id,
            organization_id=a.organization_id,
            start_sequence=a.start_sequence,
            end_sequence=a.end_sequence,
            archive_path=a.archive_path,
            checksum=a.checksum,
            created_at=a.created_at,
        )
        for a in archives
    ]


@router.post(
    "/restore",
    dependencies=[Depends(require_feature(Feature.LOCAL_AUDIT_CHAIN))],
)
async def restore_archive(
    archive_path: str = Query(..., description="Path to archive file"),
):
    """Restore entries from an archive. Requires AUDIT_ARCHIVE capability."""
    try:
        restored = AuditArchiver.restore(archive_path)
        return {"ok": True, "entries_restored": restored}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archive file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
