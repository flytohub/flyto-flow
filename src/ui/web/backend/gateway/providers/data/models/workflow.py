"""Workflow DTO Models"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

from gateway.providers.data.models.common import DataSource


ResourceRef = str | List[str]


class TriggerType(str, Enum):
    """Workflow trigger types"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    EVENT = "event"


class WorkflowNode(BaseModel):
    """Workflow node (step)"""
    id: str
    node_type: str
    module_id: str = Field(..., alias="action")  # Accept both action and module_id
    label: str
    params: Dict[str, Any] = Field(default_factory=dict, alias="config")  # Accept both config and params
    position_x: int = 0
    position_y: int = 0
    order_index: int = 0
    # Advanced fields for workflow execution control
    when: Optional[str] = None  # Execution condition
    on_error: Optional[str] = None  # Error handling strategy
    retry: Optional[Dict[str, Any]] = None  # Retry configuration
    timeout: Optional[int] = None  # Timeout in seconds
    parallel: Optional[bool] = None  # Parallel execution flag
    foreach: Optional[str] = None  # Loop iteration expression
    as_: Optional[str] = Field(None, alias="as")  # Loop variable name ('as' is reserved)
    description: Optional[str] = None  # Step description
    output: Optional[str] = None  # Output mapping expression
    connections: Optional[Dict[str, List[str]]] = None  # Control flow connections (Loop/Branch/Switch)
    resources: Optional[Dict[str, ResourceRef]] = None  # AI Agent sub-nodes (model/memory/tools)
    pinned_output: Optional[Any] = None  # Data pinning for testing

    model_config = ConfigDict(populate_by_name=True)


class WorkflowEdge(BaseModel):
    """Connection between nodes"""
    id: str
    source_node_id: str
    target_node_id: str
    condition: str = "always"
    label: Optional[str] = None
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class WorkflowDTO(BaseModel):
    """
    Unified Workflow DTO

    All providers must map their data to this structure.
    """
    # Identity
    id: str
    user_id: str

    # Basic info
    name: str
    description: Optional[str] = None

    # Status
    is_active: bool = True

    # Trigger
    trigger_type: TriggerType = TriggerType.MANUAL
    trigger_config: Optional[Dict[str, Any]] = None

    # Statistics
    total_executions: int = 0
    success_count: int = 0
    failed_count: int = 0

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_executed_at: Optional[datetime] = None

    # Graph structure (optional - only when fetching full workflow)
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None

    # Metadata
    source: DataSource = DataSource.USER
    tags: List[str] = Field(default_factory=list)

    # Capabilities (what can user do with this workflow)
    capabilities: Dict[str, bool] = Field(default_factory=lambda: {
        "execute": True,
        "edit": True,
        "delete": True,
        "share": False,
        "publish": False,
    })

    # Error handling: workflow to trigger on failure
    error_workflow_id: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


class WorkflowCreateDTO(BaseModel):
    """DTO for creating a workflow"""
    name: str
    description: Optional[str] = None
    trigger_type: TriggerType = TriggerType.MANUAL
    trigger_config: Optional[Dict[str, Any]] = None
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class WorkflowUpdateDTO(BaseModel):
    """DTO for updating a workflow"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    trigger_type: Optional[TriggerType] = None
    trigger_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    error_workflow_id: Optional[str] = None
    # Support updating workflow structure (including node positions)
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
