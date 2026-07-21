"""User Tool DTO Models"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class UserToolDTO(BaseModel):
    """User custom tool/plugin"""
    id: str
    user_id: str

    # Tool info
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None

    # Code
    code: str
    language: str = "javascript"  # javascript, python

    # Schema
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)

    # Status
    is_enabled: bool = True
    is_public: bool = False

    # Usage stats
    execution_count: int = 0
    last_executed_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserToolCreateDTO(BaseModel):
    """DTO for creating a user tool"""
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    code: str
    language: str = "javascript"
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False


class UserToolUpdateDTO(BaseModel):
    """DTO for updating a user tool"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    code: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None
    is_public: Optional[bool] = None
