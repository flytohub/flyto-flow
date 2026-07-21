"""
Config API — Modules

LLM providers, triggers, HTTP, parameter types, and node design configuration.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/llm")
async def get_llm_config():
    """
    Get LLM providers and models configuration.

    S-Grade: All LLM options are centralized here.
    Frontend should never hardcode provider/model lists.
    """
    return {
        "ok": True,
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama",
                "description": "Local LLM server",
                "icon": "CircuitBoard",
                "models": [
                    {"id": "llama3.2", "name": "Llama 3.2"},
                    {"id": "llama3.1", "name": "Llama 3.1"},
                    {"id": "llama3.1:70b", "name": "Llama 3.1 70B"},
                    {"id": "mistral", "name": "Mistral"},
                    {"id": "mixtral", "name": "Mixtral 8x7B"},
                    {"id": "codellama", "name": "Code Llama"},
                    {"id": "phi3", "name": "Phi-3"},
                    {"id": "gemma2", "name": "Gemma 2"},
                    {"id": "qwen2.5", "name": "Qwen 2.5"},
                    {"id": "deepseek-r1", "name": "DeepSeek R1"},
                ],
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "OpenAI API",
                "icon": "Bot",
                "models": [
                    {"id": "gpt-4o", "name": "GPT-4o"},
                    {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
                    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
                    {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
                    {"id": "o1", "name": "o1"},
                    {"id": "o1-mini", "name": "o1 Mini"},
                    {"id": "o3-mini", "name": "o3 Mini"},
                ],
            },
            {
                "id": "claude",
                "name": "Claude",
                "description": "Anthropic Claude",
                "icon": "Sparkles",
                "models": [
                    {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
                    {"id": "claude-opus-4-20250514", "name": "Claude Opus 4"},
                    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
                    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
                    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
                ],
            },
            {
                "id": "gemini",
                "name": "Gemini",
                "description": "Google Gemini",
                "icon": "Gem",
                "models": [
                    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
                    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
                    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
                ],
            },
        ],
        "defaults": {
            "provider": "ollama",
            "model": "llama3.2",
            "temperature": 0.7,
            "max_tokens": 1000,
        },
    }


@router.get("/triggers")
async def get_trigger_config():
    """
    Get trigger types configuration.

    S-Grade: All trigger options are centralized here.
    Frontend should never hardcode trigger types.
    """
    return {
        "ok": True,
        "trigger_types": [
            {
                "id": "manual",
                "name": "Manual",
                "description": "Manually triggered by user",
                "icon": "Play",
            },
            {
                "id": "webhook",
                "name": "Webhook",
                "description": "Triggered by HTTP webhook",
                "icon": "Webhook",
            },
            {
                "id": "schedule",
                "name": "Schedule",
                "description": "Triggered on schedule (cron)",
                "icon": "Clock",
            },
            {
                "id": "event",
                "name": "Event",
                "description": "Triggered by system event",
                "icon": "Zap",
            },
            {
                "id": "mcp",
                "name": "MCP Tool",
                "description": "Exposed as a callable MCP tool for AI clients",
                "icon": "PlugZap",
            },
        ],
        "defaults": {
            "trigger_type": "manual",
        },
    }


@router.get("/http")
async def get_http_config():
    """
    Get HTTP module configuration.

    Methods, authentication types, and body types for HTTP nodes.
    """
    return {
        "ok": True,
        "methods": [
            {"id": "GET", "name": "GET", "has_body": False},
            {"id": "POST", "name": "POST", "has_body": True},
            {"id": "PUT", "name": "PUT", "has_body": True},
            {"id": "PATCH", "name": "PATCH", "has_body": True},
            {"id": "DELETE", "name": "DELETE", "has_body": False},
            {"id": "HEAD", "name": "HEAD", "has_body": False},
            {"id": "OPTIONS", "name": "OPTIONS", "has_body": False},
        ],
        "auth_types": [
            {"id": "none", "name": "None", "fields": []},
            {"id": "bearer", "name": "Bearer Token", "fields": ["token"]},
            {"id": "basic", "name": "Basic Auth", "fields": ["username", "password"]},
            {"id": "api_key", "name": "API Key", "fields": ["key", "value", "location"]},
        ],
        "body_types": [
            {"id": "none", "name": "None"},
            {"id": "json", "name": "JSON"},
            {"id": "form", "name": "Form Data"},
            {"id": "raw", "name": "Raw"},
            {"id": "multipart", "name": "Multipart"},
        ],
        "defaults": {
            "method": "GET",
            "auth_type": "none",
            "body_type": "none",
            "timeout": 30000,
        },
    }


@router.get("/param-types")
async def get_param_type_config():
    """
    Get parameter type to UI component mappings.

    Defines which UI components to use for different parameter types.
    """
    return {
        "ok": True,
        "param_type_map": {
            "string": {
                "default": "text-input",
                "multiline": "textarea",
                "code": "code-editor",
                "markdown": "markdown-editor",
                "html": "html-editor",
                "json": "json-editor",
                "yaml": "yaml-editor",
                "xml": "xml-editor",
                "sql": "sql-editor",
                "password": "password-input",
                "email": "email-input",
                "url": "url-input",
                "color": "color-picker",
                "date": "date-picker",
                "time": "time-picker",
                "datetime": "datetime-picker",
                "file_path": "file-path-input",
                "directory": "directory-picker",
                "template": "template-editor",
            },
            "number": {
                "default": "number-input",
                "slider": "slider",
                "rating": "rating",
                "percentage": "percentage-input",
            },
            "integer": {
                "default": "number-input",
                "slider": "slider",
                "stepper": "stepper",
            },
            "boolean": {
                "default": "toggle-switch",
                "checkbox": "checkbox",
            },
            "array": {
                "default": "tag-input",
                "list": "list-editor",
                "table": "table-editor",
                "checkboxes": "checkbox-group",
            },
            "object": {
                "default": "json-editor",
                "key_value": "key-value-editor",
                "form": "nested-form",
            },
            "file": {
                "default": "file-upload",
                "image/*": "image-upload",
                "video/*": "video-upload",
                "audio/*": "audio-upload",
            },
            "enum": {
                "default": "select-dropdown",
                "radio": "radio-group",
                "segmented": "segmented-control",
            },
        },
        "output_type_map": {
            "string": {
                "default": "text-block",
                "image": "image-preview",
                "video": "video-player",
                "audio": "audio-player",
                "code": "code-block",
                "markdown": "markdown-renderer",
                "html": "html-renderer",
                "json": "json-viewer",
                "url": "link",
                "email": "email-link",
            },
            "number": {
                "default": "number-display",
                "currency": "currency-display",
                "percentage": "percentage-display",
                "progress": "progress-bar",
            },
            "boolean": {
                "default": "boolean-badge",
                "icon": "boolean-icon",
            },
            "array": {
                "default": "list-display",
                "table": "table-display",
                "tags": "tag-display",
            },
            "object": {
                "default": "json-viewer",
                "tree": "tree-viewer",
                "table": "key-value-display",
            },
            "file": {
                "default": "file-download",
                "preview": "file-preview",
            },
        },
    }


@router.get("/node-design")
async def get_node_design_config():
    """
    Node dimensions, shapes, and visual config for each node type.

    SSOT for layout engine + frontend rendering.
    Icon/color management is separate (module-appearance API).
    """
    from services.node_config import NODE_TYPE_CONFIGS

    design = {}
    for ntype, conf in NODE_TYPE_CONFIGS.items():
        design[ntype] = {
            'dimensions': conf.get('dimensions', {}),
            'ui_config': conf.get('ui_config', {}),
        }
    return {"ok": True, "node_design": design}
