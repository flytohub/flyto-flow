"""Translation Review DTO Models

Enhanced translation review workflow with:
- Status tracking on templates
- Revision history
- Notification support
"""

from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class TranslationReviewStatus(str, Enum):
    """Translation review status"""
    PENDING = "pending"
    IN_REVIEW = "in_review"  # Admin has started reviewing
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"  # Returned to submitter for changes


class TranslationReviewDTO(BaseModel):
    """
    DTO for template translation reviews.

    Used for the localized review workflow where translations
    need admin approval before becoming visible.
    """
    id: str
    template_id: str
    template_name: Optional[str] = None  # For display
    language: str  # e.g., "zh-TW", "ja"
    status: TranslationReviewStatus = TranslationReviewStatus.PENDING

    # Translation content
    content: Dict[str, str] = Field(default_factory=dict)
    # Format: {"name": "...", "description": "..."}

    # Submitter
    submitted_by: str  # user_id
    submitter_name: Optional[str] = None  # For display
    submitted_at: datetime

    # Reviewer
    reviewed_by: Optional[str] = None
    reviewer_name: Optional[str] = None  # For display
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    # Revision tracking
    revision_number: int = 1
    previous_review_id: Optional[str] = None  # Link to previous revision
    revision_history: List[dict] = Field(default_factory=list)

    # Quality metrics
    word_count: int = 0
    quality_score: Optional[float] = None  # 0-100

    model_config = ConfigDict(use_enum_values=True)


class TranslationReviewCreateDTO(BaseModel):
    """DTO for creating a translation review"""
    template_id: str
    language: str
    content: Dict[str, str]
    previous_review_id: Optional[str] = None  # For revisions


class TranslationReviewUpdateDTO(BaseModel):
    """DTO for updating a translation review (admin only)"""
    status: Optional[TranslationReviewStatus] = None
    review_notes: Optional[str] = None
    quality_score: Optional[float] = None


class TranslationReviewSummaryDTO(BaseModel):
    """Summary of translation review status for a template"""
    template_id: str
    total_languages: int = 0
    pending_reviews: int = 0
    approved_translations: int = 0
    languages_with_pending: List[str] = Field(default_factory=list)
    languages_approved: List[str] = Field(default_factory=list)
    languages_rejected: List[str] = Field(default_factory=list)
