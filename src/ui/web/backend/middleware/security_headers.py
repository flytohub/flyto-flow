"""
Security Headers Middleware

Adds security-related HTTP headers to all responses.
Helps protect against common web vulnerabilities.

CSP Nonce Support:
    When FLYTO_CSP_NONCE=true, this middleware generates a unique nonce
    for each request, enabling strict CSP without 'unsafe-inline'.
    The nonce is available via request.state.csp_nonce for templates.
"""

import logging
import os
import secrets
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Environment-based CSP mode
# When True, use nonces instead of unsafe-inline for stricter security
# Auto-enable on Cloud Run (K_SERVICE is set by Cloud Run runtime)
_explicit_nonce = os.environ.get('FLYTO_CSP_NONCE', '').lower()
if _explicit_nonce:
    USE_CSP_NONCE = _explicit_nonce == 'true'
else:
    USE_CSP_NONCE = bool(os.environ.get('K_SERVICE'))


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to HTTP responses.

    Headers added:
    - X-Content-Type-Options: Prevents MIME-sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Legacy XSS filter (for older browsers)
    - Strict-Transport-Security: Enforces HTTPS
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Restricts browser features
    - Content-Security-Policy: XSS and injection protection (basic)
    """

    def __init__(
        self,
        app,
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        enable_csp: bool = True,
        csp_policy: str = None,
        use_nonce: bool = None,
    ):
        """
        Initialize security headers middleware.

        Args:
            app: ASGI application
            enable_hsts: Whether to add HSTS header
            hsts_max_age: HSTS max-age in seconds
            enable_csp: Whether to add CSP header
            csp_policy: Custom CSP policy string
            use_nonce: Use nonce-based CSP (env FLYTO_CSP_NONCE)
        """
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.enable_csp = enable_csp
        self.use_nonce = use_nonce if use_nonce is not None else USE_CSP_NONCE
        self._custom_csp = csp_policy

    def _generate_nonce(self) -> str:
        """Generate a cryptographically secure nonce for CSP."""
        return secrets.token_urlsafe(16)

    def _build_csp_policy(self, nonce: Optional[str] = None) -> str:
        """
        Build Content-Security-Policy based on configuration.

        Args:
            nonce: Optional nonce for strict CSP mode

        Returns:
            CSP policy string
        """
        if self._custom_csp:
            return self._custom_csp

        # Build CSP directives
        directives = [
            "default-src 'self'",
        ]

        if nonce:
            # SECURITY: Strict CSP with nonce - no unsafe-inline
            # All inline scripts/styles must include nonce="<value>" attribute
            directives.extend([
                f"script-src 'self' 'nonce-{nonce}' 'strict-dynamic'",
                f"style-src 'self' 'nonce-{nonce}'",
            ])
            logger.debug(f"CSP: Using nonce-based policy (nonce={nonce[:8]}...)")
        else:
            # No unsafe-eval in any environment — pre-compiled Vue templates only
            directives.extend([
                "script-src 'self' 'unsafe-inline'",
                "style-src 'self' 'unsafe-inline'",
            ])

        # Common directives for both modes
        directives.extend([
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' https: wss:",  # API calls and WebSockets
            "frame-ancestors 'none'",  # Prevent clickjacking via iframe
            "base-uri 'self'",  # Prevent base tag injection
            "form-action 'self'",  # Restrict form submissions
        ])

        return "; ".join(directives)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers to response."""
        # Generate nonce if using strict CSP mode
        nonce = None
        if self.use_nonce:
            nonce = self._generate_nonce()
            # Store nonce in request state for templates/handlers to use
            request.state.csp_nonce = nonce

        response = await call_next(request)

        # Anti-MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Allow popups (Google OAuth) to communicate back to opener
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"

        # Disable some browser features for security
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )

        # HSTS - only for HTTPS responses
        if self.enable_hsts:
            # Check if request is over HTTPS (directly or via proxy)
            is_https = (
                request.url.scheme == "https" or
                request.headers.get("X-Forwarded-Proto") == "https"
            )
            if is_https:
                response.headers["Strict-Transport-Security"] = (
                    f"max-age={self.hsts_max_age}; includeSubDomains"
                )

        # Content Security Policy
        if self.enable_csp:
            csp_policy = self._build_csp_policy(nonce)
            response.headers["Content-Security-Policy"] = csp_policy

        return response


def get_csp_nonce(request: Request) -> Optional[str]:
    """
    Helper function to get CSP nonce from request state.

    Usage in route handlers:
        @app.get("/page")
        async def page(request: Request):
            nonce = get_csp_nonce(request)
            return templates.TemplateResponse(
                "page.html",
                {"request": request, "csp_nonce": nonce}
            )

    Usage in templates:
        <script nonce="{{ csp_nonce }}">...</script>
        <style nonce="{{ csp_nonce }}">...</style>
    """
    return getattr(request.state, 'csp_nonce', None)
