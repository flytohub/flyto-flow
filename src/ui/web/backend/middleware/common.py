"""
Common Middleware & CORS Setup

Local middleware and CORS assembly for Flyto2 Flow.

Change middleware here → both cloud and local pick it up automatically.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from middleware.cache import APICacheMiddleware
from middleware.csrf import CSRFProtectionMiddleware
from middleware.rate_limiter import RateLimiterMiddleware, RateLimitConfig
from middleware.security_headers import SecurityHeadersMiddleware
from middleware.trailing_slash import TrailingSlashMiddleware
from services.observability.logging_middleware import RequestLoggingMiddleware
from api.errors import register_exception_handlers


# --- CORS shared constants (single source of truth) ---

CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

# Headers accepted by the local browser client.
CORS_BASE_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-Request-ID",
    "X-Requested-With",
    "Accept",
    "Accept-Language",
    "Origin",
]


def setup_cors(
    app: FastAPI,
    *,
    origins: list[str],
    extra_headers: list[str] | None = None,
    expose_headers: list[str] | None = None,
) -> None:
    """
    Register CORS middleware with local defaults.

    Methods and base headers are defined once here.

    Args:
        app: FastAPI application instance.
        origins: Allowed origins for this deployment mode.
        extra_headers: Additional allowed headers beyond the shared base.
        expose_headers: Headers to expose to the browser.
    """
    allow_headers = list(CORS_BASE_HEADERS)
    if extra_headers:
        allow_headers.extend(extra_headers)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=allow_headers,
        expose_headers=expose_headers or [],
    )


def setup_common_middleware(
    app: FastAPI,
    *,
    extra_logging_excludes: list[str] | None = None,
    csrf_allowed_origins: list[str] | None = None,
    csrf_exempt_prefixes: list[str] | None = None,
) -> None:
    """
    Register middleware for Flyto2 Flow.

    Starlette executes middleware in reverse registration order
    (last registered is outermost and runs first).

    Args:
        app: FastAPI application instance.
        extra_logging_excludes: Additional paths to exclude from request logging.
        csrf_allowed_origins: Origin allowlist for CSRF enforcement. Should mirror
            the CORS origin allowlist for this deployment mode.
        csrf_exempt_prefixes: Additional local path prefixes to exempt from CSRF.
    """
    # --- API Cache-Control headers ---
    app.add_middleware(APICacheMiddleware)

    # --- Compression ---
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # --- URL normalization ---
    app.add_middleware(TrailingSlashMiddleware)

    # --- Security headers (HSTS, CSP, X-Frame-Options, etc.) ---
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=True, enable_csp=True)

    # --- Rate limiting ---
    rate_limit_config = RateLimitConfig(
        default_rpm=60,
        local_rpm=120,
        enabled=True,
    )
    app.add_middleware(RateLimiterMiddleware, config=rate_limit_config)

    # --- CSRF protection (FLY-24 / H2) ---
    # Registered AFTER RateLimiter so CSRF sits OUTSIDE rate limiting in the
    # request flow (see module docstring about reverse-order dispatch):
    # cross-origin attack traffic is rejected before it counts against the
    # legitimate user's rate quota.
    app.add_middleware(
        CSRFProtectionMiddleware,
        allowed_origins=csrf_allowed_origins or [],
        exempt_prefixes=csrf_exempt_prefixes or [],
    )

    # --- Request logging ---
    exclude_paths = ["/api/health", "/health"]
    if extra_logging_excludes:
        exclude_paths.extend(extra_logging_excludes)

    app.add_middleware(
        RequestLoggingMiddleware,
        log_request_body=False,
        log_response_body=False,
        exclude_paths=exclude_paths,
    )

    # --- Exception handlers ---
    register_exception_handlers(app)
