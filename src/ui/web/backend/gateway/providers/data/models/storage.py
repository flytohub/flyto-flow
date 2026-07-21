"""Storage DTO Models"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FileUploadDTO(BaseModel):
    """Uploaded file info"""
    id: str
    user_id: str

    # File info
    filename: str
    original_name: str
    content_type: str
    size: int

    # URL
    url: str

    # Metadata
    purpose: Optional[str] = None  # avatar, chat, template, etc.

    # Timestamps
    created_at: datetime


class FileUploadRequestDTO(BaseModel):
    """DTO for file upload request"""
    purpose: Optional[str] = None
