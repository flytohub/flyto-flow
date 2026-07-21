"""
Workflow API

Unified workflow management API using gateway providers.
Works across all deployment modes (Cloud/Enterprise/Offline).

All functionality has been split into:
- models.py - Pydantic request/response models
- validation.py - Connection validation
- websocket.py - WebSocket connection management
- crud.py - CRUD operations
- execution.py - Execution endpoints
"""

from fastapi import APIRouter

from api.workflows import crud, execution, websocket

# Local router: conversion + run + websocket (no Firebase needed)
local_router = APIRouter()
local_router.include_router(crud.conversion_router)
local_router.include_router(execution.run_router)
local_router.include_router(websocket.router)

# Full router: all endpoints (for cloud + dev mode)
router = APIRouter()
router.include_router(crud.router)
router.include_router(execution.router)
router.include_router(websocket.router)

# Re-exports for backwards compatibility
from api.workflows.models import (
    NodeCreate,
    EdgeCreate,
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowRunRequest,
)
from api.workflows.validation import validate_workflow_connections_for_api
from api.workflows.websocket import ConnectionManager, manager, get_connection_manager

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
