"""AI Usage DTO Models"""

from datetime import datetime
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field


class AIUsageDTO(BaseModel):
    """AI usage record"""
    id: str
    user_id: str

    # Period
    year: int
    month: int

    # Usage
    tokens_used: int = 0
    tokens_limit: int = 100000  # Default monthly limit
    requests_count: int = 0

    # Breakdown by model
    usage_by_model: Dict[str, int] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None


class AIUsageRecordDTO(BaseModel):
    """Single AI usage record for tracking"""
    user_id: str
    model: str
    tokens_input: int
    tokens_output: int
    request_type: str  # chat, workflow, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)
