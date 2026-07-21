"""
CSRF Protection Middleware (FLY-24 / H2)

Defends state-changing requests (POST/PUT/PATCH/DELETE) on the FastAPI
cloud/worker/local apps against Cross-Site Request Forgery.

Defense layers (in order):

1. Method filter — safe methods (GET/HEAD/OPTIONS/TRACE) bypass.
2. Path exemption — webhook / OAuth callback endpoints that authenticate via
   signed payloads (not cookies) are exempt.
3. Origin / Referer allowlist — if the request carries an ``Origin`` header it
   MUST match the configured allowlist, else 403. If no ``Origin`` is present
   (common with server-to-server or CLI callers) the ``Referer`` host is
   checked; if it is also absent the request is allowed through, because a
   browser-initiated CSRF always carries at least one of these headers.
4. Double-submit token — when a session cookie is detected in the request OR
   the client sends the CSRF cookie, the ``X-CSRF-Token`` request header MUST
   match the ``csrf_token`` cookie value (constant-time compare). This covers
   any future cookie-based auth flows without a middleware rewrite.

The middleware is **fail-closed**: any configuration surprise results in 403.

Configuration (env):
    FLYTO_CSRF_ENABLED         — "false" disables enforcement (default: on)
    FLYTO_CSRF_ALLOWED_ORIGINS — comma-separated origins; falls back to the
                                 CORS allowlist if unset.
    FLYTO_CSRF_EXEMPT_PATHS    — comma-separated path prefixes to exempt in
                                 addition to the built-in webhook/oauth list.
"""

from __future__ import annotations

import hmac
import logging
import os
import secrets
from typing import Callable, Iterable, Optional, Sequence
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# HTTP methods that mutate state and therefore require CSRF defenses.
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Cookie name the SPA reads to echo in the X-CSRF-Token header.
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"

# Names of request cookies that indicate the caller is using cookie-based
# auth (so the double-submit token is enforced). Extend here when new
# authenticated cookie mechanisms are introduced.
AUTH_COOKIE_NAMES = frozenset({
    "_flyto_secret",   # desktop sidecar (main_local.py)
    "session",         # generic reserved name for future session cookies
    "__session",       # Firebase hosting session cookie reserved name
    "flyto_session",   # reserved for future cloud session cookie
})

# Path prefixes that must be exempt from CSRF enforcement because they carry
# their own authenticity proof (HMAC signature, one-time state token, etc.)
# and therefore cannot provide a CSRF header. Keep this list tight.
DEFAULT_EXEMPT_PREFIXES: tuple[str, ...] = (
    "/api/billing/webhook",          # Stripe — validated via stripe-signature
    "/api/triggers/webhooks/",       # User-defined webhooks — HMAC + IP allowlist
    "/auth/desktop-oauth/callback",  # Desktop OAuth — validated via state param
    "/api/health",                   # Health probe
    "/health",                       # Health probe (alt)
    "/metrics",                      # Prom scrape
)


def _split_env_list(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _origin_host(origin: str) -> Optional[str]:
    """Return the scheme://host[:port] portion of an Origin/Referer value.

    Returns None if the value cannot be parsed into an origin (e.g. "null").
    """
    if not origin or origin == "null":
        return None
    try:
        parsed = urlparse(origin)
    except ValueError:
        return None
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def generate_csrf_token() -> str:
    """Generate a cryptographically strong CSRF token."""
    return secrets.token_urlsafe(32)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Enforce CSRF defenses on state-changing requests.

    See module docstring for defense-layer ordering.
    """

    def __init__(
        self,
        app,
        *,
        allowed_origins: Sequence[str],
        exempt_prefixes: Iterable[str] = (),
        enabled: bool = True,
    ) -> None:
        super().__init__(app)
        # Normalize to scheme://host[:port] so comparisons are stable. A bare
        # "*" in the list turns the origin check into a no-op, matching the
        # CORS allow_origins semantics used upstream.
        normalized: list[str] = []
        self._allow_any_origin = False
        for origin in allowed_origins:
            if origin == "*":
                self._allow_any_origin = True
                continue
            normalized_origin = _origin_host(origin)
            if normalized_origin:
                normalized.append(normalized_origin)
            else:
                logger.warning("CSRF: ignoring malformed allowed origin %r", origin)
        self._allowed_origins = frozenset(normalized)

        exempt_env = _split_env_list(os.getenv("FLYTO_CSRF_EXEMPT_PATHS"))
        combined = tuple(DEFAULT_EXEMPT_PREFIXES) + tuple(exempt_prefixes) + tuple(exempt_env)
        self._exempt_prefixes = tuple(sorted(set(combined)))

        env_flag = os.getenv("FLYTO_CSRF_ENABLED", "").strip().lower()
        if env_flag in {"0", "false", "no", "off"}:
            self._enabled = False
        elif env_flag in {"1", "true", "yes", "on"}:
            self._enabled = True
        else:
            self._enabled = enabled

        if not self._enabled:
            logger.warning("CSRFProtectionMiddleware: enforcement DISABLED via env")

    # --- helpers -----------------------------------------------------------

    def _is_exempt(self, path: str) -> bool:
        return any(path == prefix or path.startswith(prefix) for prefix in self._exempt_prefixes)

    def _origin_allowed(self, origin_value: str) -> bool:
        if self._allow_any_origin:
            return True
        candidate = _origin_host(origin_value)
        if candidate is None:
            return False
        return candidate in self._allowed_origins

    def _referer_allowed(self, referer_value: str) -> bool:
        return self._origin_allowed(referer_value)

    def _has_auth_cookie(self, request: Request) -> bool:
        return any(name in request.cookies for name in AUTH_COOKIE_NAMES)

    def _double_submit_valid(self, request: Request) -> bool:
        cookie_value = request.cookies.get(CSRF_COOKIE_NAME)
        header_value = request.headers.get(CSRF_HEADER_NAME)
        if not cookie_value or not header_value:
            return False
        # Constant-time compare to avoid timing oracles.
        return hmac.compare_digest(cookie_value, header_value)

    @staticmethod
    def _reject(reason: str) -> Response:
        return JSONResponse(
            status_code=403,
            content={"ok": False, "error": "CSRF check failed", "reason": reason},
        )

    # --- dispatch ----------------------------------------------------------

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self._enabled:
            return await call_next(request)

        method = request.method.upper()
        if method not in UNSAFE_METHODS:
            return await call_next(request)

        path = request.url.path
        if self._is_exempt(path):
            return await call_next(request)

        origin = request.headers.get("origin")
        referer = request.headers.get("referer")

        if origin:
            if not self._origin_allowed(origin):
                logger.info("CSRF reject: origin=%s path=%s method=%s", origin, path, method)
                return self._reject("origin_not_allowed")
        elif referer:
            if not self._referer_allowed(referer):
                logger.info("CSRF reject: referer=%s path=%s method=%s", referer, path, method)
                return self._reject("referer_not_allowed")
        # else: no Origin and no Referer → not a browser-initiated request;
        # CSRF is not applicable. Fall through to the double-submit check,
        # which only enforces when the caller actually presents cookies.

        # Enforce double-submit only when the caller brings a cookie the server
        # might treat as an auth factor. This keeps pure-Bearer callers working
        # today and closes the gap automatically if session cookies are added.
        if self._has_auth_cookie(request) or CSRF_COOKIE_NAME in request.cookies:
            if not self._double_submit_valid(request):
                logger.info(
                    "CSRF reject: double-submit mismatch path=%s method=%s has_cookie=%s has_header=%s",
                    path,
                    method,
                    CSRF_COOKIE_NAME in request.cookies,
                    CSRF_HEADER_NAME in request.headers,
                )
                return self._reject("csrf_token_missing_or_mismatch")

        return await call_next(request)


def setup_csrf_cookie(
    response: Response,
    *,
    token: Optional[str] = None,
    secure: bool = True,
    max_age: int = 60 * 60 * 12,  # 12 hours
) -> str:
    """Issue a new CSRF token and set it as a SameSite=Strict cookie.

    Returns the raw token so the caller can also return it in the response
    body for SPA bootstrapping.
    """
    value = token or generate_csrf_token()
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=value,
        httponly=False,  # SPA reads the token to echo in X-CSRF-Token
        secure=secure,
        samesite="strict",
        path="/",
        max_age=max_age,
    )
    return value
