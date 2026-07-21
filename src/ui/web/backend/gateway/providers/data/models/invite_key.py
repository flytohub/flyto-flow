"""Invite Key DTO Models"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class InviteKeyDTO(BaseModel):
    """Invite key"""
    id: str
    key: str
    creator_id: str
    template_id: Optional[str] = None  # If set, this is a template-specific key

    # Usage
    max_uses: int = 1
    current_uses: int = 0
    used_by: List[str] = Field(default_factory=list)

    # Status
    is_active: bool = True
    expires_at: Optional[datetime] = None

    # Metadata
    note: Optional[str] = None
    campaign: Optional[str] = None

    # Timestamps
    created_at: datetime
    last_used_at: Optional[datetime] = None


class InviteKeyCreateDTO(BaseModel):
    """DTO for creating an invite key"""
    max_uses: int = 1
    expires_at: Optional[datetime] = None
    note: Optional[str] = None
    campaign: Optional[str] = None


class InviteKeyBatchCreateDTO(BaseModel):
    """DTO for batch creating invite keys"""
    count: int = 10
    max_uses: int = 1
    expires_at: Optional[datetime] = None
    campaign: Optional[str] = None


class InviteKeyStatsDTO(BaseModel):
    """Invite key statistics"""
    total_keys: int = 0
    active_keys: int = 0
    expired_keys: int = 0
    total_uses: int = 0
    total_max_uses: int = 0
    usage_rate: float = 0.0
    by_campaign: Dict[str, int] = Field(default_factory=dict)
