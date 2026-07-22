"""Same-origin protection for state-changing CE requests."""

from __future__ import annotations

import hmac
import os
import secrets
from collections.abc import Iterable, Sequence
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"
DEFAULT_EXEMPT_PREFIXES = ("/api/health", "/health", "/metrics")


def _split_env_list(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _origin(value: str) -> str | None:
    if not value or value == "null":
        return None
    try:
        parsed = urlparse(value)
    except ValueError:
        return None
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Reject cross-origin mutations; CE has no session or identity cookies."""

    def __init__(
        self,
        app,
        *,
        allowed_origins: Sequence[str],
        exempt_prefixes: Iterable[str] = (),
        enabled: bool = True,
    ) -> None:
        super().__init__(app)
        self._allow_any = "*" in allowed_origins
        self._allowed = frozenset(
            normalized for normalized in (_origin(value) for value in allowed_origins) if normalized
        )
        configured = _split_env_list(os.getenv("FLYTO_CSRF_EXEMPT_PATHS"))
        self._exempt = tuple(set(DEFAULT_EXEMPT_PREFIXES + tuple(exempt_prefixes) + tuple(configured)))
        flag = os.getenv("FLYTO_CSRF_ENABLED", "").strip().lower()
        self._enabled = enabled if not flag else flag in {"1", "true", "yes", "on"}

    def _is_exempt(self, path: str) -> bool:
        return any(path == prefix or path.startswith(prefix) for prefix in self._exempt)

    def _origin_allowed(self, value: str) -> bool:
        return self._allow_any or _origin(value) in self._allowed

    async def dispatch(self, request: Request, call_next):
        if not self._enabled or request.method not in UNSAFE_METHODS or self._is_exempt(request.url.path):
            return await call_next(request)

        supplied_origin = request.headers.get("origin") or request.headers.get("referer")
        if supplied_origin and not self._origin_allowed(supplied_origin):
            return JSONResponse(status_code=403, content={"ok": False, "error": "Cross-origin request rejected"})

        cookie = request.cookies.get(CSRF_COOKIE_NAME)
        if cookie:
            header = request.headers.get(CSRF_HEADER_NAME)
            if not header or not hmac.compare_digest(cookie, header):
                return JSONResponse(status_code=403, content={"ok": False, "error": "CSRF token mismatch"})
        return await call_next(request)
