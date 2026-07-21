"""
Template Runtime Module

Provides subprocess-based template execution for non-official templates.
Templates execute in isolated subprocesses with restricted permissions.

This follows the flyto-platform design principle:
- Official templates: execute in-process (trusted)
- Non-official templates: execute in subprocess (isolated)
"""

from .runtime import (
    TemplateRuntime,
    TemplateProcess,
    TemplateProcessConfig,
    ProcessStatus,
    get_template_runtime,
)

from .protocol import (
    JsonRpcRequest,
    JsonRpcResponse,
    ProtocolEncoder,
    ProtocolDecoder,
    ErrorCode,
    PROTOCOL_VERSION,
)

__all__ = [
    # Runtime
    "TemplateRuntime",
    "TemplateProcess",
    "TemplateProcessConfig",
    "ProcessStatus",
    "get_template_runtime",

    # Protocol
    "JsonRpcRequest",
    "JsonRpcResponse",
    "ProtocolEncoder",
    "ProtocolDecoder",
    "ErrorCode",
    "PROTOCOL_VERSION",
]
