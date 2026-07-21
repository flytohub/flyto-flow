"""
Review Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional

from gateway.providers.data.models import (
    ReviewDTO,
    ReviewCreateDTO,
    ReviewUpdateDTO,
    ReviewStatsDTO,
    PaginatedResponse,
)


class ReviewProvider(ABC):
    """
    Review data provider interface.

    Handles template reviews and ratings.
    """

    @abstractmethod
    async def list_reviews(
        self,
        template_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List reviews for a template."""
        pass

    @abstractmethod
    async def get_review(
        self,
        review_id: str,
    ) -> Optional[ReviewDTO]:
        """Get single review."""
        pass

    @abstractmethod
    async def create_review(
        self,
        user_id: str,
        data: ReviewCreateDTO,
    ) -> ReviewDTO:
        """Create a review."""
        pass

    @abstractmethod
    async def update_review(
        self,
        user_id: str,
        review_id: str,
        data: ReviewUpdateDTO,
    ) -> Optional[ReviewDTO]:
        """Update a review."""
        pass

    @abstractmethod
    async def delete_review(
        self,
        user_id: str,
        review_id: str,
    ) -> bool:
        """Delete a review."""
        pass

    @abstractmethod
    async def get_review_stats(
        self,
        template_id: str,
    ) -> ReviewStatsDTO:
        """Get review statistics for a template."""
        pass

    @abstractmethod
    async def get_user_review(
        self,
        user_id: str,
        template_id: str,
    ) -> Optional[ReviewDTO]:
        """Get user's review for a template."""
        pass
