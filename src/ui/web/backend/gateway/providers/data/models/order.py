"""Order DTO Models"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict


class OrderStatus(str, Enum):
    """Order status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class OrderDTO(BaseModel):
    """Custom order"""
    id: str

    # Parties
    buyer_id: str
    seller_id: str

    # Order info
    title: str
    description: str
    requirements: Optional[str] = None

    # Pricing
    amount: int  # cents
    currency: str = "usd"

    # Status
    status: OrderStatus = OrderStatus.PENDING

    # Deliverables
    deliverable_url: Optional[str] = None
    deliverable_notes: Optional[str] = None
    delivered_at: Optional[datetime] = None

    # Payment
    payment_intent_id: Optional[str] = None
    paid_at: Optional[datetime] = None

    # Dates
    deadline: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Cancellation
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None

    # Conversation
    conversation_id: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class OrderCreateDTO(BaseModel):
    """DTO for creating an order"""
    seller_id: str
    title: str
    description: str
    requirements: Optional[str] = None
    amount: int  # cents
    currency: str = "usd"
    deadline: Optional[datetime] = None


class OrderUpdateDTO(BaseModel):
    """DTO for updating an order"""
    status: Optional[OrderStatus] = None
    requirements: Optional[str] = None
    deadline: Optional[datetime] = None
    deliverable_url: Optional[str] = None
    deliverable_notes: Optional[str] = None
