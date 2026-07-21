"""Request-scoped context shared by gateway provider calls."""

from contextvars import ContextVar, Token
from typing import Optional


_authorization_header: ContextVar[Optional[str]] = ContextVar(
    "gateway_authorization_header",
    default=None,
)


def bind_authorization_header(value: Optional[str]) -> Token:
    """Bind an incoming Bearer header for the lifetime of one request."""
    authorization = value if value and value.startswith("Bearer ") else None
    return _authorization_header.set(authorization)


def reset_authorization_header(token: Token) -> None:
    """Restore the authorization context that preceded the current request."""
    _authorization_header.reset(token)


def get_authorization_header() -> Optional[str]:
    """Return the current request's Bearer header, when one is bound."""
    return _authorization_header.get()
