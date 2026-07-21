"""
Workflow API Models

Pydantic request/response models for workflow endpoints.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Dict, List, Optional, Any


ALLOWED_SCREENSHOT_MODES = {"off", "on_error", "all"}
MAX_RUN_BREAKPOINTS = 100
ResourceRef = str | List[str]


class NodeCreate(BaseModel):
    """Request model for creating a workflow node."""
    id: Optional[str] = None  # Optional client-provided ID; server generates node_{i} if absent
    node_type: str
    module_id: str = Field(..., alias="action")  # Accept both action and module_id
    label: str
    params: Dict[str, Any] = Field(default_factory=dict, alias="config")  # Accept both config and params
    position_x: int = 0
    position_y: int = 0
    order_index: int = 0
    # Advanced fields
    when: Optional[str] = None
    on_error: Optional[str] = None
    retry: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    parallel: Optional[bool] = None
    foreach: Optional[str] = None
    as_: Optional[str] = Field(None, alias="as")
    description: Optional[str] = None
    output: Optional[str] = None
    connections: Optional[Dict[str, List[str]]] = None
    resources: Optional[Dict[str, ResourceRef]] = None
    pinned_output: Optional[Any] = None

    @model_validator(mode='before')
    @classmethod
    def check_params_config_conflict(cls, data):
        """Reject requests that send both params and config to avoid ambiguity."""
        if isinstance(data, dict):
            has_params = 'params' in data and data['params'] is not None
            has_config = 'config' in data and data['config'] is not None
            if has_params and has_config:
                raise ValueError("Cannot specify both 'params' and 'config'. Use only one.")
        return data

    model_config = ConfigDict(populate_by_name=True)


class EdgeCreate(BaseModel):
    """Request model for creating a workflow edge."""
    source_node_id: str
    target_node_id: str
    condition: str = "always"
    label: Optional[str] = None
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class WorkflowCreate(BaseModel):
    """Request model for creating a workflow."""
    name: str
    description: Optional[str] = None
    mode: str = "manual"
    trigger_type: Optional[str] = "manual"
    trigger_config: Optional[Dict[str, Any]] = None
    nodes: List[NodeCreate] = []
    edges: List[EdgeCreate] = []
    tags: List[str] = []


class NodeUpdate(BaseModel):
    """Node for workflow update - includes position"""
    id: str
    node_type: Optional[str] = None
    module_id: Optional[str] = Field(default=None, alias="action")  # Accept both action and module_id
    label: Optional[str] = None
    params: Optional[Dict[str, Any]] = Field(default=None, alias="config")  # Accept both config and params
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    order_index: Optional[int] = None
    # Advanced fields
    when: Optional[str] = None
    on_error: Optional[str] = None
    retry: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    parallel: Optional[bool] = None
    foreach: Optional[str] = None
    as_: Optional[str] = Field(default=None, alias="as")
    description: Optional[str] = None
    output: Optional[str] = None
    connections: Optional[Dict[str, List[str]]] = None
    resources: Optional[Dict[str, ResourceRef]] = None
    pinned_output: Optional[Any] = None

    @model_validator(mode='before')
    @classmethod
    def check_params_config_conflict(cls, data):
        """Reject requests that send both params and config to avoid ambiguity."""
        if isinstance(data, dict):
            has_params = 'params' in data and data['params'] is not None
            has_config = 'config' in data and data['config'] is not None
            if has_params and has_config:
                raise ValueError("Cannot specify both 'params' and 'config'. Use only one.")
        return data

    model_config = ConfigDict(populate_by_name=True)


class EdgeUpdate(BaseModel):
    """Edge for workflow update"""
    id: str
    source_node_id: str
    target_node_id: str
    condition: Optional[str] = None
    label: Optional[str] = None
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class WorkflowUpdate(BaseModel):
    """Request model for updating a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    # Support updating workflow structure (including node positions)
    nodes: Optional[List[NodeUpdate]] = None
    edges: Optional[List[EdgeUpdate]] = None


class WorkflowRunRequest(BaseModel):
    """Request body for running workflow directly"""
    workflow_yaml: str = Field(alias="workflowYaml")
    params: Optional[Dict[str, Any]] = {}
    start_step: Optional[int] = Field(default=None, alias="startStep")
    end_step: Optional[int] = Field(default=None, alias="endStep")
    breakpoints: Optional[List[str]] = None  # Human Checkpoint node IDs
    screenshot_mode: Optional[str] = Field(default=None, alias="screenshotMode")

    @field_validator("start_step", "end_step")
    @classmethod
    def validate_step_index(cls, value):
        if value is not None and value < 0:
            raise ValueError("step index must be greater than or equal to 0")
        return value

    @field_validator("breakpoints")
    @classmethod
    def validate_breakpoints(cls, value):
        if value is None:
            return value
        if len(value) > MAX_RUN_BREAKPOINTS:
            raise ValueError(f"breakpoints cannot exceed {MAX_RUN_BREAKPOINTS} items")

        seen = set()
        for breakpoint in value:
            if not isinstance(breakpoint, str) or not breakpoint.strip():
                raise ValueError("breakpoints must be non-empty node IDs")
            if breakpoint in seen:
                raise ValueError(f"duplicate breakpoint: {breakpoint}")
            seen.add(breakpoint)
        return value

    @field_validator("screenshot_mode")
    @classmethod
    def validate_screenshot_mode(cls, value):
        if value is None:
            return value
        if value not in ALLOWED_SCREENSHOT_MODES:
            allowed = ", ".join(sorted(ALLOWED_SCREENSHOT_MODES))
            raise ValueError(f"screenshotMode must be one of: {allowed}")
        return value

    @model_validator(mode="after")
    def validate_step_range(self):
        if self.start_step is not None and self.end_step is not None and self.start_step > self.end_step:
            raise ValueError("startStep must be less than or equal to endStep")
        return self

    model_config = ConfigDict(populate_by_name=True)


class WorkflowNodeValidate(BaseModel):
    """Node for validation request"""
    id: str
    module_id: str
    node_type: Optional[str] = None
    label: Optional[str] = None
    params: Optional[Dict[str, Any]] = {}
    data: Optional[Dict[str, Any]] = None  # S-Grade: Full node data for sorting
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    ui_state: Optional[Dict[str, Any]] = None  # Persistent UI state (collapsed, etc.)


class WorkflowEdgeValidate(BaseModel):
    """Edge for validation request.

    Note: Frontend HTTP client converts camelCase → snake_case in requests,
    so sourceHandle arrives as source_handle. We accept both via aliases.
    """
    id: str
    source: str
    target: str
    type: Optional[str] = None  # 'loop' for loop-back edges
    sourceHandle: Optional[str] = Field(None, alias="source_handle")
    targetHandle: Optional[str] = Field(None, alias="target_handle")
    data: Optional[Dict[str, Any]] = None  # S-Grade: Edge metadata for edgeType detection

    model_config = ConfigDict(populate_by_name=True)


class WorkflowValidateRequest(BaseModel):
    """Request body for workflow validation"""
    nodes: List[WorkflowNodeValidate]
    edges: List[WorkflowEdgeValidate]
    has_loop: bool = False  # Flag indicating workflow contains loop modules


class WorkflowLayoutRequest(WorkflowValidateRequest):
    """Extended request for layout computation"""
    preset: Optional[str] = "default"   # default | compact | spacious
    direction: Optional[str] = "RIGHT"  # RIGHT | DOWN


class WorkflowStep(BaseModel):
    """Step for VueFlow conversion"""
    id: str
    module: Optional[str] = None
    type: Optional[str] = None  # Alternative to module
    label: Optional[str] = None
    params: Optional[Dict[str, Any]] = {}
    config: Optional[Dict[str, Any]] = None  # Alternative to params
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    connections: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, ResourceRef]] = None  # AI Agent sub-nodes
    description: Optional[str] = None
    output: Optional[str] = None
    when: Optional[str] = None
    on_error: Optional[str] = None
    retry: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    parallel: Optional[bool] = None
    foreach: Optional[str] = None
    as_: Optional[str] = Field(None, alias="as")

    model_config = ConfigDict(populate_by_name=True)


class StepsToVueFlowRequest(BaseModel):
    """Request body for converting steps to VueFlow format"""
    steps: List[WorkflowStep]


class VueFlowNode(BaseModel):
    """VueFlow node for conversion to backend steps"""
    id: str
    type: Optional[str] = "custom"
    position: Optional[Dict[str, float]] = None
    label: Optional[str] = None
    data: Optional[Dict[str, Any]] = {}


class VueFlowEdge(BaseModel):
    """VueFlow edge for conversion to backend steps.

    Note: Frontend HTTP client converts camelCase → snake_case in requests,
    so sourceHandle arrives as source_handle. We accept both via aliases.
    """
    model_config = {"populate_by_name": True}

    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = Field(None, alias="source_handle")
    targetHandle: Optional[str] = Field(None, alias="target_handle")
    type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    label: Optional[str] = None


class VueFlowToStepsRequest(BaseModel):
    """Request body for converting VueFlow elements to backend steps"""
    nodes: List[VueFlowNode]
    edges: List[VueFlowEdge] = []


class UIComponent(BaseModel):
    """UI component for schema preview"""
    id: str
    type: Optional[str] = None
    module: Optional[str] = None
    label: Optional[str] = None
    required: Optional[bool] = None
    default: Optional[Any] = None
    placeholder: Optional[str] = None
    options: Optional[List[Any]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    rows: Optional[int] = None
    accept: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class UISection(BaseModel):
    """UI section for schema preview"""
    id: Optional[str] = None
    columns_data: Optional[List[Dict[str, Any]]] = None


class SchemaPreviewRequest(BaseModel):
    """Request body for schema preview inference"""
    workflow_elements: List[VueFlowNode] = []
    ui_sections: List[UISection] = []
