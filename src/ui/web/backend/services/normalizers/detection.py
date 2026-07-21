"""
Module Detection and Classification Utilities

Functions for detecting node types, AI module flags, template modules,
and custom UI requirements.
"""

from typing import Dict, Any, Optional, Set


def detect_node_type(module_id: str, metadata: Dict[str, Any] = None) -> Optional[str]:
    """
    Detect special node types from module ID patterns.

    Backend is single source of truth for nodeType - frontend just uses the value.
    This function handles flow control nodes that need special rendering.

    Args:
        module_id: The module identifier (e.g., 'flow.branch', 'loop.times')
        metadata: Optional module metadata dict

    Returns:
        Node type string or None to use category default
    """
    if metadata is None:
        metadata = {}

    # Check if metadata already specifies node_type
    explicit_type = metadata.get("node_type") or metadata.get("nodeType")
    if explicit_type:
        return explicit_type

    id_lower = module_id.lower()

    # Extract the module name (last segment after the last dot) for precise matching
    # e.g., "flow.loop" -> "loop", "string.loop_handler" -> "loop_handler"
    module_name = id_lower.rsplit('.', 1)[-1] if '.' in id_lower else id_lower

    # Loop nodes - iterate over items or repeat
    if module_name in ("loop", "foreach", "while", "repeat"):
        return "loop"

    # Branch nodes - conditional flow
    if module_name == "branch" or id_lower == "flow.if":
        return "branch"

    # Switch nodes - multi-way branching
    if module_name == "switch":
        return "switch"

    # Container nodes - subflow/sandbox
    if module_name in ("container", "sandbox", "subflow"):
        return "container"

    # Trigger nodes - workflow entry points
    if module_name == "trigger" or id_lower == "flow.start":
        return "trigger"

    # AI Agent nodes (not sub-agents)
    if module_name == "agent" and "sub" not in id_lower:
        return "ai_agent"

    # Code nodes
    if id_lower.startswith("code.") or module_name == "execute_code":
        return "code"

    # HTTP nodes
    if id_lower.startswith("http.") or id_lower.startswith("api."):
        return "http"

    return None  # Use category default


def detect_ai_module_flags(module_id: str, category: str, metadata: Dict[str, Any] = None) -> Dict[str, bool]:
    """
    Detect AI-related module flags for frontend filtering.

    Backend is single source of truth - frontend uses these flags directly
    instead of hardcoded prefix matching.

    Args:
        module_id: The module identifier
        category: Module category
        metadata: Optional module metadata dict

    Returns:
        Dict with isAIModel, isMemory, isTool flags
    """
    if metadata is None:
        metadata = {}

    id_lower = module_id.lower()
    cat_lower = category.lower() if category else ""

    # isAIModel: LLM/Chat models that can be used as AI Agent model
    is_ai_model = (
        id_lower.startswith("api.openai") or
        id_lower.startswith("api.anthropic") or
        id_lower.startswith("api.google_gemini") or
        id_lower.startswith("ai.") or
        id_lower.startswith("llm.") or
        id_lower.startswith("agent.") or
        cat_lower == "ai" or
        cat_lower == "llm" or
        metadata.get("isAIModel", False)
    )

    # isMemory: Memory/context modules for AI Agent memory port
    is_memory = (
        "memory" in id_lower or
        id_lower.startswith("ai.memory") or
        metadata.get("isMemory", False)
    )

    # isTool: Tool modules that can be connected to AI Agent tools port
    is_tool = (
        cat_lower in ("tools", "developer", "browser") or
        "tool" in id_lower or
        id_lower.startswith("browser.") or
        id_lower.startswith("http.") or
        id_lower.startswith("file.") or
        id_lower.startswith("data.") or
        metadata.get("isTool", False)
    )

    return {
        "isAIModel": is_ai_model,
        "isMemory": is_memory,
        "isTool": is_tool
    }


def is_template_module(module_id: str) -> bool:
    """
    Check if module ID represents a template module.

    Args:
        module_id: The module identifier

    Returns:
        True if this is a template module
    """
    if not module_id:
        return False
    return module_id.startswith("template.")


# Module IDs that require custom parameter UI components
# These have complex UIs that cannot be auto-generated from paramsSchema
# This is the single source of truth - frontend reads this from module metadata
CUSTOM_UI_MODULE_PATTERNS: Set[str] = {
    # Flow Control - Dynamic routing, conditional handles
    "flow.branch",
    "flow.if",
    "flow.switch",
    "flow.loop",
    "flow.foreach",
    "flow.while",

    # AI/LLM - Provider selection, model tabs, streaming config
    "ai.llm_chain",
    "ai.llm",
    "langchain.llm",

    # Vector Store - Operation modes, collection selector
    "ai.vector_store",
    "ai.vectorstore",
    "langchain.vectorstore",

    # AI Agent - Tool selection, iteration settings, resource ports
    "ai.agent",
    "ai.autonomous",
    "langchain.agent",

    # Code - Monaco editor integration
    "code.run",
    "code.javascript",
    "code.python",

    # HTTP - Method tabs, headers builder, curl import
    "http.request",
    "http.get",
    "http.post",
    "http.put",
    "http.delete",

    # Form - Dynamic field builder
    "form.input",
    "form.select",
    "form.checkbox",
    "form.textarea",
}

# Prefix patterns for custom UI detection
CUSTOM_UI_PREFIXES: Set[str] = {
    "huggingface.",  # HuggingFace - Model browser
}


def detect_requires_custom_ui(module_id: str, metadata: Dict[str, Any] = None) -> bool:
    """
    Detect if a module requires custom parameter UI.

    Backend is single source of truth - frontend reads this flag directly
    instead of maintaining a hardcoded list.

    Modules requiring custom UI have complex parameter interfaces that
    cannot be auto-generated from paramsSchema, such as:
    - Dynamic handles (switch, branch nodes)
    - Provider tabs (LLM models)
    - Code editors (code modules)
    - File uploaders (form modules)

    Args:
        module_id: The module identifier
        metadata: Optional module metadata dict

    Returns:
        True if module needs custom parameter UI
    """
    if not module_id:
        return False

    if metadata is None:
        metadata = {}

    # Check metadata first (explicit override)
    if metadata.get("requiresCustomUI") is not None:
        return metadata.get("requiresCustomUI")
    if metadata.get("requires_custom_ui") is not None:
        return metadata.get("requires_custom_ui")

    # Exact match
    if module_id in CUSTOM_UI_MODULE_PATTERNS:
        return True

    # Prefix match
    for prefix in CUSTOM_UI_PREFIXES:
        if module_id.startswith(prefix):
            return True

    return False
