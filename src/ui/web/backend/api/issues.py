"""
Issues API

Public issue tracking system (GitHub Issues style).
Public endpoints do not require authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from api.auth import get_current_user, get_optional_user
from api.admin_guard import require_admin
from gateway.providers.hub import get_provider_hub

router = APIRouter(prefix="/issues", tags=["issues"])


class CreateIssueRequest(BaseModel):
    """Request body for creating a new issue."""
    title: str
    description: str
    type: str = "bug"  # bug, feature, question
    priority: str = "medium"  # low, medium, high
    labels: List[str] = []
    images: List[str] = []


class UpdateIssueRequest(BaseModel):
    """Request body for updating an existing issue."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # open, in_progress, closed
    priority: Optional[str] = None
    labels: Optional[List[str]] = None


class CreateCommentRequest(BaseModel):
    """Request body for creating a comment on an issue."""
    content: str
    images: List[str] = []


# ============== Public endpoints ==============

@router.get("/")
async def list_issues(
    status: Optional[str] = None,
    type: Optional[str] = None,
    sort: str = Query(default="newest", pattern="^(newest|oldest|most_upvoted|recently_updated)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """List all issues (public)."""
    hub = get_provider_hub()

    result = await hub.data.issues.list_issues(
        page=page,
        page_size=page_size,
        status=status,
        issue_type=type,
        sort=sort,
    )

    return {
        "ok": True,
        "issues": [i.model_dump() for i in result.items],
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "has_next": result.has_next,
        "has_prev": result.has_prev,
    }


@router.get("/{issue_id}")
async def get_issue(issue_id: str):
    """Get single issue (public)."""
    hub = get_provider_hub()

    issue = await hub.data.issues.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    return {"ok": True, "issue": issue.model_dump()}


# ============== Auth-required endpoints ==============

@router.post("/")
async def create_issue(
    request: CreateIssueRequest,
    user: dict = Depends(get_current_user),
):
    """Create an issue (requires auth)."""
    hub = get_provider_hub()

    from gateway.providers.data.models import IssueCreateDTO, IssueType, IssuePriority

    issue = await hub.data.issues.create_issue(
        author_id=user["id"],
        author_name=user.get("name", user.get("display_name", "Anonymous")),
        author_avatar=user.get("avatar", user.get("photo_url")),
        data=IssueCreateDTO(
            title=request.title,
            description=request.description,
            type=IssueType(request.type),
            priority=IssuePriority(request.priority),
            labels=request.labels,
            images=request.images,
        ),
    )

    return {"ok": True, "issue": issue.model_dump()}


@router.put("/{issue_id}")
async def update_issue(
    issue_id: str,
    request: UpdateIssueRequest,
    user: dict = Depends(get_current_user),
):
    """Update an issue (author or admin)."""
    hub = get_provider_hub()

    # Check permissions: author or admin
    existing = await hub.data.issues.get_issue(issue_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Issue not found")

    is_admin = user.get("is_admin", False)
    is_author = existing.author_id == user["id"]

    if not is_author and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    from gateway.providers.data.models import IssueUpdateDTO, IssueStatus, IssuePriority

    update_data = IssueUpdateDTO(
        title=request.title,
        description=request.description,
        labels=request.labels,
    )

    if request.status:
        update_data.status = IssueStatus(request.status)
    if request.priority:
        update_data.priority = IssuePriority(request.priority)

    closed_by = user["id"] if request.status == "closed" else None

    issue = await hub.data.issues.update_issue(
        issue_id=issue_id,
        data=update_data,
        closed_by=closed_by,
    )

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    return {"ok": True, "issue": issue.model_dump()}


# Admin DELETE /issues/{id} — MIGRATED to flyto-admin BFF
#   DELETE /admin/cloud/issues/{id}
# The PUT /{id} endpoint above stays here because it serves both authors
# (author can edit own issue) and admins (inline is_admin check); not a pure
# admin operation.

@router.post("/{issue_id}/upvote")
async def toggle_upvote(
    issue_id: str,
    user: dict = Depends(get_current_user),
):
    """Toggle upvote on an issue (requires auth)."""
    hub = get_provider_hub()

    issue = await hub.data.issues.toggle_upvote(issue_id, user["id"])
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    return {"ok": True, "issue": issue.model_dump()}


# ============== Comments ==============

@router.get("/{issue_id}/comments")
async def list_comments(
    issue_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    """List comments for an issue (public)."""
    hub = get_provider_hub()

    result = await hub.data.issues.list_comments(
        issue_id=issue_id,
        page=page,
        page_size=page_size,
    )

    return {
        "ok": True,
        "comments": [c.model_dump() for c in result.items],
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
    }


@router.post("/{issue_id}/comments")
async def create_comment(
    issue_id: str,
    request: CreateCommentRequest,
    user: dict = Depends(get_current_user),
):
    """Add a comment to an issue (requires auth)."""
    hub = get_provider_hub()

    from gateway.providers.data.models import IssueCommentCreateDTO

    try:
        comment = await hub.data.issues.create_comment(
            issue_id=issue_id,
            author_id=user["id"],
            author_name=user.get("name", user.get("display_name", "Anonymous")),
            author_avatar=user.get("avatar", user.get("photo_url")),
            data=IssueCommentCreateDTO(content=request.content, images=request.images),
        )
        return {"ok": True, "comment": comment.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{issue_id}/comments/{comment_id}")
async def delete_comment(
    issue_id: str,
    comment_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a comment (author or admin)."""
    hub = get_provider_hub()

    # Check comment ownership
    comments_result = await hub.data.issues.list_comments(issue_id)
    comment = next((c for c in comments_result.items if c.id == comment_id), None)

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    is_admin = user.get("is_admin", False)
    is_author = comment.author_id == user["id"]

    if not is_author and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    success = await hub.data.issues.delete_comment(issue_id, comment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")

    return {"ok": True}
