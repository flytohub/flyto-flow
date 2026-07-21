"""API Key DTO Models"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ApiKeyDTO(BaseModel):
    """User API key"""
    id: str
    user_id: str

    # Key info (actual key is hashed, never exposed)
    name: str
    prefix: str  # First 8 chars of key for identification
    key_hash: str = ""  # Hashed key for verification (not exposed to client)

    # Permissions
    scopes: List[str] = Field(default_factory=lambda: ["read"])

    # Status
    is_active: bool = True
    last_used_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    expires_at: Optional[datetime] = None


class ApiKeyCreateDTO(BaseModel):
    """DTO for creating an API key"""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[str] = Field(default_factory=lambda: ["read"])
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class ApiKeyUpdateDTO(BaseModel):
    """DTO for updating an API key"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    scopes: Optional[List[str]] = None


class ApiKeyVerifyResult(BaseModel):
    """Result of API key verification"""
    valid: bool
    user_id: Optional[str] = None
    key_id: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    error: Optional[str] = None
