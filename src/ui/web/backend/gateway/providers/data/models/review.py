"""Review DTO Models"""

from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field


class ReviewDTO(BaseModel):
    """Template review"""
    id: str
    template_id: str
    user_id: str

    # Content
    rating: int  # 1-5
    comment: Optional[str] = None

    # Author info
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None

    # Status
    is_verified_purchase: bool = False

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None


class ReviewCreateDTO(BaseModel):
    """DTO for creating a review"""
    template_id: str
    rating: int  # 1-5
    comment: Optional[str] = None


class ReviewUpdateDTO(BaseModel):
    """DTO for updating a review"""
    rating: Optional[int] = None
    comment: Optional[str] = None


class ReviewStatsDTO(BaseModel):
    """Review statistics for a template"""
    template_id: str
    average_rating: float = 0.0
    total_reviews: int = 0
    rating_distribution: Dict[int, int] = Field(default_factory=lambda: {
        1: 0, 2: 0, 3: 0, 4: 0, 5: 0
    })
