"""
LINE Bot API Models

Pydantic models for LINE webhook events and responses.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# =============================================================================
# LINE Webhook Event Models
# =============================================================================

class LineSource(BaseModel):
    """LINE event source (user, group, or room)"""
    type: Literal["user", "group", "room"]
    userId: Optional[str] = None
    groupId: Optional[str] = None
    roomId: Optional[str] = None


class LineMessage(BaseModel):
    """LINE message content"""
    id: str
    type: str  # text, image, video, audio, file, location, sticker
    text: Optional[str] = None
    # For other message types
    fileName: Optional[str] = None
    fileSize: Optional[int] = None
    title: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    packageId: Optional[str] = None
    stickerId: Optional[str] = None


class LinePostback(BaseModel):
    """LINE postback data"""
    data: str
    params: Optional[Dict[str, str]] = None


class LineEvent(BaseModel):
    """LINE webhook event"""
    type: str  # message, postback, follow, unfollow, join, leave, etc.
    timestamp: int
    source: LineSource
    replyToken: Optional[str] = None
    message: Optional[LineMessage] = None
    postback: Optional[LinePostback] = None


class LineWebhookRequest(BaseModel):
    """LINE webhook request body"""
    destination: str
    events: List[LineEvent]


# =============================================================================
# Firestore Message Models
# =============================================================================

class FirestoreMessage(BaseModel):
    """Message stored in Firestore for desktop app to process"""
    user_id: str
    reply_token: Optional[str] = None
    type: str  # text, image, postback, etc.
    content: Any  # Text string or message object
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["pending", "processing", "done", "expired"] = "pending"
    processed_by: Optional[str] = None
    reply_token_expires_at: Optional[datetime] = None

    # User info (cached from LINE profile)
    user_display_name: Optional[str] = None
    user_picture_url: Optional[str] = None


class FirestoreResponse(BaseModel):
    """Response to send back to LINE (written by desktop app)"""
    user_id: str
    reply_token: Optional[str] = None
    message_id: Optional[str] = None  # Reference to original message
    content: Dict[str, Any]  # text, imageUrl, flex, etc.
    status: Literal["pending", "sent", "failed"] = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None


# =============================================================================
# API Request/Response Models
# =============================================================================

class LineReplyRequest(BaseModel):
    """Request to send LINE reply (from desktop app)"""
    user_id: str
    reply_token: Optional[str] = None  # If available (within 30s)
    messages: List[Dict[str, Any]]  # LINE message objects


class LineReplyResponse(BaseModel):
    """Response from LINE reply endpoint"""
    ok: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class LinePushRequest(BaseModel):
    """Request to push LINE message (no reply token needed)"""
    user_id: str
    messages: List[Dict[str, Any]]


class LineMessageStatus(BaseModel):
    """Status of a message in the queue"""
    message_id: str
    user_id: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    content_preview: Optional[str] = None
