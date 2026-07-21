"""
Workflow JSON Schema

JSON Schema definition for workflow validation.
"""

from typing import List, Tuple

# JSON Schema for workflow definition (Draft-07)
WORKFLOW_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["id", "name", "nodes"],
    "properties": {
        "id": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_-]{1,100}$",
            "description": "Unique workflow identifier",
        },
        "name": {
            "type": "string",
            "maxLength": 200,
            "description": "Human-readable workflow name",
        },
        "description": {
            "type": "string",
            "maxLength": 2000,
        },
        "version": {
            "type": "string",
            "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$",
        },
        "nodes": {
            "type": "array",
            "items": {"$ref": "#/definitions/node"},
            "minItems": 1,
        },
        "edges": {
            "type": "array",
            "items": {"$ref": "#/definitions/edge"},
        },
        "variables": {
            "type": "object",
            "additionalProperties": True,
        },
        "triggers": {
            "type": "array",
            "items": {"$ref": "#/definitions/trigger"},
        },
        "metadata": {
            "type": "object",
            "properties": {
                "author": {"type": "string", "maxLength": 100},
                "tags": {
                    "type": "array",
                    "items": {"type": "string", "maxLength": 50},
                    "maxItems": 20,
                },
                "created_at": {"type": "string"},
                "updated_at": {"type": "string"},
            },
        },
    },
    "definitions": {
        "node": {
            "type": "object",
            "required": ["id", "type", "module"],
            "properties": {
                "id": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9_-]{1,100}$",
                },
                "type": {
                    "type": "string",
                    "enum": ["action", "condition", "loop", "subflow", "start", "end"],
                },
                "module": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9_.:-]{1,100}$",
                },
                "name": {
                    "type": "string",
                    "maxLength": 200,
                },
                "params": {
                    "type": "object",
                },
                "position": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"},
                    },
                },
                "retry": {
                    "type": "object",
                    "properties": {
                        "max_attempts": {"type": "integer", "minimum": 0, "maximum": 10},
                        "delay_ms": {"type": "integer", "minimum": 0, "maximum": 60000},
                    },
                },
                "timeout_ms": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3600000,
                },
            },
        },
        "edge": {
            "type": "object",
            "required": ["source", "target"],
            "properties": {
                "id": {"type": "string"},
                "source": {"type": "string"},
                "target": {"type": "string"},
                "source_handle": {"type": "string"},
                "target_handle": {"type": "string"},
                "type": {
                    "type": "string",
                    "enum": ["control", "resource"],
                },
                "condition": {
                    "type": "string",
                    "maxLength": 500,
                },
            },
        },
        "trigger": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "id": {"type": "string"},
                "type": {
                    "type": "string",
                    "enum": ["cron", "webhook", "queue", "event", "manual"],
                },
                "config": {"type": "object"},
                "enabled": {"type": "boolean"},
            },
        },
    },
}

# Dangerous patterns to detect in strings
# Format: (regex_pattern, error_code, message)
DANGEROUS_PATTERNS: List[Tuple[str, str, str]] = [
    # Code injection
    (r"__import__", "CODE_INJECTION", "Possible code injection via __import__"),
    (r"eval\s*\(", "CODE_INJECTION", "Possible code injection via eval()"),
    (r"exec\s*\(", "CODE_INJECTION", "Possible code injection via exec()"),
    (r"compile\s*\(", "CODE_INJECTION", "Possible code injection via compile()"),

    # Template injection
    (r"\{\{.*?__.*?\}\}", "TEMPLATE_INJECTION", "Possible template injection"),
    (r"\$\{.*?__.*?\}", "TEMPLATE_INJECTION", "Possible template injection"),

    # Path traversal
    (r"\.\./", "PATH_TRAVERSAL", "Possible path traversal attack"),
    (r"\\\.\\.", "PATH_TRAVERSAL", "Possible path traversal attack"),

    # Command injection
    (r";\s*rm\s", "COMMAND_INJECTION", "Possible command injection"),
    (r"\|\s*sh\b", "COMMAND_INJECTION", "Possible command injection"),
    (r"`.*`", "COMMAND_INJECTION", "Possible command injection via backticks"),
    (r"\$\(.*\)", "COMMAND_INJECTION", "Possible command injection via $()"),

    # SQL injection patterns
    (r"'\s*OR\s*'", "SQL_INJECTION", "Possible SQL injection"),
    (r"--\s*$", "SQL_INJECTION", "Possible SQL comment injection"),
    (r";\s*DROP\s", "SQL_INJECTION", "Possible SQL injection"),

    # SSRF patterns
    (r"file://", "SSRF", "Possible SSRF via file:// protocol"),
    (r"gopher://", "SSRF", "Possible SSRF via gopher:// protocol"),
    (r"dict://", "SSRF", "Possible SSRF via dict:// protocol"),
]
