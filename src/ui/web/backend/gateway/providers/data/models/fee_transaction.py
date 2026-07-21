"""Fee Transaction DTO Models

Detailed transaction records for tax compliance and audit purposes.
Records all fee calculations with breakdown for legal/tax requirements.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class TransactionType(str, Enum):
    """Transaction type"""
    PURCHASE = "purchase"
    REFUND = "refund"
    PAYOUT = "payout"
    FEE_ADJUSTMENT = "fee_adjustment"


class TransactionStatus(str, Enum):
    """Transaction status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class FeeTransactionDTO(BaseModel):
    """
    Detailed fee transaction record for audit/tax compliance.

    Contains complete breakdown of:
    - Gross amount (what buyer paid)
    - Platform fee (what platform keeps)
    - Net earnings (what creator receives)
    - Stripe fees (payment processor fees)
    """
    id: str

    # Transaction identifiers
    transaction_type: TransactionType
    status: TransactionStatus

    # Related entities
    purchase_id: Optional[str] = None
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    buyer_id: Optional[str] = None
    buyer_email: Optional[str] = None
    creator_id: Optional[str] = None
    creator_email: Optional[str] = None

    # Financial breakdown (all in cents for precision)
    gross_amount: int = 0  # Total paid by buyer
    currency: str = "usd"

    # Platform fee calculation
    platform_fee_percent: float = 0.0  # e.g., 0.15 for 15%
    platform_fee_amount: int = 0  # Calculated platform fee

    # Stripe fees (estimated, actual comes from Stripe)
    stripe_fee_percent: float = 0.029  # 2.9%
    stripe_fee_fixed: int = 30  # 30 cents
    stripe_fee_amount: int = 0  # Calculated Stripe fee

    # Net calculations
    net_after_stripe: int = 0  # Gross - Stripe fees
    creator_earnings: int = 0  # What creator receives

    # Stripe references
    stripe_payment_intent: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    stripe_transfer_id: Optional[str] = None
    stripe_session_id: Optional[str] = None

    # Regional/tax info
    buyer_region: Optional[str] = None
    buyer_country: Optional[str] = None
    tax_amount: int = 0
    tax_rate: float = 0.0

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class FeeTransactionCreateDTO(BaseModel):
    """DTO for creating a fee transaction record"""
    transaction_type: TransactionType
    purchase_id: Optional[str] = None
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    buyer_id: Optional[str] = None
    buyer_email: Optional[str] = None
    creator_id: Optional[str] = None
    creator_email: Optional[str] = None
    gross_amount: int = 0
    currency: str = "usd"
    platform_fee_percent: float = 0.15
    stripe_payment_intent: Optional[str] = None
    stripe_session_id: Optional[str] = None
    buyer_region: Optional[str] = None
    buyer_country: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeeCalculation:
    """
    Fee calculation utility.

    Calculates all fees with proper rounding for financial accuracy.
    """

    @staticmethod
    def calculate(
        gross_amount: int,
        platform_fee_percent: float = 0.15,
        stripe_fee_percent: float = 0.029,
        stripe_fee_fixed: int = 30,
    ) -> Dict[str, int]:
        """
        Calculate fee breakdown.

        Args:
            gross_amount: Total amount in cents
            platform_fee_percent: Platform fee percentage (0.15 = 15%)
            stripe_fee_percent: Stripe fee percentage (0.029 = 2.9%)
            stripe_fee_fixed: Stripe fixed fee in cents (30 = $0.30)

        Returns:
            Dict with calculated amounts
        """
        # Stripe fee calculation (2.9% + 30 cents)
        stripe_fee = int(gross_amount * stripe_fee_percent) + stripe_fee_fixed

        # Net after Stripe fees
        net_after_stripe = gross_amount - stripe_fee

        # Platform fee on gross amount
        platform_fee = int(gross_amount * platform_fee_percent)

        # Creator earnings (gross - platform fee)
        # Note: Stripe fees come out of platform's share or are handled separately
        creator_earnings = gross_amount - platform_fee

        return {
            "gross_amount": gross_amount,
            "stripe_fee_amount": stripe_fee,
            "net_after_stripe": net_after_stripe,
            "platform_fee_amount": platform_fee,
            "creator_earnings": creator_earnings,
        }
