"""
Execution API Package

Workflow execution endpoints organized by function:
- Basic: run, status, cancel, list, cleanup
- Control: pause, resume, step, run-to-end, state
- Recovery: resume-options, resume-from-checkpoint

API Routes:
    POST /api/executions/run - Start a new execution
    GET  /api/executions/{id} - Get execution status
    POST /api/executions/{id}/cancel - Cancel running execution
    GET  /api/executions - List all executions
    POST /api/executions/cleanup - Clean up old executions
    POST /api/executions/{id}/pause - Pause running execution
    POST /api/executions/{id}/resume - Resume paused execution
    POST /api/executions/{id}/step - Execute single step
    POST /api/executions/{id}/run-to-end - Run to completion
    GET  /api/executions/{id}/state - Get detailed state
    GET  /api/executions/{id}/resume-options - Get checkpoint list
    POST /api/executions/{id}/resume-from-checkpoint - Resume from checkpoint
"""

from fastapi import APIRouter

from api.executions.routes_basic import router as basic_router
from api.executions.routes_control import router as control_router
from api.executions.routes_recovery import router as recovery_router

# Main router that combines all sub-routers
router = APIRouter()
router.include_router(basic_router)
router.include_router(control_router)
router.include_router(recovery_router)

# Export models for external use
from api.executions.models import (
    RunWorkflowRequest,
    RunWorkflowResponse,
    ExecutionStatusResponse,
    CancelResponse,
    ExecutionListResponse,
    PauseResponse,
    ResumeResponse,
    StepResponse,
    RunToEndResponse,
    ExecutionStateResponse,
    CheckpointInfo,
    ResumeOptionsResponse,
    ResumeFromCheckpointRequest,
    ResumeFromCheckpointResponse,
)

__all__ = [
    "router",
    # Models
    "RunWorkflowRequest",
    "RunWorkflowResponse",
    "ExecutionStatusResponse",
    "CancelResponse",
    "ExecutionListResponse",
    "PauseResponse",
    "ResumeResponse",
    "StepResponse",
    "RunToEndResponse",
    "ExecutionStateResponse",
    "CheckpointInfo",
    "ResumeOptionsResponse",
    "ResumeFromCheckpointRequest",
    "ResumeFromCheckpointResponse",
]
