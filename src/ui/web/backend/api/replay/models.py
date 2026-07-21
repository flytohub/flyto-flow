"""
Replay API Models

Pydantic request/response models for the replay API.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReplayValidateRequest(BaseModel):
    """Request to validate replay feasibility"""
    execution_id: str
    step_id: str
    end_step_id: Optional[str] = None
    skip_steps: List[str] = Field(default_factory=list)


class ReplayExecuteRequest(BaseModel):
    """Request to execute a replay"""
    execution_id: str
    step_id: Optional[str] = None  # None = full replay
    end_step_id: Optional[str] = None
    modified_context: Dict[str, Any] = Field(default_factory=dict)
    skip_steps: List[str] = Field(default_factory=list)
    breakpoints: List[str] = Field(default_factory=list)
    dry_run: bool = False


class SingleStepReplayRequest(BaseModel):
    """Request to replay a single step"""
    execution_id: str
    step_id: str
    modified_params: Dict[str, Any] = Field(default_factory=dict)
    modified_context: Dict[str, Any] = Field(default_factory=dict)


class CompareRequest(BaseModel):
    """Request to compare executions"""
    original_execution_id: str
    replay_execution_id: str


class ReplayResult(BaseModel):
    """Replay execution result"""
    ok: bool
    replay_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    steps_executed: int = 0
    context: Dict[str, Any] = Field(default_factory=dict)
