"""
User Tool Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional

from gateway.providers.data.models import (
    UserToolDTO,
    UserToolCreateDTO,
    UserToolUpdateDTO,
    PaginatedResponse,
)


class UserToolProvider(ABC):
    """
    User tool data provider interface.

    Handles user custom tools/plugins.
    """

    @abstractmethod
    async def list_user_tools(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List user's custom tools."""
        pass

    @abstractmethod
    async def get_tool(
        self,
        user_id: str,
        tool_id: str,
    ) -> Optional[UserToolDTO]:
        """Get single tool."""
        pass

    @abstractmethod
    async def create_tool(
        self,
        user_id: str,
        data: UserToolCreateDTO,
    ) -> UserToolDTO:
        """Create a custom tool."""
        pass

    @abstractmethod
    async def update_tool(
        self,
        user_id: str,
        tool_id: str,
        data: UserToolUpdateDTO,
    ) -> Optional[UserToolDTO]:
        """Update a custom tool."""
        pass

    @abstractmethod
    async def delete_tool(
        self,
        user_id: str,
        tool_id: str,
    ) -> bool:
        """Delete a custom tool."""
        pass

    @abstractmethod
    async def list_public_tools(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List public tools."""
        pass

    @abstractmethod
    async def execute_tool(
        self,
        user_id: str,
        tool_id: str,
        params: dict,
    ) -> dict:
        """Execute a tool and return result."""
        pass
