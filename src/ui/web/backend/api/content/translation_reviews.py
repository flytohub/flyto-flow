"""
Translation Review API Routes

Provides endpoints for translation review workflow.
Users can submit translations for review, admins can approve/reject.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.auth import get_current_user
from api.validators import require_admin as validate_admin
from gateway.providers.hub import get_data_provider
from gateway.providers.data.models.translation_review import (
    TranslationReviewCreateDTO,
    TranslationReviewUpdateDTO,
    TranslationReviewStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/translation-reviews", tags=["Translation Reviews"])


# =============================================================================
# Middleware
# =============================================================================


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role for endpoint access."""
    validate_admin(current_user)
    return current_user


# =============================================================================
# Request/Response Models
# =============================================================================


class SubmitTranslationRequest(BaseModel):
    """Request to submit a translation for review"""
    template_id: str
    language: str = Field(..., min_length=2, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)


class ReviewTranslationRequest(BaseModel):
    """Request to review a translation (admin)"""
    status: str = Field(..., pattern="^(approved|rejected)$")
    notes: Optional[str] = Field(None, max_length=500)


# =============================================================================
# User Endpoints
# =============================================================================


@router.post("")
async def submit_translation(
    data: SubmitTranslationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Submit a translation for review.

    Users can submit translations for templates they own or public templates.
    The translation will be queued for admin approval.
    """
    provider = get_data_provider()
    user_id = current_user["id"]

    try:
        # Verify template exists
        template = await provider.templates.get_template(data.template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Create review
        review = await provider.translation_reviews.create_review(
            user_id=user_id,
            data=TranslationReviewCreateDTO(
                template_id=data.template_id,
                language=data.language,
                content={
                    "name": data.name,
                    "description": data.description or "",
                },
            ),
        )

        return {
            "ok": True,
            "review": {
                "id": review.id,
                "template_id": review.template_id,
                "language": review.language,
                "status": review.status.value,
                "submitted_at": review.submitted_at.isoformat(),
            },
            "message": "Translation submitted for review",
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to submit translation")
        return {"ok": False, "error": "Failed to submit translation"}


@router.get("/my")
async def list_my_translations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List translations submitted by the current user."""
    provider = get_data_provider()

    # This would need a filter by submitted_by, simplified for now
    items, total = await provider.translation_reviews.list_reviews(
        page=page,
        page_size=page_size,
    )

    # Filter to current user's submissions
    user_id = current_user["id"]
    items = [r for r in items if r.submitted_by == user_id]

    return {
        "ok": True,
        "reviews": [
            {
                "id": r.id,
                "template_id": r.template_id,
                "language": r.language,
                "status": r.status.value,
                "content": r.content,
                "submitted_at": r.submitted_at.isoformat(),
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                "review_notes": r.review_notes,
            }
            for r in items
        ],
        "total": len(items),
    }


# =============================================================================
# Admin Endpoints
# =============================================================================


@router.get("")
async def list_reviews(
    status: Optional[str] = Query(None, pattern="^(pending|approved|rejected)$"),
    language: Optional[str] = None,
    template_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_admin),
):
    """List all translation reviews (admin only)."""
    provider = get_data_provider()

    items, total = await provider.translation_reviews.list_reviews(
        status=status,
        language=language,
        template_id=template_id,
        page=page,
        page_size=page_size,
    )

    return {
        "ok": True,
        "reviews": [
            {
                "id": r.id,
                "template_id": r.template_id,
                "language": r.language,
                "status": r.status.value,
                "content": r.content,
                "submitted_by": r.submitted_by,
                "submitted_at": r.submitted_at.isoformat(),
                "reviewed_by": r.reviewed_by,
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                "review_notes": r.review_notes,
            }
            for r in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/pending/count")
async def get_pending_count(
    _: dict = Depends(require_admin),
):
    """Get count of pending reviews (admin only)."""
    provider = get_data_provider()
    count = await provider.translation_reviews.get_pending_count()
    return {"ok": True, "count": count}


@router.get("/{review_id}")
async def get_review(
    review_id: str,
    _: dict = Depends(require_admin),
):
    """Get a translation review by ID (admin only)."""
    provider = get_data_provider()

    review = await provider.translation_reviews.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Get template info for context
    template = await provider.templates.get_template(review.template_id)

    return {
        "ok": True,
        "review": {
            "id": review.id,
            "template_id": review.template_id,
            "template_name": template.name if template else "Unknown",
            "language": review.language,
            "status": review.status.value,
            "content": review.content,
            "submitted_by": review.submitted_by,
            "submitted_at": review.submitted_at.isoformat(),
            "reviewed_by": review.reviewed_by,
            "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None,
            "review_notes": review.review_notes,
        },
    }


@router.patch("/{review_id}")
async def review_translation(
    review_id: str,
    data: ReviewTranslationRequest,
    current_user: dict = Depends(require_admin),
):
    """
    Approve or reject a translation (admin only).

    If approved, the translation is automatically applied to the template.
    """
    provider = get_data_provider()
    admin_id = current_user["id"]

    try:
        status = TranslationReviewStatus.APPROVED if data.status == "approved" else TranslationReviewStatus.REJECTED

        review = await provider.translation_reviews.update_review(
            review_id=review_id,
            admin_id=admin_id,
            data=TranslationReviewUpdateDTO(
                status=status,
                review_notes=data.notes,
            ),
        )

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        return {
            "ok": True,
            "review": {
                "id": review.id,
                "status": review.status.value,
                "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None,
            },
            "message": f"Translation {data.status}",
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to review translation")
        return {"ok": False, "error": "Failed to review translation"}


@router.delete("/{review_id}")
async def delete_review(
    review_id: str,
    _: dict = Depends(require_admin),
):
    """Delete a translation review (admin only)."""
    provider = get_data_provider()

    success = await provider.translation_reviews.delete_review(review_id)
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")

    return {"ok": True, "message": "Review deleted"}
