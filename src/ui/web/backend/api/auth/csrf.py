"""
CSRF token endpoint (FLY-24 / H2).

Issues a CSRF token via a SameSite=Strict, Secure cookie and returns the
raw value in the response body. The SPA is expected to read the cookie
value and echo it on subsequent mutating requests in the ``X-CSRF-Token``
header (double-submit pattern — see middleware/csrf.py).

The endpoint is safe (GET) so it is not subject to CSRF enforcement
itself; it also does not require authentication, because the token has
no value to an attacker: it is only meaningful when paired with an
already-valid session cookie on the legitimate user's browser.
"""

import os

from fastapi import APIRouter, Request, Response

from middleware.csrf import (
    CSRF_COOKIE_NAME,
    generate_csrf_token,
    setup_csrf_cookie,
)

router = APIRouter()


def _default_secure_flag(request: Request) -> bool:
    """Cookies should be Secure in production, relaxed only for local HTTP."""
    scheme = request.url.scheme
    forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
    if scheme == "https" or forwarded_proto == "https":
        return True
    host = request.url.hostname or ""
    # Only disable Secure on genuinely local hostnames.
    if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return False
    # Default to Secure so we fail closed on misconfigured reverse proxies.
    return True


@router.get("/csrf")
async def issue_csrf_token(request: Request, response: Response):
    """
    Issue (or rotate) a CSRF token.

    If the caller already presents a valid CSRF cookie we keep it, otherwise
    we generate a new one. Either way the response sets the cookie with
    SameSite=Strict so browsers will only attach it on same-site requests.
    """
    existing = request.cookies.get(CSRF_COOKIE_NAME)
    token = existing or generate_csrf_token()
    secure = _default_secure_flag(request)
    setup_csrf_cookie(response, token=token, secure=secure)
    return {
        "ok": True,
        "csrfToken": token,
        "headerName": "X-CSRF-Token",
        "cookieName": CSRF_COOKIE_NAME,
    }
