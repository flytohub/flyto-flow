"""Redaction helpers for execution inputs, outputs, and persisted status."""

import re
from typing import Any, Collection, Optional


DEFAULT_SENSITIVE_KEYS = frozenset({
    "password",
    "passwd",
    "pwd",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "credential",
    "credentials",
    "private_key",
    "private",
    "access_key",
    "secret_key",
    "session",
    "cookie",
    "jwt",
    "bearer",
    "username",
    "user_name",
})

SAFE_SECRET_METADATA_KEYS = frozenset({
    "secret_values_stored",
    "secrets_policy",
    "runtime_args_policy",
})


def is_sensitive_key(
    key: Any,
    *,
    sensitive_keys: Optional[Collection[str]] = None,
) -> bool:
    """Return true when a dict key is expected to hold a secret value."""
    if not isinstance(key, str):
        return False

    normalized = key.strip().lower()
    if not normalized or normalized in SAFE_SECRET_METADATA_KEYS:
        return False

    keys = {item.lower() for item in (sensitive_keys or DEFAULT_SENSITIVE_KEYS)}
    if normalized in keys:
        return True

    parts = [part for part in re.split(r"[^a-z0-9]+", normalized) if part]
    return any(part in keys for part in parts)


def looks_like_secret(value: str) -> bool:
    """Detect common token/key shapes without hiding ordinary long slugs."""
    if len(value) < 20:
        return False

    secret_patterns = [
        "eyJ",       # JWT prefix
        "sk-",       # OpenAI/Stripe prefix
        "ghp_",      # GitHub personal token
        "gho_",      # GitHub OAuth token
        "Bearer ",   # Bearer token
    ]
    if any(pattern in value for pattern in secret_patterns):
        return True

    # Generic high-entropy fallback. Keep this deliberately narrower than
    # slug syntax so MCP tool names like warroom_product_verification survive.
    return len(value) > 48 and all(c.isalnum() or c in "+/=" for c in value)


def redact_sensitive(
    data: Any,
    *,
    sensitive_keys: Optional[Collection[str]] = None,
) -> Any:
    """Recursively replace secret values with [REDACTED]."""
    if data is None:
        return None

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if is_sensitive_key(key, sensitive_keys=sensitive_keys):
                result[key] = "[REDACTED]"
            else:
                result[key] = redact_sensitive(value, sensitive_keys=sensitive_keys)
        return result

    if isinstance(data, list):
        return [redact_sensitive(item, sensitive_keys=sensitive_keys) for item in data]

    if isinstance(data, str) and looks_like_secret(data):
        return "[REDACTED]"

    return data
