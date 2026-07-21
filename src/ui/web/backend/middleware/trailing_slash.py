"""
Trailing Slash Middleware

Normalizes API routes to handle both with and without trailing slash.
This ensures consistent behavior for /api/templates and /api/templates/
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse


class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle trailing slash normalization for API routes.

    - Redirects /api/templates to /api/templates/ (HTTP 307 for POST/PUT/DELETE)
    - Applies to all HTTP methods on /api/* routes
    - Does not affect routes with path parameters (e.g., /api/templates/{id})
    """

    # Routes that should have trailing slash added
    NORMALIZE_ROUTES = {
        "/api/templates",
        "/api/executions",
        "/api/workflows",
        "/api/trials",
        "/api/plugins",
        "/api/notifications",
        "/api/chat",
        "/api/config",
        "/api/reviews",
        "/api/user-tools",
        "/api/orders",
        "/api/invite-keys",
        "/api/reports",
        "/api/debug",
        "/api/variables",
        "/api/triggers",
        "/api/organizations",
        "/api/metrics",
        "/api/alerts",
        "/api/traces",
        "/api/versions",
        "/api/evidence",
        "/api/replay",
        "/api/breakpoints",
        "/api/lineage",
        "/api/testing",
        "/api/versioning",
        "/api/api-keys",
        "/api/licenses",
        "/api/audit",
        "/api/tools",
        "/api/projects",
        "/api/storage",
        "/api/subscriptions",
        # Note: /api/telemetry removed - POST requests don't work well with 307 redirects
    }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Redirect API routes without trailing slash to with trailing slash
        if (
            path.startswith("/api/") and
            not path.endswith("/") and
            path in self.NORMALIZE_ROUTES
        ):
            # Build redirect URL with trailing slash
            new_path = path + "/"
            if request.url.query:
                new_path = f"{new_path}?{request.url.query}"

            # Use 307 for non-GET to preserve method and body
            status_code = 307 if request.method != "GET" else 308
            return RedirectResponse(url=new_path, status_code=status_code)

        return await call_next(request)
