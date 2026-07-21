"""AI vendor adapters exposed through provider-neutral functions."""

from gateway.providers.ai.validation import (
    configured_ai_base_url_allowed,
    validate_ai_credentials,
)

__all__ = ["configured_ai_base_url_allowed", "validate_ai_credentials"]
