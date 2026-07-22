"""Local CE workflow API.

Functionality is split into:
- models.py - Pydantic request/response models
- validation.py - Connection validation
- websocket.py - WebSocket connection management
- crud.py - CRUD operations
- execution.py - Execution endpoints
"""

from fastapi import APIRouter

from api.workflows import crud, execution

# Local router: conversion + run + websocket.
local_router = APIRouter()
local_router.include_router(crud.conversion_router)
local_router.include_router(execution.run_router)

router = local_router

# Re-exports for backwards compatibility
from api.workflows.models import (
    NodeCreate,
    EdgeCreate,
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowRunRequest,
)
from api.workflows.validation import validate_workflow_connections_for_api
from services.websocket_manager import ConnectionManager, manager, get_connection_manager

__all__ = [
    "router",
    "NodeCreate",
    "EdgeCreate",
    "WorkflowCreate",
    "WorkflowUpdate",
    "WorkflowRunRequest",
    "validate_workflow_connections_for_api",
    "ConnectionManager",
    "manager",
    "get_connection_manager",
]
