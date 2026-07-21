"""Deterministic URL policy for user-configured AI provider endpoints."""

from collections.abc import Iterable
from urllib.parse import urlparse


AI_BASE_URL_ALLOWED_DOMAINS = frozenset({
    "api.openai.com",
    "openrouter.ai",
    "api.groq.com",
    "api.together.xyz",
    "api.mistral.ai",
    "api.deepseek.com",
    "api.fireworks.ai",
    "api.perplexity.ai",
    "api.endpoints.anyscale.com",
    "api.cohere.com",
})

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "0.0.0.0", "::1"})


def is_ai_base_url_allowed(
    base_url: str,
    *,
    allow_local: bool = False,
    allowed_domains: Iterable[str] | None = None,
) -> bool:
    """Allow known HTTPS vendors and explicitly enabled local runtimes."""
    try:
        parsed = urlparse(base_url)
        host = (parsed.hostname or "").lower().rstrip(".")
        scheme = (parsed.scheme or "").lower()
        _ = parsed.port
    except (TypeError, ValueError):
        return False

    if not host or scheme not in {"http", "https"}:
        return False
    if parsed.username or parsed.password:
        return False
    if host in _LOCAL_HOSTS:
        return allow_local
    if scheme != "https":
        return False
    domains = {
        domain.lower().rstrip(".")
        for domain in (
            AI_BASE_URL_ALLOWED_DOMAINS
            if allowed_domains is None
            else allowed_domains
        )
        if domain
    }
    return host in domains or host.endswith(".openai.azure.com")
