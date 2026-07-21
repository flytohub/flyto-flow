"""
Lineage API Models

Pydantic models for lineage API requests and responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class LineageNode(BaseModel):
    """A node in the lineage graph"""
    id: str
    type: str  # 'step', 'variable', 'input', 'output', 'state', 'group'
    label: str
    step_id: Optional[str] = None
    variable_name: Optional[str] = None
    data_type: Optional[str] = None
    value_preview: Optional[str] = None
    # New fields for swimlane view
    lane: Optional[str] = None  # 'source', 'transform', 'sink'
    module_id: Optional[str] = None
    category: Optional[str] = None  # 'browser', 'data', 'flow', 'ai', 'http'
    is_control_flow: bool = False  # loop, if, retry
    loop_count: Optional[int] = None
    group_children: Optional[List[str]] = None  # For grouped nodes
    order: Optional[int] = None  # Execution order for sorting
    # Diagnostic fields
    consumed_variables: Optional[List[str]] = None  # Variables this step reads
    produced_variables: Optional[List[str]] = None  # Variables this step writes
    status: Optional[str] = None  # 'success', 'failed', 'skipped'
    error: Optional[str] = None  # Error message if failed


class LineageEdge(BaseModel):
    """An edge in the lineage graph"""
    source: str
    target: str
    label: Optional[str] = None
    edge_type: str = "data_flow"  # 'data_flow', 'data_dependency', 'control_flow'
    is_control_flow: bool = False


class LineageGraphResponse(BaseModel):
    """Full lineage graph response"""
    execution_id: str
    nodes: List[LineageNode]
    edges: List[LineageEdge]
    step_count: int
    variable_count: int


class SwimlaneViewResponse(BaseModel):
    """Swimlane view for Lineage (Sources | Transforms | Sinks)"""
    execution_id: str
    sources: List[LineageNode]
    transforms: List[LineageNode]
    sinks: List[LineageNode]
    data_edges: List[LineageEdge]  # Only data dependency edges
    state_nodes: List[LineageNode]  # Browser session, page state etc.
    groups: List[LineageNode]  # Collapsed loop/group nodes


class StepLineageResponse(BaseModel):
    """Step-specific lineage"""
    step_id: str
    module_id: Optional[str] = None
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    consumed_variables: List[str]
    produced_variables: List[str]
    upstream_steps: List[str]
    downstream_steps: List[str]


class VariableLineageResponse(BaseModel):
    """Variable tracing response"""
    variable_name: str
    origin_step: Optional[str] = None
    current_value: Any = None
    history: List[Dict[str, Any]]
    consumed_by: List[str]


class ItemOriginResponse(BaseModel):
    """Item-level origin information"""
    node_id: str
    port_id: str
    index: Optional[int] = None
    key_path: Optional[str] = None
    timestamp: Optional[str] = None
    transform_chain: List[str] = []


class TrackedOutputResponse(BaseModel):
    """Tracked output with item-level lineage"""
    step_id: str
    port_id: str
    value_type: str
    value_preview: str
    is_array: bool
    item_count: Optional[int] = None
    origin: Optional[ItemOriginResponse] = None
    transform_chain: List[str] = []
    item_origins: Optional[List[ItemOriginResponse]] = None


class ItemLevelLineageResponse(BaseModel):
    """Full item-level lineage for an execution"""
    execution_id: str
    tracked_outputs: List[TrackedOutputResponse]
    total_items_tracked: int
