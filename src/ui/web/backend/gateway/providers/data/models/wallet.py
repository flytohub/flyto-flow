"""Wallet / Credits DTO Models"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CreditTransactionType(str, Enum):
    """Types of credit transactions."""
    TOPUP = "topup"
    SERIAL_CODE = "serial_code"
    TEMPLATE_CALL = "template_call"
    ADMIN_GRANT = "admin_grant"
    REFUND = "refund"


class CreditTransactionDTO(BaseModel):
    """A single credit transaction record."""
    id: str
    user_id: str
    type: CreditTransactionType
    amount: int  # positive = credit, negative = debit
    balance_after: int
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(use_enum_values=True)
