"""
Logging Middleware

FastAPI middleware for request logging and context propagation.
"""

import time
import uuid
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from services.observability.structured_logging import (
    ExecutionLogContext,
    set_context,
    clear_context,
    get_logger,
)

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log requests and set up request context.

    Extracts trace_id from headers (X-Trace-ID, X-Request-ID) or generates one.
    Sets up execution context for correlated logging.
    """

    def __init__(
        self,
        app,
        log_request_body: bool = False,
        log_response_body: bool = False,
        exclude_paths: Optional[list] = None,
    ):
        """Initialize with logging options and excluded paths."""
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.exclude_paths = exclude_paths or ["/api/health", "/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Extract or generate trace ID
        trace_id = (
            request.headers.get("X-Trace-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )

        # Extract execution context from headers if present
        exec_id = request.headers.get("X-Execution-ID")

        # Set up context
        context = ExecutionLogContext(
            exec_id=exec_id or f"req-{trace_id[:8]}",
            trace_id=trace_id,
            workspace_id="local-workspace",
        )
        set_context(context)

        start_time = time.time()

        try:
            # Log request
            logger.info(
                "Request started",
                event="request_started",
                method=request.method,
                path=request.url.path,
                query=str(request.query_params) if request.query_params else None,
                client_ip=request.client.host if request.client else None,
            )

            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log response
            logger.info(
                "Request completed",
                event="request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            # Add trace ID to response headers
            response.headers["X-Trace-ID"] = trace_id

            return response

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Request failed: {e}",
                event="request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error=str(e),
            )
            raise

        finally:
            clear_context()


class ExecutionContextMiddleware(BaseHTTPMiddleware):
    """
    Lightweight middleware that only sets execution context.

    Use this when you don't need request logging but want context propagation.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract trace ID
        trace_id = (
            request.headers.get("X-Trace-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )

        # Extract execution context
        exec_id = request.headers.get("X-Execution-ID")

        if exec_id:
            context = ExecutionLogContext(
                exec_id=exec_id,
                trace_id=trace_id,
                workspace_id="local-workspace",
            )
            set_context(context)

        try:
            response = await call_next(request)
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            if exec_id:
                clear_context()
