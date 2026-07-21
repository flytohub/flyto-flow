"""
Pydantic models for the Triggers API.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Schedule Models
# ============================================================================


class CreateScheduleRequest(BaseModel):
    """Request to create a schedule."""

    name: str = Field(..., min_length=1, max_length=100)
    workflow_id: str
    workspace_id: str = Field(..., min_length=1)  # Required for Cloud Functions routing
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    timezone: str = "UTC"
    description: Optional[str] = None


class UpdateScheduleRequest(BaseModel):
    """Request to update a schedule."""

    name: Optional[str] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    inputs: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    description: Optional[str] = None


class ScheduleResponse(BaseModel):
    """Schedule response."""

    id: str
    name: str
    workflow_id: str
    workspace_id: Optional[str]
    cron_expression: Optional[str]
    interval_seconds: Optional[int]
    timezone: str
    status: str
    inputs: Dict[str, Any]
    next_run_at: Optional[str]
    last_run_at: Optional[str]
    run_count: int
    failure_count: int
    description: Optional[str]
    created_at: str
    updated_at: str


# ============================================================================
# Webhook Models
# ============================================================================


class CreateWebhookRequest(BaseModel):
    """Request to create a webhook."""

    name: str = Field(..., min_length=1, max_length=100)
    workflow_id: str
    workspace_id: str = Field(..., min_length=1)  # Required for Cloud Functions routing
    inputs_mapping: Dict[str, str] = Field(default_factory=dict)
    require_signature: bool = True
    allowed_ips: List[str] = Field(default_factory=list)
    provider: Optional[str] = Field(None, description="Provider: github, stripe, generic")
    description: Optional[str] = None


class WebhookResponse(BaseModel):
    """Webhook response."""

    id: str
    name: str
    workflow_id: str
    workspace_id: Optional[str]
    status: str
    inputs_mapping: Dict[str, str]
    require_signature: bool
    allowed_ips: List[str]
    provider: Optional[str]
    trigger_count: int
    last_triggered_at: Optional[str]
    description: Optional[str]
    created_at: str
    updated_at: str
    # URL for triggering
    trigger_url: Optional[str] = None  # Local backend URL


class WebhookWithSecretResponse(WebhookResponse):
    """Webhook response including secret (only on create)."""

    secret: str


# ============================================================================
# Utility Models
# ============================================================================


class CronValidateRequest(BaseModel):
    """Request to validate a cron expression."""
    expression: str = Field(..., min_length=1, max_length=100)
