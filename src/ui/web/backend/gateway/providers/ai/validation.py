"""Credential validation adapters for supported AI vendors."""

import logging
import os
from typing import Any, Optional

from gateway.providers.ai.url_policy import is_ai_base_url_allowed

logger = logging.getLogger(__name__)
_PROVIDER_TIMEOUT_SECONDS = 15.0


def configured_ai_base_url_allowed(
    base_url: str,
    *,
    allowed_domains: list[str] | None = None,
) -> bool:
    """Apply deployment policy to an OpenAI-compatible endpoint."""
    allow_local = os.getenv("AI_ALLOW_LOCAL_BASE_URL", "").lower() in {
        "1",
        "true",
        "yes",
    }
    return is_ai_base_url_allowed(
        base_url,
        allow_local=allow_local,
        allowed_domains=allowed_domains,
    )


async def validate_ai_credentials(
    *,
    provider: str,
    api_key: Optional[str],
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict[str, Any]:
    """Validate credentials without exposing vendor SDKs to the API layer."""
    if not api_key:
        return {"ok": False, "error": "API key is required"}
    if base_url and provider != "openai-compatible":
        return {
            "ok": False,
            "error": "Base URL requires the openai-compatible provider",
        }
    if provider == "openai-compatible" and base_url:
        if not configured_ai_base_url_allowed(base_url):
            return {"ok": False, "error": "Base URL is not allowed"}
    if provider in {"openai", "openai-compatible"}:
        return await _validate_openai(api_key=api_key, base_url=base_url)
    if provider == "anthropic":
        return await _validate_anthropic(api_key=api_key, model=model)
    return {"ok": False, "error": "Unknown AI provider"}


async def _validate_openai(
    *,
    api_key: str,
    base_url: Optional[str],
) -> dict[str, Any]:
    try:
        import openai

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        client = openai.AsyncOpenAI(
            **kwargs,
            timeout=_PROVIDER_TIMEOUT_SECONDS,
            max_retries=1,
        )
        models_response = await client.models.list()
        model_ids = [item.id for item in models_response.data[:20]]
        return {
            "ok": True,
            "message": "AI provider credentials are valid",
            "models": model_ids,
        }
    except ImportError:
        logger.error("OpenAI-compatible SDK is not installed")
        return {"ok": False, "error": "AI provider is not available"}
    except Exception as exc:
        if _is_authentication_error(exc, "openai", "AuthenticationError"):
            return {"ok": False, "error": "Invalid API key"}
        logger.warning("OpenAI-compatible credential validation failed: %s", type(exc).__name__)
        return {"ok": False, "error": "AI provider request failed"}


async def _validate_anthropic(
    *,
    api_key: str,
    model: Optional[str],
) -> dict[str, Any]:
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(
            api_key=api_key,
            timeout=_PROVIDER_TIMEOUT_SECONDS,
            max_retries=1,
        )
        await client.messages.create(
            model=model or "claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}],
        )
        return {
            "ok": True,
            "message": "AI provider credentials are valid",
            "models": [
                "claude-opus-4-0-20250514",
                "claude-sonnet-4-20250514",
                "claude-haiku-4-20250514",
                "claude-sonnet-4-5-20250929",
            ],
        }
    except ImportError:
        logger.error("Anthropic SDK is not installed")
        return {"ok": False, "error": "AI provider is not available"}
    except Exception as exc:
        if _is_authentication_error(exc, "anthropic", "AuthenticationError"):
            return {"ok": False, "error": "Invalid API key"}
        logger.warning("Anthropic credential validation failed: %s", type(exc).__name__)
        return {"ok": False, "error": "AI provider request failed"}


def _is_authentication_error(exc: Exception, module: str, class_name: str) -> bool:
    return (
        exc.__class__.__module__.split(".", 1)[0] == module
        and exc.__class__.__name__ == class_name
    )
