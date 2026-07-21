"""
Shared HTTP Client with Connection Pool, Retry, Circuit Breaker

Provides a centralized HTTP client for all Enterprise providers with:
- Connection pooling for efficient resource usage
- Automatic retry with exponential backoff
- Circuit breaker pattern for fault tolerance
- Health check utilities
"""

import time
import logging
import asyncio
import random
import os
from typing import Optional, Dict, Any
from functools import lru_cache

import httpx

from gateway.request_context import get_authorization_header

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_LIMITS = httpx.Limits(
    max_keepalive_connections=20,
    max_connections=100,
    keepalive_expiry=30.0,
)

DEFAULT_TIMEOUT = httpx.Timeout(
    timeout=10.0,
    connect=5.0,
    read=10.0,
    write=5.0,
)

RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT = 1
RETRY_MAX_WAIT = 10


# =============================================================================
# Exceptions (Legacy - kept for backward compatibility)
# =============================================================================

class ServiceUnavailableError(Exception):
    """
    Raised when a service is unavailable (circuit breaker open).

    NOTE: For new code, prefer using gateway.exceptions.ServiceUnavailableError
    which provides richer error information via ProviderException.
    """
    pass


class RetryableError(Exception):
    """Base class for errors that should trigger retry."""
    pass


# =============================================================================
# Exception Conversion Helpers
# =============================================================================

def to_provider_exception(error: Exception, backend_url: str = ""):
    """
    Convert HTTP client exceptions to ProviderException.

    Args:
        error: The original exception
        backend_url: Backend URL for context

    Returns:
        ProviderException instance
    """
    from gateway.exceptions import (
        ServiceUnavailableError as ProviderServiceError,
        ErrorCode,
        ProviderException,
    )

    if isinstance(error, ServiceUnavailableError):
        return ProviderServiceError(
            service_name="enterprise-backend",
            message=str(error),
            original_error=error,
        )

    if isinstance(error, httpx.TimeoutException):
        return ProviderServiceError(
            service_name="enterprise-backend",
            message=f"Request timeout to {backend_url}",
            original_error=error,
        )

    if isinstance(error, httpx.ConnectError):
        return ProviderServiceError(
            service_name="enterprise-backend",
            message=f"Connection failed to {backend_url}",
            original_error=error,
        )

    return ProviderException(
        code=ErrorCode.EXTERNAL_SERVICE_ERROR,
        message=str(error),
        http_status=503,
        original_error=error,
    )


# =============================================================================
# Circuit Breaker
# =============================================================================

class CircuitBreaker:
    """
    Simple circuit breaker implementation.

    States:
    - closed: Normal operation, requests go through
    - open: Too many failures, requests are blocked
    - half-open: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"
        self.half_open_calls = 0
        self._lock = asyncio.Lock()

    async def record_failure(self) -> None:
        """Record a failed request."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == "half-open":
                # Failed during half-open, go back to open
                self.state = "open"
                self.half_open_calls = 0
                logger.warning("Circuit breaker: half-open -> open (failure during test)")
            elif self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker: closed -> open (threshold {self.failure_threshold} reached)")

    async def record_success(self) -> None:
        """Record a successful request."""
        async with self._lock:
            if self.state == "half-open":
                self.success_count += 1
                if self.success_count >= self.half_open_max_calls:
                    # Enough successes, close the circuit
                    self.state = "closed"
                    self.failure_count = 0
                    self.success_count = 0
                    self.half_open_calls = 0
                    logger.info("Circuit breaker: half-open -> closed (recovered)")
            else:
                # Reset failure count on success
                self.failure_count = max(0, self.failure_count - 1)

    async def can_execute(self) -> bool:
        """Check if request can proceed."""
        async with self._lock:
            if self.state == "closed":
                return True

            if self.state == "open":
                # Check if reset timeout has passed
                if self.last_failure_time is None:
                    return True

                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.reset_timeout:
                    self.state = "half-open"
                    self.half_open_calls = 0
                    self.success_count = 0
                    logger.info("Circuit breaker: open -> half-open (testing recovery)")
                    return True
                return False

            # half-open: allow limited requests
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
        }


# =============================================================================
# Client Pool Management
# =============================================================================

_clients: Dict[str, httpx.AsyncClient] = {}
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_client_lock = asyncio.Lock()


async def get_shared_client(backend_url: str) -> httpx.AsyncClient:
    """
    Get or create a shared HTTP client for the given backend URL.

    Args:
        backend_url: Base URL of the backend service

    Returns:
        Shared httpx.AsyncClient instance with connection pooling
    """
    backend_url = backend_url.rstrip("/")

    async with _client_lock:
        if backend_url not in _clients or _clients[backend_url].is_closed:
            _clients[backend_url] = httpx.AsyncClient(
                base_url=backend_url,
                limits=DEFAULT_LIMITS,
                timeout=DEFAULT_TIMEOUT,
            )
            logger.info(f"Created shared HTTP client for {backend_url}")

        return _clients[backend_url]


def get_circuit_breaker(backend_url: str) -> CircuitBreaker:
    """
    Get or create a circuit breaker for the given backend URL.

    Args:
        backend_url: Base URL of the backend service

    Returns:
        CircuitBreaker instance for the backend
    """
    backend_url = backend_url.rstrip("/")

    if backend_url not in _circuit_breakers:
        _circuit_breakers[backend_url] = CircuitBreaker()
        logger.debug(f"Created circuit breaker for {backend_url}")

    return _circuit_breakers[backend_url]


async def close_all_clients() -> None:
    """Close all shared HTTP clients. Call this on application shutdown."""
    async with _client_lock:
        for url, client in _clients.items():
            if not client.is_closed:
                await client.aclose()
                logger.info(f"Closed HTTP client for {url}")
        _clients.clear()


def reset_circuit_breakers() -> None:
    """Reset all circuit breakers. Call this on application shutdown or for testing."""
    _circuit_breakers.clear()
    logger.info("All circuit breakers reset")


# =============================================================================
# Request Helpers
# =============================================================================

async def resilient_request(
    backend_url: str,
    method: str,
    path: str,
    max_retries: int = RETRY_ATTEMPTS,
    **kwargs,
) -> httpx.Response:
    """
    Make an HTTP request with retry and circuit breaker protection.

    Args:
        backend_url: Base URL of the backend service
        method: HTTP method (GET, POST, etc.)
        path: Request path
        max_retries: Maximum retry attempts
        **kwargs: Additional arguments passed to httpx.request

    Returns:
        httpx.Response

    Raises:
        ServiceUnavailableError: If circuit breaker is open
        httpx.HTTPError: If all retries fail
    """
    cb = get_circuit_breaker(backend_url)

    # Enterprise APIs authorize the end user, not the gateway process. Carry
    # the inbound Bearer token across the provider boundary unless a caller
    # intentionally supplied another Authorization header.
    authorization = get_authorization_header()
    if authorization:
        headers = dict(kwargs.get("headers") or {})
        if not any(name.lower() == "authorization" for name in headers):
            headers["Authorization"] = authorization
            kwargs["headers"] = headers

    service_token = os.getenv("FLYTO_ENTERPRISE_SERVICE_TOKEN", "").strip()
    if service_token:
        headers = dict(kwargs.get("headers") or {})
        if not any(name.lower() == "x-flyto2-service-token" for name in headers):
            headers["X-Flyto2-Service-Token"] = service_token
            kwargs["headers"] = headers

    # Check circuit breaker
    if not await cb.can_execute():
        raise ServiceUnavailableError(
            f"Service {backend_url} is unavailable (circuit breaker open)"
        )

    client = await get_shared_client(backend_url)
    last_error: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            response = await client.request(method, path, **kwargs)

            # Record success for circuit breaker
            await cb.record_success()

            return response

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            last_error = e
            await cb.record_failure()

            if attempt < max_retries - 1:
                # SECURITY: Add jitter to prevent thundering herd
                base_wait = min(RETRY_MAX_WAIT, RETRY_MIN_WAIT * (2 ** attempt))
                wait_time = base_wait + random.uniform(0, base_wait * 0.5)
                logger.warning(
                    f"Request to {backend_url}{path} failed (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {wait_time:.2f}s: {e}"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"Request to {backend_url}{path} failed after {max_retries} attempts: {e}"
                )

        except httpx.HTTPStatusError as e:
            # Don't retry for client errors (4xx), but do retry for server errors (5xx)
            if e.response.status_code >= 500:
                last_error = e
                await cb.record_failure()

                if attempt < max_retries - 1:
                    # SECURITY: Add jitter to prevent thundering herd
                    base_wait = min(RETRY_MAX_WAIT, RETRY_MIN_WAIT * (2 ** attempt))
                    wait_time = base_wait + random.uniform(0, base_wait * 0.5)
                    logger.warning(
                        f"Server error from {backend_url}{path} (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time:.2f}s: {e.response.status_code}"
                    )
                    await asyncio.sleep(wait_time)
            else:
                # Client error, don't retry
                await cb.record_success()  # Service is responding
                raise

    # All retries exhausted
    if last_error:
        raise last_error
    raise RuntimeError("Unexpected state: no response and no error")


# =============================================================================
# Health Check
# =============================================================================

async def check_backend_health(backend_url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Check health of a backend service.

    Args:
        backend_url: Base URL of the backend service
        timeout: Health check timeout in seconds

    Returns:
        Dict with health status
    """
    backend_url = backend_url.rstrip("/")
    cb = get_circuit_breaker(backend_url)

    try:
        client = await get_shared_client(backend_url)
        response = await client.get("/health", timeout=timeout)

        is_healthy = response.status_code == 200

        return {
            "url": backend_url,
            "healthy": is_healthy,
            "status_code": response.status_code,
            "circuit_breaker": cb.get_state(),
        }

    except Exception as e:
        return {
            "url": backend_url,
            "healthy": False,
            "error": str(e),
            "circuit_breaker": cb.get_state(),
        }


async def check_all_backends_health() -> Dict[str, Any]:
    """
    Check health of all registered backend services.

    Returns:
        Dict with health status for all backends
    """
    results = {}

    for url in list(_clients.keys()):
        results[url] = await check_backend_health(url)

    all_healthy = all(r.get("healthy", False) for r in results.values())

    return {
        "ok": all_healthy,
        "backends": results,
    }
