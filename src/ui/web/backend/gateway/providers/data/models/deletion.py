"""Deletion Request DTO Models (GDPR)"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict


class DeletionRequestStatus(str, Enum):
    """Deletion request status"""
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DeletionRequestDTO(BaseModel):
    """Account deletion request (GDPR 30-day buffer)"""
    id: str
    user_id: str
    email: str

    # Status
    status: DeletionRequestStatus = DeletionRequestStatus.PENDING

    # Reason
    reason: Optional[str] = None
    feedback: Optional[str] = None

    # Dates
    requested_at: datetime
    scheduled_deletion_at: datetime  # 30 days after request
    cancelled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class DeletionRequestCreateDTO(BaseModel):
    """DTO for creating a deletion request"""
    reason: Optional[str] = None
    feedback: Optional[str] = None
