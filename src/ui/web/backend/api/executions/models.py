"""
Execution API Request/Response Models

Pydantic models for execution API endpoints.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# =============================================================================
# Basic Operations
# =============================================================================


class RunWorkflowRequest(BaseModel):
    """Request body for running a workflow."""
    workflow_yaml: str
    variables: Optional[Dict[str, Any]] = None
    workflow_id: Optional[str] = None
    screenshot_mode: Optional[str] = None  # "off", "on_error", "all"


class RunWorkflowResponse(BaseModel):
    """Response for run workflow."""
    ok: bool
    execution_id: str
    message: str


class ExecutionStatusResponse(BaseModel):
    """Response for execution status."""
    ok: bool
    execution: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CancelResponse(BaseModel):
    """Response for cancel execution."""
    ok: bool
    message: str


class ExecutionListResponse(BaseModel):
    """Response for listing executions."""
    ok: bool
    executions: Dict[str, Dict[str, Any]]


# =============================================================================
# Execution Control
# =============================================================================


class PauseResponse(BaseModel):
    """Response for pause execution."""
    ok: bool
    message: str


class ResumeResponse(BaseModel):
    """Response for resume execution."""
    ok: bool
    message: str


class StepResponse(BaseModel):
    """Response for step execution."""
    ok: bool
    message: str


class RunToEndResponse(BaseModel):
    """Response for run-to-end execution."""
    ok: bool
    message: str


class ExecutionStateResponse(BaseModel):
    """
    Response for execution state.

    Provides detailed runtime state for debugging and control UI.
    """
    ok: bool
    execution_id: str
    status: str
    current_node_id: Optional[str] = None
    current_step_index: int = 0
    total_steps: int = 0
    paused_at: Optional[str] = None
    pause_reason: Optional[str] = None
    variables: Dict[str, Any] = {}
    node_outputs: Dict[str, Any] = {}
    can_resume: bool = True
    can_step: bool = True
    error_message: Optional[str] = None


# =============================================================================
# Recovery/Checkpoint Resume
# =============================================================================


class CheckpointInfo(BaseModel):
    """Information about a checkpoint."""
    id: str
    type: str
    node_id: str
    node_index: int
    timestamp: str
    has_error: bool = False


class ResumeOptionsResponse(BaseModel):
    """Response for resume options."""
    ok: bool
    execution_id: str
    can_resume: bool
    checkpoints: List[CheckpointInfo] = []
    recommended_checkpoint: Optional[str] = None
    failure_node: Optional[str] = None
    failure_message: Optional[str] = None


class ResumeFromCheckpointRequest(BaseModel):
    """Request body for resuming from checkpoint."""
    checkpoint_id: Optional[str] = None
    modified_variables: Optional[Dict[str, Any]] = None


class ResumeFromCheckpointResponse(BaseModel):
    """Response for resume from checkpoint."""
    ok: bool
    new_execution_id: Optional[str] = None
    message: str
