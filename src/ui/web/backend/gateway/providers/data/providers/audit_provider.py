"""
Audit Log Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from gateway.providers.data.models import (
    AuditLogDTO,
    AuditLogCreateDTO,
    PaginatedResponse,
)


class AuditLogProvider(ABC):
    """
    Audit Log data provider interface.

    Records system actions for compliance and debugging.
    """

    @abstractmethod
    async def create_log(
        self,
        data: AuditLogCreateDTO,
    ) -> AuditLogDTO:
        """Create an audit log entry."""
        pass

    @abstractmethod
    async def list_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        actor_id: str = None,
        action: str = None,
        resource_type: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> PaginatedResponse:
        """List audit logs with filters."""
        pass

    @abstractmethod
    async def get_log(
        self,
        log_id: str,
    ) -> Optional[AuditLogDTO]:
        """Get single audit log entry."""
        pass

    @abstractmethod
    async def get_user_activity(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[AuditLogDTO]:
        """Get recent activity for a user."""
        pass
