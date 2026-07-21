"""Module Access DTO Models

Models for module access control, purchases, and organization sharing.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class AccessType(str, Enum):
    """Module access type"""
    PURCHASED = "purchased"          # User purchased the module
    ORG_SHARED = "org_shared"        # Shared through organization
    PERSONAL = "personal"            # User-created custom module
    GRANTED = "granted"              # Admin granted access
    TRIAL = "trial"                  # Trial access


class ModuleAccessDTO(BaseModel):
    """
    Module access record.

    Represents a user's access to a specific module.
    """
    id: str = Field(..., description="Unique access record ID")
    user_id: str = Field(..., description="User ID")
    module_id: str = Field(..., description="Module ID (e.g., 'http.request')")
    access_type: AccessType = Field(..., description="Type of access")

    # Access metadata
    granted_by: Optional[str] = Field(None, description="ID of user who granted access")
    granted_at: datetime = Field(..., description="When access was granted")
    expires_at: Optional[datetime] = Field(None, description="When access expires (None = permanent)")

    # Purchase info (if access_type == PURCHASED)
    order_id: Optional[str] = Field(None, description="Order ID for purchase")
    price_paid: Optional[float] = Field(None, description="Price paid (in USD)")

    # Organization sharing (if access_type == ORG_SHARED)
    organization_id: Optional[str] = Field(None, description="Organization that shared the module")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(use_enum_values=True)


class ModuleAccessCreateDTO(BaseModel):
    """DTO for creating a module access record"""
    user_id: str
    module_id: str
    access_type: AccessType
    granted_by: Optional[str] = None
    expires_at: Optional[datetime] = None
    order_id: Optional[str] = None
    price_paid: Optional[float] = None
    organization_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModuleAccessUpdateDTO(BaseModel):
    """DTO for updating a module access record"""
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class OrgModuleShareDTO(BaseModel):
    """
    Organization module sharing record.

    When an organization purchases or is granted access to modules,
    all members can use them.
    """
    id: str = Field(..., description="Unique share record ID")
    organization_id: str = Field(..., description="Organization ID")
    module_id: str = Field(..., description="Module ID")

    # Access details
    shared_by: str = Field(..., description="User who shared/purchased")
    shared_at: datetime = Field(..., description="When shared")
    expires_at: Optional[datetime] = Field(None, description="When sharing expires")

    # Limits
    max_users: Optional[int] = Field(None, description="Max users who can use (None = unlimited)")
    current_users: int = Field(default=0, description="Current users using this module")

    # Purchase info
    order_id: Optional[str] = Field(None, description="Order ID if purchased")
    license_type: str = Field(default="unlimited", description="License type: unlimited, per_seat, concurrent")

    model_config = ConfigDict(use_enum_values=True)


class OrgModuleShareCreateDTO(BaseModel):
    """DTO for creating an organization module share"""
    organization_id: str
    module_id: str
    shared_by: str
    expires_at: Optional[datetime] = None
    max_users: Optional[int] = None
    order_id: Optional[str] = None
    license_type: str = "unlimited"


class ModulePurchaseDTO(BaseModel):
    """
    Module purchase record.

    Tracks individual module purchases for marketplace.
    """
    id: str = Field(..., description="Unique purchase ID")
    user_id: str = Field(..., description="Buyer user ID")
    module_id: str = Field(..., description="Purchased module ID")

    # Purchase details
    order_id: str = Field(..., description="Order/transaction ID")
    price: float = Field(..., description="Purchase price (USD)")
    currency: str = Field(default="USD", description="Currency code")

    # Status
    status: str = Field(default="completed", description="Purchase status: pending, completed, refunded")
    purchased_at: datetime = Field(..., description="Purchase timestamp")
    refunded_at: Optional[datetime] = Field(None, description="Refund timestamp if refunded")

    # Creator info (for marketplace)
    creator_id: Optional[str] = Field(None, description="Module creator ID")
    creator_earnings: Optional[float] = Field(None, description="Creator's earnings from this sale")
    platform_fee: Optional[float] = Field(None, description="Platform fee charged")

    model_config = ConfigDict(use_enum_values=True)


class ModulePurchaseCreateDTO(BaseModel):
    """DTO for creating a module purchase record"""
    user_id: str
    module_id: str
    order_id: str
    price: float
    currency: str = "USD"
    creator_id: Optional[str] = None
    creator_earnings: Optional[float] = None
    platform_fee: Optional[float] = None


class UserModuleAccessSummary(BaseModel):
    """
    Summary of a user's module access.

    Used for API responses.
    """
    user_id: str
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None

    # Access counts
    purchased_count: int = 0
    org_shared_count: int = 0
    personal_count: int = 0

    # Module lists
    purchased_modules: List[str] = Field(default_factory=list)
    org_shared_modules: List[str] = Field(default_factory=list)
    personal_modules: List[str] = Field(default_factory=list)

    # Total accessible (union of all)
    total_accessible: int = 0
