"""
Rate Limiter Middleware

Implements token bucket algorithm for API rate limiting.
Uses a process-local token bucket. CE never discovers or connects to Redis.
"""
import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional, Callable, Protocol
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    # Default limits (requests per minute)
    default_rpm: int = 60
    # Local workspace limit
    local_rpm: int = 120
    # Sensitive operation limits (SECURITY: protect credential reveal, exports)
    sensitive_reveal_rpm: int = 10  # 10 credential reveals per minute
    sensitive_export_rpm: int = 5  # 5 exports per minute
    # Burst allowance (temporary spike)
    burst_multiplier: float = 1.5
    # Window size in seconds
    window_seconds: int = 60
    # Enable rate limiting
    enabled: bool = True
    # Trusted proxy networks (for X-Forwarded-For validation)
    trusted_proxy_networks: tuple = (
        "10.",      # Private network
        "169.254.", # Link-local network
        "172.16.",  # Private network
        "172.17.",  # Docker default
        "172.18.",
        "172.19.",
        "172.20.",
        "172.21.",
        "172.22.",
        "172.23.",
        "172.24.",
        "172.25.",
        "172.26.",
        "172.27.",
        "172.28.",
        "172.29.",
        "172.30.",
        "172.31.",
        "192.168.", # Private network
        "127.",     # Localhost
    )


@dataclass
class RateLimitResult:
    """Result of a rate limit check"""
    allowed: bool
    remaining: int
    reset_seconds: int


class RateLimiterBackend(Protocol):
    """Protocol for the local rate limiter backend."""

    async def consume(
        self, key: str, limit: int, window_seconds: int
    ) -> RateLimitResult: ...


# ---------------------------------------------------------------------------
# In-memory backend (token bucket, single instance only)
# ---------------------------------------------------------------------------

@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    tokens: float
    last_update: float
    max_tokens: float
    refill_rate: float  # tokens per second

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        Returns True if successful, False if rate limited.
        """
        now = time.time()
        time_passed = now - self.last_update

        # Refill tokens based on time passed
        self.tokens = min(
            self.max_tokens,
            self.tokens + time_passed * self.refill_rate
        )
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    @property
    def remaining(self) -> int:
        """Get remaining tokens (approximate)"""
        return max(0, int(self.tokens))

    @property
    def reset_time(self) -> int:
        """Get seconds until bucket refills"""
        if self.tokens >= self.max_tokens:
            return 0
        needed = self.max_tokens - self.tokens
        return int(needed / self.refill_rate) + 1


class InMemoryBackend:
    """In-memory store for rate limit buckets (single-instance only)"""

    MAX_BUCKETS = 10_000  # Cap to prevent memory exhaustion under DDoS

    def __init__(self):
        """Initialize empty bucket store with cleanup tracking."""
        self.buckets: Dict[str, TokenBucket] = {}
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()

    async def consume(
        self, key: str, limit: int, window_seconds: int
    ) -> RateLimitResult:
        """Consume one request from the bucket."""
        max_tokens = limit * 1.5  # burst multiplier
        refill_rate = limit / window_seconds
        bucket = self.get_bucket(key, max_tokens, refill_rate)
        allowed = bucket.consume()
        return RateLimitResult(
            allowed=allowed,
            remaining=bucket.remaining,
            reset_seconds=bucket.reset_time,
        )

    def get_bucket(
        self,
        key: str,
        max_tokens: float,
        refill_rate: float
    ) -> TokenBucket:
        """Get or create a bucket for a key"""
        self._maybe_cleanup()

        if key not in self.buckets:
            if len(self.buckets) >= self.MAX_BUCKETS:
                # Evict oldest bucket to make room
                oldest_key = min(
                    self.buckets,
                    key=lambda k: self.buckets[k].last_update
                )
                del self.buckets[oldest_key]
            self.buckets[key] = TokenBucket(
                tokens=max_tokens,
                last_update=time.time(),
                max_tokens=max_tokens,
                refill_rate=refill_rate
            )
        return self.buckets[key]

    def _maybe_cleanup(self):
        """Periodically clean up old buckets"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        self._last_cleanup = now
        cutoff = now - 3600  # Remove buckets older than 1 hour

        keys_to_remove = [
            key for key, bucket in self.buckets.items()
            if bucket.last_update < cutoff
        ]

        for key in keys_to_remove:
            del self.buckets[key]

        if keys_to_remove:
            logger.debug(f"Cleaned up {len(keys_to_remove)} expired rate limit buckets")


# Backward-compatible alias for tests and external imports
RateLimiterStore = InMemoryBackend


def _create_backend() -> RateLimiterBackend:
    """Create CE's process-local rate limiter."""
    return InMemoryBackend()


# Global backend instance (lazy-created once)
_backend: Optional[RateLimiterBackend] = None


def _get_backend() -> RateLimiterBackend:
    global _backend
    if _backend is None:
        _backend = _create_backend()
    return _backend


def is_trusted_proxy(ip: str, config: RateLimitConfig) -> bool:
    """Check if an IP is from a trusted proxy network."""
    if not ip:
        return False
    return any(ip.startswith(prefix) for prefix in config.trusted_proxy_networks)


def get_client_identifier(request: Request, config: RateLimitConfig = None) -> str:
    """
    Get a unique identifier for the client.
    Uses only the direct or trusted-proxy client address.

    SECURITY: Only trusts X-Forwarded-For from known proxy networks.
    """
    if config is None:
        config = RateLimitConfig()

    # Get direct client IP
    direct_ip = request.client.host if request.client else 'unknown'

    # SECURITY: Only trust X-Forwarded-For from known proxy networks
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded and is_trusted_proxy(direct_ip, config):
        # Trusted proxy - use first IP in chain (original client)
        client_ip = forwarded.split(',')[0].strip()
    else:
        # Untrusted or no proxy - use direct connection IP
        client_ip = direct_ip

    return f"ip:{client_ip}"


def get_rate_limit_for_path(path: str, config: RateLimitConfig) -> int:
    """Determine rate limit based on request path"""
    # SECURITY: Sensitive operations (credential reveal, exports) get strict limits
    if '/reveal' in path or '/credentials/' in path and path.endswith('/reveal'):
        return config.sensitive_reveal_rpm
    if '/export' in path:
        return config.sensitive_export_rpm

    # Health check endpoints
    if '/health' in path:
        return config.default_rpm

    return config.local_rpm


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm.

    Adds these headers to responses:
    - X-RateLimit-Limit: Maximum requests per window
    - X-RateLimit-Remaining: Remaining requests in current window
    - X-RateLimit-Reset: Seconds until limit resets
    """

    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        """Initialize middleware with optional rate limit configuration."""
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.backend = _get_backend()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.config.enabled:
            return await call_next(request)

        # Skip rate limiting for certain paths
        path = request.url.path
        if self._should_skip(path):
            return await call_next(request)

        # Get client identifier and rate limit
        client_id = get_client_identifier(request, self.config)
        limit = get_rate_limit_for_path(path, self.config)

        # Build bucket key: client + path group
        path_group = path.split('/')[2] if len(path.split('/')) > 2 else 'default'
        bucket_key = f"{client_id}:{path_group}"

        # Check the process-local token bucket.
        result = await self.backend.consume(
            bucket_key, limit, self.config.window_seconds
        )

        if result.allowed:
            response = await call_next(request)
            self._add_headers(response, limit, result)
            return response
        else:
            logger.warning("Rate limit exceeded")
            return self._rate_limit_response(limit, result)

    def _should_skip(self, path: str) -> bool:
        """Check if path should skip rate limiting"""
        skip_paths = [
            '/docs',
            '/openapi.json',
            '/redoc',
            '/static',
            '/favicon.ico',
            '/api/health',
            '/api/app/version',
        ]
        return any(path.startswith(p) for p in skip_paths)

    def _add_headers(
        self,
        response: Response,
        limit: int,
        result: RateLimitResult,
    ):
        """Add rate limit headers to response"""
        response.headers['X-RateLimit-Limit'] = str(limit)
        response.headers['X-RateLimit-Remaining'] = str(result.remaining)
        response.headers['X-RateLimit-Reset'] = str(result.reset_seconds)

    def _rate_limit_response(self, limit: int, result: RateLimitResult) -> JSONResponse:
        """Create rate limit exceeded response"""
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "retry_after": result.reset_seconds
            },
            headers={
                'X-RateLimit-Limit': str(limit),
                'X-RateLimit-Remaining': '0',
                'X-RateLimit-Reset': str(result.reset_seconds),
                'Retry-After': str(result.reset_seconds)
            }
        )


def create_rate_limiter(
    default_rpm: int = 60,
    local_rpm: int = 120,
    enabled: bool = True
) -> RateLimiterMiddleware:
    """
    Factory function to create rate limiter middleware.

    Args:
        default_rpm: Default requests per minute
        local_rpm: Requests per minute for local workspace API routes
        enabled: Whether rate limiting is enabled

    Returns:
        Configured RateLimiterMiddleware
    """
    config = RateLimitConfig(
        default_rpm=default_rpm,
        local_rpm=local_rpm,
        enabled=enabled
    )
    return lambda app: RateLimiterMiddleware(app, config)
