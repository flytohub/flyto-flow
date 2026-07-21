"""Subscription DTO Models"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict


class SubscriptionPlan(str, Enum):
    """Subscription plan types"""
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    OFFLINE = "offline"  # One-time purchase offline license
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class SubscriptionDTO(BaseModel):
    """User subscription"""
    id: str
    user_id: str

    # Plan
    plan: SubscriptionPlan
    status: SubscriptionStatus

    # Billing
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None

    # Period
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False

    # Trial
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class SubscriptionCreateDTO(BaseModel):
    """DTO for creating a subscription"""
    plan: SubscriptionPlan
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    trial_days: int = 0
