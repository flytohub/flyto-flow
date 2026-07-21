"""
Graph Helper Functions

Shared utilities for workflow graph operations.
These functions are used across validation.py and other graph-related code
to ensure consistent behavior for special node types.

Node type detection reads from flyto-core's ModuleRegistry metadata (SSOT).
A module-level cache avoids repeated registry lookups. If the registry is
unavailable (e.g. cloud-only context without flyto-core installed), a
lightweight string-based heuristic is used as fallback.

Usage:
    from services.graph_helpers import is_loop_module, is_branch_module
"""

import logging
from typing import Dict, Optional


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node-type cache: module_id -> node_type string
# Populated lazily from ModuleRegistry metadata.
# ---------------------------------------------------------------------------
_node_type_cache: Dict[str, str] = {}
_registry_available: Optional[bool] = None


def _get_registry():
    """Try to import ModuleRegistry. Returns class or None."""
    global _registry_available
    if _registry_available is False:
        return None
    try:
        from core.modules.registry import ModuleRegistry
        _registry_available = True
        return ModuleRegistry
    except ImportError:
        _registry_available = False
        return None


def _resolve_node_type(module_id: str) -> str:
    """
    Resolve node_type for a module_id.

    Priority:
      1. Cache hit
      2. ModuleRegistry metadata (if available)
      3. String-based heuristic fallback
    """
    if module_id in _node_type_cache:
        return _node_type_cache[module_id]

    # Try registry
    registry = _get_registry()
    if registry is not None:
        meta = registry.get_metadata(module_id)
        if isinstance(meta, dict):
            registry_node_type = meta.get("node_type")
        else:
            registry_node_type = getattr(meta, "node_type", None)
        if isinstance(registry_node_type, str) and registry_node_type:
            nt = registry_node_type
            _node_type_cache[module_id] = nt
            return nt

    # Fallback: string heuristic (keeps the system working without core)
    nt = _heuristic_node_type(module_id)
    _node_type_cache[module_id] = nt
    return nt


def _heuristic_node_type(module_id: str) -> str:
    """
    String-based fallback for node type detection.

    Only used when ModuleRegistry is unavailable. Kept intentionally broad
    so that new modules registered in core with proper node_type metadata
    are picked up automatically via _resolve_node_type.
    """
    ml = module_id.lower()

    # Order matters: more specific checks first
    if any(kw in ml for kw in ('loop', 'foreach', 'while', 'repeat')):
        return 'loop'
    if any(kw in ml for kw in ('branch', 'flow.if')):
        return 'branch'
    if 'switch' in ml:
        return 'switch'
    if any(kw in ml for kw in ('container', 'sandbox')):
        return 'container'
    if ml.startswith('flow.subflow'):
        return 'subflow'
    if ml.startswith('flow.start'):
        return 'start'
    if any(ml.startswith(p) for p in ('flow.trigger', 'flow.webhook')):
        return 'trigger'
    if any(ml.startswith(p) for p in ('flow.end', 'flow.return', 'flow.exit')):
        return 'end'
    if any(kw in ml for kw in ('breakpoint', 'interact')):
        return 'breakpoint'
    if any(ml.startswith(p) for p in ('flow.merge',)):
        return 'merge'
    if any(ml.startswith(p) for p in ('flow.fork',)):
        return 'fork'
    if any(ml.startswith(p) for p in ('flow.join',)):
        return 'join'

    return 'standard'


# ---------------------------------------------------------------------------
# Backward-compatible module-list constants (deprecated, kept for imports)
# Callers should prefer the is_*_module() functions.
# ---------------------------------------------------------------------------
LOOP_MODULES = ('flow.loop', 'flow.foreach', 'flow.while', 'flow.repeat')
BRANCH_MODULES = ('flow.branch', 'flow.if')
SWITCH_MODULES = ('flow.switch',)
CONTAINER_MODULES = ('flow.container', 'flow.sandbox', 'flow.subflow')
START_MODULES = ('flow.start',)
TRIGGER_MODULES = ('flow.trigger', 'flow.webhook')
TERMINAL_MODULES = ('flow.end', 'flow.return', 'flow.exit')


# ---------------------------------------------------------------------------
# Public API: node type checks
# All delegate to _resolve_node_type which reads from registry first.
# ---------------------------------------------------------------------------

def is_loop_module(module_id: Optional[str]) -> bool:
    """Check if module is a loop type (iterates over items or repeats)."""
    if not module_id:
        return False
    return _resolve_node_type(module_id) == 'loop'


def is_branch_module(module_id: Optional[str]) -> bool:
    """Check if module is a branch type (conditional flow)."""
    if not module_id:
        return False
    return _resolve_node_type(module_id) == 'branch'


def is_switch_module(module_id: Optional[str]) -> bool:
    """Check if module is a switch type (multi-path value matching)."""
    if not module_id:
        return False
    return _resolve_node_type(module_id) == 'switch'


def is_container_module(module_id: Optional[str]) -> bool:
    """Check if module is a container type (nested workflows)."""
    if not module_id:
        return False
    return _resolve_node_type(module_id) in ('container', 'subflow')


def is_start_module(module_id: Optional[str]) -> bool:
    """Check if module is a start/entry point."""
    if not module_id:
        return False
    return _resolve_node_type(module_id) == 'start'


def is_trigger_module(module_id: Optional[str]) -> bool:
    """Check if module is a trigger/entry point type."""
    if not module_id:
        return False
    return _resolve_node_type(module_id) == 'trigger'


def is_breakpoint_module(module_id: Optional[str]) -> bool:
    """Check if module is a breakpoint type (human-in-the-loop)."""
    if not module_id:
        return False
    return _resolve_node_type(module_id) == 'breakpoint'


def is_terminal_module(module_id: Optional[str]) -> bool:
    """Check if module is a terminal/end type."""
    if not module_id:
        return False
    return _resolve_node_type(module_id) == 'end'


def get_target_handle(module_id: Optional[str]) -> str:
    """
    Get the correct targetHandle ID based on module type.

    Reads from registry metadata input_ports when available, falls back to
    node_type convention: loop -> 'in', everything else -> 'target'.
    """
    if not module_id:
        return "target"

    # Try registry for the actual input port handle_id
    registry = _get_registry()
    if registry is not None:
        meta = registry.get_metadata(module_id)
        if isinstance(meta, dict):
            input_ports = meta.get("input_ports") or []
        else:
            input_ports = getattr(meta, "input_ports", None) or []
        if isinstance(input_ports, list):
            for port in input_ports:
                if not isinstance(port, dict):
                    continue
                if port.get("id") == "input":
                    handle_id = port.get("handle_id") or port.get("handleId")
                    if handle_id:
                        return handle_id

    # Fallback: convention
    if is_loop_module(module_id):
        return "in"
    return "target"


def get_source_handle(module_id: Optional[str]) -> str:
    """
    Get the default sourceHandle ID for a module.

    Returns 'output' for standard modules. Flow control modules (branch/
    switch/loop) have multiple output handles that callers resolve per-edge.
    """
    return "output"


def get_node_type_from_module(module_id: Optional[str]) -> str:
    """
    Determine the node type from module ID for rendering purposes.

    Reads from flyto-core ModuleRegistry metadata first, falls back to
    string heuristic.

    Returns:
        Node type string: 'loop', 'branch', 'switch', 'container',
        'trigger', 'start', 'end', or 'standard'
    """
    if not module_id:
        return "standard"
    return _resolve_node_type(module_id)
