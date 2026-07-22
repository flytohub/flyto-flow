"""
Canonical Module Schema v2.0

Defines the unified module format that all sources (atomic, composite, template,
and plugin modules must convert to before being sent to the frontend.

This is the single source of truth for module data structure.
Frontend receives this format and renders it directly without transformation.

Design Principles:
1. Backend is single source of truth - frontend just renders
2. All field names use camelCase exclusively
3. ~40 essential fields, organized by clear categories
4. Pre-computed values (defaultParams, icon objects) reduce frontend work

v2.0 Changes:
- Removed snake_case aliases (INCLUDE_SNAKE_CASE_ALIASES = False)
- Simplified from 320+ fields to ~40 essential fields
- Unified icon format: { type: 'lucide'|'url', value: str }
- Clear category structure: Core, Display, Schema, Connection, Node, Execution, Source
"""

from typing import TypedDict, Optional, List, Dict, Any, Literal, Union


# Feature flag - set to False to use new slim schema
# Set to True for backward compatibility during migration
INCLUDE_SNAKE_CASE_ALIASES = False


# Source types for module origin tracking
SourceType = Literal["atomic", "composite", "plugin", "template"]

# Node types for special rendering
NodeType = Literal[
    "standard", "branch", "switch", "loop", "container", "merge", "fork", "join",
    "subflow", "trigger", "start", "end", "error_trigger", "code", "http",
    "llm_chain", "vector_store", "ai_agent", "composite", "template", "ai"
]


class IconSpec(TypedDict, total=False):
    """
    Unified icon representation.

    Examples:
        {"type": "lucide", "value": "Package"}
        {"type": "url", "value": "https://..."}
    """
    type: Literal["lucide", "url"]
    value: str


class ParamProperty(TypedDict, total=False):
    """Single parameter property definition (JSON Schema subset)."""
    type: str  # string, number, boolean, array, object
    label: str
    description: Optional[str]
    placeholder: Optional[str]
    default: Any
    required: bool
    hidden: bool
    options: Optional[List[Dict[str, str]]]  # for select/radio
    enum: Optional[List[str]]
    minimum: Optional[float]
    maximum: Optional[float]
    minLength: Optional[int]
    maxLength: Optional[int]
    format: Optional[str]  # email, uri, date-time, path, password, color, etc.
    items: Optional[Dict[str, Any]]  # array item schema (recursive)
    minItems: Optional[int]
    maxItems: Optional[int]
    step: Optional[float]
    pathMode: Optional[str]
    displayOptions: Optional[Dict[str, Any]]
    showWhen: Optional[Dict[str, Any]]
    widget: Optional[str]
    ui: Optional[Dict[str, Any]]  # full UI config (widget, element_types, etc.)
    visibility: Optional[str]
    advanced: Optional[bool]
    properties: Optional[Dict[str, Any]]
    pattern: Optional[str]


class ParamsSchema(TypedDict, total=False):
    """Parameter schema (JSON Schema subset)."""
    type: Literal["object"]
    properties: Dict[str, ParamProperty]
    required: Optional[List[str]]


class HandleConfig(TypedDict, total=False):
    """React Flow handle configuration."""
    id: str
    position: Literal["left", "right", "top", "bottom"]
    color: str
    labelKey: Optional[str]
    type: Optional[str]  # resource, data, control
    maxConnections: Optional[int]


class PortConfig(TypedDict, total=False):
    """Node port configuration for workflow connections."""
    id: str
    handleId: Optional[str]       # Vue Flow handle ID (for UI derivation)
    position: Optional[str]       # left/right/top/bottom
    label: str
    labelKey: Optional[str]
    dataType: str
    edgeType: Optional[str]  # data, control, resource
    maxConnections: Optional[int]
    required: Optional[bool]
    event: Optional[str]  # For event-based ports (error, etc.)
    color: Optional[str]


class UIConfig(TypedDict, total=False):
    """Node UI configuration for frontend rendering."""
    styleClass: str
    isFlowControl: bool
    showAddButton: bool
    paramsComponent: Optional[str]
    isLoop: Optional[bool]
    isContainer: Optional[bool]
    isTrigger: Optional[bool]
    isEntryPoint: Optional[bool]
    isTerminal: Optional[bool]
    isAgent: Optional[bool]
    isCode: Optional[bool]
    isMerge: Optional[bool]
    isFork: Optional[bool]
    isJoin: Optional[bool]
    isSubflow: Optional[bool]


class DynamicHandlesConfig(TypedDict, total=False):
    """Configuration for dynamic handles (switch/fork nodes)."""
    fromParam: str
    position: str
    idPrefix: str
    colors: List[str]
    stableKeyField: Optional[str]


class EntrypointConfig(TypedDict, total=False):
    """Entrypoint configuration for module execution."""
    type: str  # template, plugin, composite
    templateId: Optional[str]
    pluginId: Optional[str]
    runtime: str


class SourceData(TypedDict, total=False):
    """Source-specific data that varies by module type."""
    # Template-specific
    templateId: Optional[str]
    libraryId: Optional[str]
    steps: Optional[List[Dict[str, Any]]]
    stepsCount: Optional[int]
    canStartWorkflow: Optional[bool]
    sideEffects: Optional[List[str]]
    provides: Optional[List[str]]
    consumes: Optional[List[str]]
    entrypoint: Optional[EntrypointConfig]
    ui: Optional[Dict[str, Any]]  # UI config with sections

    # Plugin-specific
    pluginId: Optional[str]
    runtime: Optional[str]

    # Composite-specific
    stepCount: Optional[int]



class CanonicalModule(TypedDict, total=False):
    """
    Unified module format v2.0 - ALL sources must convert to this format.

    This is the ONLY format sent to frontend. Frontend should:
    - NOT do any field transformation
    - NOT compute defaults from schema
    - NOT detect node types from module ID
    - Simply render what's provided

    ~40 essential fields organized by category:
    1. Core (identification)
    2. Display (visual properties)
    3. Schema (params and output)
    4. Connection (type compatibility)
    5. Node (rendering configuration)
    6. Execution (runtime settings)
    7. Source (origin-specific data)
    """

    # === CORE (Identification) - Required ===
    moduleId: str        # Unique module identifier (e.g., "string.uppercase", "template.invoke:abc123")
    label: str           # Human-readable name
    category: str        # Module category (e.g., "string", "browser", "my-templates")
    source: SourceType   # Where this module came from: atomic|composite|plugin|template

    # === DISPLAY (Visual) - Most required ===
    description: str                     # Description text
    icon: IconSpec                       # Icon: { type: 'lucide'|'url', value: str }
    color: str                           # Hex color (e.g., "#6366F1")
    group: str                           # UI group for categorization
    tier: str                            # featured, standard, toolkit, internal
    visibility: str                      # default, expert, hidden
    tags: Optional[List[str]]            # Searchable tags
    labelKey: Optional[str]              # i18n key for label
    descriptionKey: Optional[str]        # i18n key for description

    # === SCHEMA (Parameters) - Required ===
    paramsSchema: ParamsSchema           # Parameter schema (JSON Schema format)
    defaultParams: Dict[str, Any]        # Pre-computed default values
    outputSchema: Optional[Dict[str, Any]]  # Output schema

    # === CONNECTION (Type Compatibility) ===
    inputTypes: List[str]                # Accepted input types
    outputTypes: List[str]               # Produced output types
    canReceiveFrom: List[str]            # Module IDs that can connect to input
    canConnectTo: List[str]              # Module IDs this can connect to
    inputPorts: List[PortConfig]         # Input port definitions
    outputPorts: List[PortConfig]        # Output port definitions

    # === NODE (Rendering Configuration) ===
    nodeType: NodeType                   # Node type for rendering (branch, loop, etc.)
    uiConfig: UIConfig                   # UI configuration
    inputHandles: List[HandleConfig]     # React Flow input handles
    outputHandles: List[HandleConfig]    # React Flow output handles
    dynamicHandles: Optional[DynamicHandlesConfig]  # For switch/fork nodes
    loopTargets: Optional[List[str]]     # For loop nodes

    # === AI Agent Flags ===
    isAIModel: bool      # Can be used as AI Agent model
    isMemory: bool       # Can be used as AI Agent memory
    isTool: bool         # Can be used as AI Agent tool
    isTemplate: bool     # Is a template module

    # === UI Flags ===
    requiresCustomUI: bool  # Module needs custom parameter UI (not auto-generated from schema)

    # === EXECUTION (Runtime Settings) ===
    timeout: Optional[float]
    retryable: bool
    maxRetries: int
    concurrentSafe: bool
    requiresCredentials: bool
    requiredPermissions: List[str]
    requiredSecrets: Optional[List[str]]

    # === METADATA ===
    version: str
    stability: str       # stable, beta, alpha, deprecated
    author: Optional[str]
    docsUrl: Optional[str]
    deprecated: bool
    isVerified: bool
    isFeatured: bool

    # === SOURCE DATA (Origin-specific) ===
    sourceData: SourceData  # Contains templateId, pluginId, steps, etc. based on source type


def create_canonical_module(
    module_id: str,
    label: str,
    category: str,
    source: SourceType,
    **kwargs
) -> CanonicalModule:
    """
    Create a canonical module with required fields and sensible defaults.

    Args:
        module_id: Unique module identifier
        label: Human-readable name
        category: Module category
        source: Source type (atomic, composite, plugin, template)
        **kwargs: Additional fields to override defaults

    Returns:
        CanonicalModule with all fields populated
    """
    base: CanonicalModule = {
        # Core
        "moduleId": module_id,
        "label": label,
        "category": category,
        "source": source,

        # Display
        "description": kwargs.get("description", ""),
        "icon": kwargs.get("icon", {"type": "lucide", "value": "Package"}),
        "color": kwargs.get("color", "#6C757D"),
        "group": kwargs.get("group", category.title()),
        "tier": kwargs.get("tier", "standard"),
        "visibility": kwargs.get("visibility", "default"),
        "tags": kwargs.get("tags", []),
        "labelKey": kwargs.get("labelKey"),
        "descriptionKey": kwargs.get("descriptionKey"),

        # Schema
        "paramsSchema": kwargs.get("paramsSchema", {"type": "object", "properties": {}}),
        "defaultParams": kwargs.get("defaultParams", {}),
        "outputSchema": kwargs.get("outputSchema"),

        # Connection
        "inputTypes": kwargs.get("inputTypes", ["*"]),
        "outputTypes": kwargs.get("outputTypes", ["*"]),
        "canReceiveFrom": kwargs.get("canReceiveFrom", ["*"]),
        "canConnectTo": kwargs.get("canConnectTo", ["*"]),
        "inputPorts": kwargs.get("inputPorts", []),
        "outputPorts": kwargs.get("outputPorts", []),

        # Node
        "nodeType": kwargs.get("nodeType", "standard"),
        "uiConfig": kwargs.get("uiConfig", {}),
        "inputHandles": kwargs.get("inputHandles", []),
        "outputHandles": kwargs.get("outputHandles", []),
        "dynamicHandles": kwargs.get("dynamicHandles"),
        "loopTargets": kwargs.get("loopTargets"),

        # AI flags
        "isAIModel": kwargs.get("isAIModel", False),
        "isMemory": kwargs.get("isMemory", False),
        "isTool": kwargs.get("isTool", False),
        "isTemplate": kwargs.get("isTemplate", False),

        # UI flags
        "requiresCustomUI": kwargs.get("requiresCustomUI", False),

        # Execution
        "timeout": kwargs.get("timeout"),
        "retryable": kwargs.get("retryable", False),
        "maxRetries": kwargs.get("maxRetries", 3),
        "concurrentSafe": kwargs.get("concurrentSafe", True),
        "requiresCredentials": kwargs.get("requiresCredentials", False),
        "requiredPermissions": kwargs.get("requiredPermissions", []),
        "requiredSecrets": kwargs.get("requiredSecrets"),

        # Metadata
        "version": kwargs.get("version", "1.0.0"),
        "stability": kwargs.get("stability", "stable"),
        "author": kwargs.get("author"),
        "docsUrl": kwargs.get("docsUrl"),
        "deprecated": kwargs.get("deprecated", False),
        "isVerified": kwargs.get("isVerified", False),
        "isFeatured": kwargs.get("isFeatured", False),

        # Source data
        "sourceData": kwargs.get("sourceData", {}),
    }

    return base


# Mapping of snake_case to camelCase field names (for migration utilities)
SNAKE_TO_CAMEL_MAPPING = {
    "module_id": "moduleId",
    "label_key": "labelKey",
    "description_key": "descriptionKey",
    "params_schema": "paramsSchema",
    "output_schema": "outputSchema",
    "input_types": "inputTypes",
    "output_types": "outputTypes",
    "can_receive_from": "canReceiveFrom",
    "can_connect_to": "canConnectTo",
    "input_ports": "inputPorts",
    "output_ports": "outputPorts",
    "dynamic_ports": "dynamicPorts",
    "node_type": "nodeType",
    "ui_config": "uiConfig",
    "input_handles": "inputHandles",
    "output_handles": "outputHandles",
    "dynamic_handles": "dynamicHandles",
    "loop_targets": "loopTargets",
    "max_retries": "maxRetries",
    "concurrent_safe": "concurrentSafe",
    "execution_environment": "executionEnvironment",
    "requires_credentials": "requiresCredentials",
    "handles_sensitive_data": "handlesSensitiveData",
    "required_permissions": "requiredPermissions",
    "required_secrets": "requiredSecrets",
    "requires_context": "requiresContext",
    "provides_context": "providesContext",
    "docs_url": "docsUrl",
    "deprecated_message": "deprecatedMessage",
    "ui_help": "uiHelp",
    "ui_help_key": "uiHelpKey",
    "input_type_labels": "inputTypeLabels",
    "input_type_descriptions": "inputTypeDescriptions",
    "output_type_labels": "outputTypeLabels",
    "output_type_descriptions": "outputTypeDescriptions",
    "suggested_predecessors": "suggestedPredecessors",
    "suggested_successors": "suggestedSuccessors",
    "connection_error_messages": "connectionErrorMessages",
    "template_id": "templateId",
    "library_id": "libraryId",
    "steps_count": "stepsCount",
    "can_start_workflow": "canStartWorkflow",
    "side_effects": "sideEffects",
    "step_count": "stepCount",
    "is_verified": "isVerified",
    "is_featured": "isFeatured",
    "plugin_id": "pluginId",
    "is_template": "isTemplate",
    "data_type": "dataType",
    "edge_type": "edgeType",
    "handle_id": "handleId",
    "max_connections": "maxConnections",
}


def convert_snake_to_camel(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert snake_case keys to camelCase.

    Use this to migrate old data format to new format.

    Args:
        data: Dict with potentially snake_case keys

    Returns:
        Dict with camelCase keys
    """
    result = {}
    for key, value in data.items():
        # Convert key
        new_key = SNAKE_TO_CAMEL_MAPPING.get(key, key)

        # Recursively convert nested dicts
        if isinstance(value, dict):
            value = convert_snake_to_camel(value)
        elif isinstance(value, list):
            value = [
                convert_snake_to_camel(item) if isinstance(item, dict) else item
                for item in value
            ]

        result[new_key] = value

    return result


def add_snake_case_aliases(module: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add snake_case alias fields to a module dict for backward compatibility.

    Only used when INCLUDE_SNAKE_CASE_ALIASES is True.

    Args:
        module: Module dict with camelCase fields

    Returns:
        Module dict with both camelCase and snake_case fields
    """
    if not INCLUDE_SNAKE_CASE_ALIASES:
        return module

    result = dict(module)

    # Add snake_case aliases
    camel_to_snake = {v: k for k, v in SNAKE_TO_CAMEL_MAPPING.items()}
    for camel, snake in camel_to_snake.items():
        if camel in result and snake not in result:
            result[snake] = result[camel]

    # Also add the 'id' field for backward compatibility
    if 'moduleId' in result and 'id' not in result:
        result['id'] = result['moduleId']
    if 'moduleId' in result and 'module_id' not in result:
        result['module_id'] = result['moduleId']
    if 'moduleId' in result and 'type' not in result:
        result['type'] = result['moduleId'].replace('.', '_')
    if 'source' in result and 'level' not in result:
        result['level'] = result['source']

    return result


def strip_snake_case_aliases(module: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove snake_case alias fields from a module dict.

    Use this to clean up modules when INCLUDE_SNAKE_CASE_ALIASES is False.

    Args:
        module: Module dict with both camelCase and snake_case fields

    Returns:
        Module dict with only camelCase fields
    """
    if INCLUDE_SNAKE_CASE_ALIASES:
        return module

    # Keys to remove
    snake_keys = set(SNAKE_TO_CAMEL_MAPPING.keys())
    # Also remove legacy alias keys
    legacy_keys = {'id', 'type', 'level'}

    return {
        key: value
        for key, value in module.items()
        if key not in snake_keys and key not in legacy_keys
    }


# ==============================================================================
# DEPRECATED: Legacy support - will be removed in future version
# ==============================================================================

def create_empty_canonical_module() -> Dict[str, Any]:
    """
    DEPRECATED: Use create_canonical_module() instead.

    Create an empty canonical module with all required default values.
    Kept for backward compatibility during migration.
    """
    return create_canonical_module(
        module_id="",
        label="",
        category="",
        source="atomic"
    )
