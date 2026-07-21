"""Audit Log DTO Models"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class AuditAction(str, Enum):
    """Audit log action types"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    BYPASS_TRIAL_CHECK = "bypass_trial_check"
    EXPORT = "export"
    IMPORT = "import"
    ADMIN_ACTION = "admin_action"
    # GDPR User Deletion
    USER_DELETION_REQUESTED = "user_deletion_requested"
    USER_DELETION_CANCELLED = "user_deletion_cancelled"
    USER_DELETION_COMPLETED = "user_deletion_completed"
    USER_DATA_DELETED = "user_data_deleted"
    # Payment & Refund
    PURCHASE_COMPLETED = "purchase_completed"
    PURCHASE_REFUNDED = "purchase_refunded"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    SUBSCRIPTION_CREATED = "subscription_created"
    # Fee & Commission
    PLATFORM_FEE_CHARGED = "platform_fee_charged"
    CREATOR_EARNINGS_CREDITED = "creator_earnings_credited"
    PAYOUT_REQUESTED = "payout_requested"
    PAYOUT_COMPLETED = "payout_completed"
    # Template Marketplace
    TEMPLATE_PUBLISHED = "template_published"
    TEMPLATE_UNPUBLISHED = "template_unpublished"
    TEMPLATE_DELETED = "template_deleted"
    # Webhook Events
    WEBHOOK_RECEIVED = "webhook_received"
    WEBHOOK_PROCESSED = "webhook_processed"
    WEBHOOK_FAILED = "webhook_failed"
    WEBHOOK_RETRY_SCHEDULED = "webhook_retry_scheduled"


class AuditLogDTO(BaseModel):
    """Audit log entry"""
    id: str

    # Actor
    actor_id: str
    actor_email: Optional[str] = None
    actor_role: Optional[str] = None

    # Action
    action: AuditAction
    resource_type: str  # user, template, workflow, etc.
    resource_id: Optional[str] = None

    # Details
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Timestamps
    created_at: datetime

    model_config = ConfigDict(use_enum_values=True)


class AuditLogCreateDTO(BaseModel):
    """DTO for creating an audit log entry"""
    actor_id: str
    actor_email: Optional[str] = None
    actor_role: Optional[str] = None
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
