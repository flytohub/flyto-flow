"""
Storage Provider Interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, BinaryIO

from gateway.providers.data.models import FileUploadDTO, PaginatedResponse


@dataclass(frozen=True)
class StoredFile:
    """Private object content returned after provider-level ownership checks."""

    content: bytes
    filename: str
    content_type: str


class StorageProvider(ABC):
    """
    File storage provider interface.

    Deployment-specific implementations may use hosted object storage,
    S3-compatible storage, or the local filesystem.
    """

    @abstractmethod
    async def upload_file(
        self,
        user_id: str,
        file_data: BinaryIO,
        filename: str,
        content_type: str,
        purpose: str = None,
    ) -> FileUploadDTO:
        """Upload file."""
        pass

    @abstractmethod
    async def get_file_url(
        self,
        file_id: str,
    ) -> Optional[str]:
        """Get file URL."""
        pass

    @abstractmethod
    async def download_file(
        self,
        user_id: str,
        file_id: str,
    ) -> Optional[StoredFile]:
        """Download a user-owned file, or return None when it does not exist."""
        pass

    @abstractmethod
    async def delete_file(
        self,
        user_id: str,
        file_id: str,
    ) -> bool:
        """Delete file."""
        pass

    @abstractmethod
    async def list_user_files(
        self,
        user_id: str,
        purpose: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List user's uploaded files."""
        pass
