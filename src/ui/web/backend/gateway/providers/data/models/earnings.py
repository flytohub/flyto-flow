"""Earnings DTO Models"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict


class EarningStatus(str, Enum):
    """Earning status"""
    PENDING = "pending"
    AVAILABLE = "available"
    PAID = "paid"
    REFUNDED = "refunded"


class EarningDTO(BaseModel):
    """Creator earning record"""
    id: str
    creator_id: str

    # Transaction
    purchase_id: str
    template_id: str
    buyer_id: str

    # Amount
    gross_amount: int  # cents
    platform_fee: int  # cents
    net_amount: int  # cents
    available_amount: Optional[int] = None  # cents remaining for payout
    paid_amount: Optional[int] = None  # cents allocated to payouts
    currency: str = "usd"

    # Status
    status: EarningStatus

    # Payout
    payout_id: Optional[str] = None
    paid_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class EarningsSummaryDTO(BaseModel):
    """Creator earnings summary"""
    total_earnings: int = 0  # cents (net to creator)
    available_balance: int = 0  # cents
    pending_balance: int = 0  # cents
    paid_out: int = 0  # cents
    total_sales: int = 0  # cents (gross of all sales)
    total_platform_fees: int = 0  # cents
    sales_count: int = 0  # number of earning records
    currency: str = "usd"


class PayoutDTO(BaseModel):
    """Payout record"""
    id: str
    creator_id: str

    # Amount
    amount: int  # cents
    currency: str = "usd"

    # Status
    status: str  # pending, processing, completed, failed
    stripe_payout_id: Optional[str] = None

    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime] = None
