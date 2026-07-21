"""Execution DTO Models"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class ExecutionStatus(str, Enum):
    """Execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionDTO(BaseModel):
    """Workflow execution record"""
    id: str
    workflow_id: str
    user_id: str

    status: ExecutionStatus

    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    input_params: Dict[str, Any] = Field(default_factory=dict)
    result_data: Optional[Dict[str, Any]] = None

    logs: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None
    error_node_id: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)
