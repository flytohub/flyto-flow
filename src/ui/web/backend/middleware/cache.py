"""
API Cache-Control Headers Middleware

Sets appropriate Cache-Control headers on read-only GET API responses.
Mutation endpoints and auth-dependent routes are never cached.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# (prefix, Cache-Control value)
_CACHEABLE_RULES: list[tuple[str, str]] = [
    ("/api/modules/", "public, max-age=300"),       # Module catalog — 5 min
    ("/api/core/version", "public, max-age=3600"),   # Version — 1 hour
    ("/api/core/health", "public, max-age=10"),      # Health check — 10 sec
    ("/api/capabilities", "public, max-age=60"),     # Capabilities — 1 min
]


class APICacheMiddleware(BaseHTTPMiddleware):
    """
    Attach Cache-Control headers to safe, cacheable GET endpoints.

    Only applies when:
    - Method is GET
    - Path matches a known cacheable prefix
    - Response status is 2xx
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        if request.method != "GET":
            return response

        # Don't cache error responses
        if response.status_code < 200 or response.status_code >= 300:
            return response

        path = request.url.path
        for prefix, cache_value in _CACHEABLE_RULES:
            if path.startswith(prefix):
                response.headers["Cache-Control"] = cache_value
                break

        return response
