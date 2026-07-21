"""ASGI middleware that scopes gateway context to one request."""

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from gateway.request_context import (
    bind_authorization_header,
    reset_authorization_header,
)


class GatewayRequestContextMiddleware:
    """Expose incoming authentication to downstream enterprise providers."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        authorization = Headers(scope=scope).get("authorization")
        token = bind_authorization_header(authorization)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_authorization_header(token)
