"""Payment DTO Models"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CheckoutSessionDTO(BaseModel):
    """Stripe checkout session"""
    session_id: str
    session_url: str
    expires_at: datetime


class PayoutSettingsDTO(BaseModel):
    """Creator payout settings"""
    user_id: str

    # Stripe Connect
    stripe_account_id: Optional[str] = None
    stripe_account_status: Optional[str] = None  # pending, verified, restricted

    # Bank info (masked)
    bank_name: Optional[str] = None
    bank_last4: Optional[str] = None

    # Status
    payouts_enabled: bool = False
    charges_enabled: bool = False

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PayoutSettingsUpdateDTO(BaseModel):
    """DTO for updating payout settings"""
    country: Optional[str] = None
    # Other fields come from Stripe Connect onboarding
