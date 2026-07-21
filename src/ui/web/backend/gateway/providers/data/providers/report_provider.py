"""
Report Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional

from gateway.providers.data.models import (
    ReportDTO,
    ReportCreateDTO,
    ReportUpdateDTO,
    PaginatedResponse,
)


class ReportProvider(ABC):
    """
    Report data provider interface.

    Handles content reports for moderation.
    """

    @abstractmethod
    async def list_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str = None,
        target_type: str = None,
    ) -> PaginatedResponse:
        """List reports."""
        pass

    @abstractmethod
    async def get_report(
        self,
        report_id: str,
    ) -> Optional[ReportDTO]:
        """Get single report."""
        pass

    @abstractmethod
    async def create_report(
        self,
        reporter_id: str,
        data: ReportCreateDTO,
    ) -> ReportDTO:
        """Create a report."""
        pass

    @abstractmethod
    async def update_report(
        self,
        admin_id: str,
        report_id: str,
        data: ReportUpdateDTO,
    ) -> Optional[ReportDTO]:
        """Update/resolve a report."""
        pass

    @abstractmethod
    async def delete_report(
        self,
        report_id: str,
    ) -> bool:
        """Delete a report."""
        pass

    @abstractmethod
    async def get_user_reports(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """Get reports submitted by a user."""
        pass

    @abstractmethod
    async def get_stats(self) -> dict:
        """Get report statistics."""
        pass
