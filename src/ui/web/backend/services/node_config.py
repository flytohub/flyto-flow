"""
Node Configuration Service
Provides UI configurations for different node types.

Handle derivation: Core ports are the single source of truth.
enrich_module_with_node_config() derives inputHandles/outputHandles from
inputPorts/outputPorts. NODE_TYPE_CONFIGS only stores ui_config (shape/flags).
"""
from typing import Dict, Any, List, Optional

# Case colors for switch/fork dynamic handles (matching frontend)
CASE_COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EC4899', '#8B5CF6', '#06B6D4', '#EF4444', '#84CC16']

# Node type configurations — dimensions + ui_config
# dimensions: {shape, width, height} — SSOT for layout engine + frontend rendering
NODE_TYPE_CONFIGS: Dict[str, Dict[str, Any]] = {
    'standard': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': '',
            'isFlowControl': False,
            'showAddButton': True,
            'paramsComponent': 'GenericParams'
        },
    },
    'branch': {
        'dimensions': {'shape': 'diamond', 'width': 76, 'height': 76},
        'ui_config': {
            'styleClass': 'branch-node',
            'isFlowControl': True,
            'showAddButton': True,
            'paramsComponent': 'FlowControlParams'
        },
    },
    'switch': {
        'dimensions': {'shape': 'diamond', 'width': 76, 'height': 76},
        'ui_config': {
            'styleClass': 'switch-node',
            'isFlowControl': True,
            'showAddButton': True,
            'paramsComponent': 'FlowControlParams'
        },
    },
    'loop': {
        'dimensions': {'shape': 'hexagon', 'width': 76, 'height': 76},
        'ui_config': {
            'styleClass': 'loop-node',
            'isFlowControl': True,
            'isLoop': True,
            'showAddButton': True,
            'paramsComponent': 'FlowControlParams'
        },
    },
    'container': {
        'dimensions': {'shape': 'container', 'width': 90, 'height': 90},
        'ui_config': {
            'styleClass': 'container-node',
            'isFlowControl': True,
            'isContainer': True,
            'showAddButton': True,
            'paramsComponent': 'GenericParams'
        },
    },
    'merge': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'merge-node',
            'isFlowControl': True,
            'isMerge': True,
            'showAddButton': True,
            'paramsComponent': 'FlowControlParams'
        },
    },
    'fork': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'fork-node',
            'isFlowControl': True,
            'isFork': True,
            'showAddButton': True,
            'paramsComponent': 'FlowControlParams'
        },
    },
    'join': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'join-node',
            'isFlowControl': True,
            'isJoin': True,
            'showAddButton': True,
            'paramsComponent': 'FlowControlParams'
        },
    },
    'subflow': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'subflow-node',
            'isFlowControl': True,
            'isSubflow': True,
            'showAddButton': True,
            'paramsComponent': 'GenericParams'
        },
    },
    'trigger': {
        'dimensions': {'shape': 'semicircle', 'width': 120, 'height': 76},
        'ui_config': {
            'styleClass': 'trigger-node',
            'isFlowControl': True,
            'isTrigger': True,
            'isEntryPoint': True,
            'showAddButton': True,
            'paramsComponent': 'TriggerParams'
        },
    },
    'start': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'start-node',
            'isFlowControl': True,
            'isStart': True,
            'isEntryPoint': True,
            'showAddButton': True,
            'paramsComponent': None
        },
    },
    'end': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'end-node',
            'isFlowControl': True,
            'isEnd': True,
            'isTerminal': True,
            'showAddButton': False,
            'paramsComponent': None
        },
    },
    'error_trigger': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'error-trigger-node',
            'isFlowControl': True,
            'isErrorTrigger': True,
            'showAddButton': True,
            'paramsComponent': 'GenericParams'
        },
    },
    'code': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'code-node',
            'isFlowControl': False,
            'isCode': True,
            'showAddButton': True,
            'paramsComponent': 'CodeNodeParams'
        },
    },
    'http': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'http-node',
            'isFlowControl': False,
            'isHttp': True,
            'showAddButton': True,
            'paramsComponent': 'HttpNodeParams'
        },
    },
    'llm_chain': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'llm-chain-node',
            'isFlowControl': False,
            'isLLMChain': True,
            'showAddButton': True,
            'paramsComponent': 'LLMChainParams'
        },
    },
    'vector_store': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'vector-store-node',
            'isFlowControl': False,
            'isVectorStore': True,
            'showAddButton': True,
            'paramsComponent': 'VectorStoreParams'
        },
    },
    'ai_agent': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'ai-agent-node',
            'isFlowControl': False,
            'isAgent': True,
            'showAddButton': True,
            'paramsComponent': 'AIAgentParams'
        },
    },
    'ai': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'ai-node',
            'isFlowControl': False,
            'showAddButton': True,
            'paramsComponent': 'GenericParams'
        },
    },
    'ai_sub': {
        'dimensions': {'shape': 'pill', 'width': 72, 'height': 56},
        'ui_config': {
            'styleClass': 'ai-sub-node',
            'isFlowControl': False,
            'showAddButton': False,
            'paramsComponent': 'GenericParams'
        },
    },
    'template': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'template-node',
            'isFlowControl': False,
            'isTemplate': True,
            'showAddButton': True,
            'paramsComponent': 'GenericParams'
        },
    },
    'composite': {
        'dimensions': {'shape': 'rectangle', 'width': 240, 'height': 76},
        'ui_config': {
            'styleClass': 'composite-node',
            'isFlowControl': False,
            'showAddButton': True,
            'paramsComponent': 'GenericParams'
        },
    },
}

# Default configuration for unknown node types
DEFAULT_CONFIG = NODE_TYPE_CONFIGS['standard']
DEFAULT_DIMENSIONS = DEFAULT_CONFIG['dimensions']

# Aliases: legacy callers may pass 'terminal' instead of 'end'
_TYPE_ALIASES = {'terminal': 'end'}


def get_node_config(node_type: str) -> Dict[str, Any]:
    """
    Get UI configuration for a node type.

    Args:
        node_type: The node type string (e.g. 'branch', 'switch', 'loop')

    Returns:
        Dict containing dimensions and ui_config
    """
    if not node_type:
        return DEFAULT_CONFIG

    lower_type = node_type.lower()
    lower_type = _TYPE_ALIASES.get(lower_type, lower_type)
    return NODE_TYPE_CONFIGS.get(lower_type, DEFAULT_CONFIG)


def get_node_dimensions(node_type: str) -> Dict[str, Any]:
    """Get {shape, width, height} for a node type."""
    config = get_node_config(node_type)
    return config.get('dimensions', DEFAULT_DIMENSIONS)


def _ports_to_handles(ports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert core port definitions to UI handle configs."""
    handles = []
    for p in ports:
        handle_id = p.get('handle_id') or p.get('handleId') or p['id']
        handle: Dict[str, Any] = {
            'id': handle_id,
            'position': p.get('position', 'left'),
            'color': p.get('color', '#6B7280'),
        }
        label_key = p.get('label_key') or p.get('labelKey')
        if label_key:
            handle['labelKey'] = label_key
        max_conn = p.get('max_connections') or p.get('maxConnections')
        if max_conn is not None:
            handle['maxConnections'] = max_conn
        edge_type = p.get('edge_type') or p.get('edgeType')
        if edge_type == 'resource':
            handle['type'] = 'resource'
        handles.append(handle)
    return handles


def _dynamic_ports_to_handles(dynamic_ports: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert dynamic_ports config to dynamicHandles for switch/fork nodes."""
    if not dynamic_ports:
        return None
    output_cfg = dynamic_ports.get('output')
    if not output_cfg:
        return None
    result: Dict[str, Any] = {
        'fromParam': output_cfg.get('from_param') or output_cfg.get('fromParam'),
        'position': output_cfg.get('position', 'right'),
        'idPrefix': 'source-case-',
        'colors': CASE_COLORS,
    }
    stable_key = output_cfg.get('stable_key_field') or output_cfg.get('stableKeyField')
    if stable_key:
        result['stableKeyField'] = stable_key
    return result


def enrich_module_with_node_config(module_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich module data with node configuration.

    Derives handles from ports (single source of truth):
    - uiConfig: from NODE_TYPE_CONFIGS (shape, flags, component)
    - inputHandles/outputHandles: derived from inputPorts/outputPorts
    - dynamicHandles: derived from dynamicPorts config
    - loopTargets: derived from output ports with iterate event

    Args:
        module_data: The module metadata dict

    Returns:
        Enriched module data with node configuration
    """
    node_type = (
        module_data.get('nodeType') or
        module_data.get('node_type') or
        'standard'
    )
    config = get_node_config(node_type)
    result = dict(module_data)

    # uiConfig: from node_config (shape, flags, component)
    if not result.get('uiConfig'):
        result['uiConfig'] = dict(config.get('ui_config', {}))
    elif isinstance(result['uiConfig'], dict):
        result['uiConfig'] = dict(result['uiConfig'])

    # dimensions: inject into uiConfig for frontend consumption
    dims = config.get('dimensions')
    if dims and 'dimensions' not in result['uiConfig']:
        result['uiConfig']['dimensions'] = dims

    # Handles: derive FROM ports (single source of truth)
    input_ports = result.get('inputPorts') or result.get('input_ports') or []
    output_ports = result.get('outputPorts') or result.get('output_ports') or []

    if not result.get('inputHandles') and input_ports:
        result['inputHandles'] = _ports_to_handles(input_ports)

    if not result.get('outputHandles') and output_ports:
        result['outputHandles'] = _ports_to_handles(output_ports)

    # Dynamic handles: derive from dynamic_ports config
    if not result.get('dynamicHandles'):
        dynamic_ports = result.get('dynamicPorts') or result.get('dynamic_ports')
        if dynamic_ports:
            result['dynamicHandles'] = _dynamic_ports_to_handles(dynamic_ports)

    # showErrorHandle: auto-synthesize error output port for all standard nodes
    FLOW_CONTROL_TYPES = {
        'branch', 'switch', 'loop', 'fork', 'join',
        'container', 'trigger', 'start', 'end', 'error_trigger',
        'ai_agent', 'ai_sub',
    }
    is_flow_control = node_type in FLOW_CONTROL_TYPES
    if 'showErrorHandle' not in result.get('uiConfig', {}):
        has_error_port = any(
            p.get('event') == 'error'
            for p in output_ports
        )
        if has_error_port:
            result['uiConfig']['showErrorHandle'] = True
        elif not is_flow_control:
            # Auto-add error output port and handle for standard nodes
            error_port = {
                'id': 'error',
                'handleId': 'source-error',
                'position': 'bottom',
                'label': 'Error',
                'event': 'error',
                'color': '#EF4444',
            }
            output_ports = list(output_ports)
            output_ports.append(error_port)
            result['outputPorts'] = output_ports
            # Append error handle to outputHandles
            error_handle = _ports_to_handles([error_port])
            if result.get('outputHandles'):
                result['outputHandles'] = list(result['outputHandles']) + error_handle
            else:
                result['outputHandles'] = error_handle
            result['uiConfig']['showErrorHandle'] = True

    # isMultiOutput: true if node type has multiple output paths
    MULTI_OUTPUT_TYPES = {'branch', 'switch', 'loop', 'fork', 'container', 'ai_agent'}
    if 'isMultiOutput' not in result.get('uiConfig', {}):
        if node_type in MULTI_OUTPUT_TYPES:
            result['uiConfig']['isMultiOutput'] = True

    # Loop targets: derive from output ports with iterate event
    if not result.get('loopTargets') and output_ports:
        loop_targets = [
            p.get('handle_id') or p.get('handleId') or p['id']
            for p in output_ports
            if p.get('event') == 'iterate'
        ]
        if loop_targets:
            result['loopTargets'] = loop_targets

    return result
