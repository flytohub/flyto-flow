"""Report DTO Models"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict


class ReportStatus(str, Enum):
    """Report status"""
    PENDING = "pending"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ReportType(str, Enum):
    """Report target types"""
    TEMPLATE = "template"
    USER = "user"
    REVIEW = "review"
    MESSAGE = "message"


class ReportDTO(BaseModel):
    """Content report"""
    id: str
    reporter_id: str

    # Target
    target_type: ReportType
    target_id: str

    # Content
    reason: str
    details: Optional[str] = None

    # Status
    status: ReportStatus = ReportStatus.PENDING

    # Resolution
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    action_taken: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class ReportCreateDTO(BaseModel):
    """DTO for creating a report"""
    target_type: ReportType
    target_id: str
    reason: str
    details: Optional[str] = None


class ReportUpdateDTO(BaseModel):
    """DTO for updating a report"""
    status: Optional[ReportStatus] = None
    resolution_note: Optional[str] = None
    action_taken: Optional[str] = None
