"""Fixed single-workspace context for CE.

The fixed identifier scopes local records. Extended editions replace the
application entry point and compose their own context downstream.
"""

from gateway.providers.base import WorkspaceContext


LOCAL_WORKSPACE = WorkspaceContext(
    id="local-workspace",
)


async def get_local_principal() -> WorkspaceContext:
    return LOCAL_WORKSPACE


async def get_optional_local_principal() -> WorkspaceContext:
    return LOCAL_WORKSPACE


async def get_local_actor() -> dict:
    """FastAPI dependency for legacy handlers that expect a dictionary actor."""
    return LOCAL_WORKSPACE.model_dump()


def local_principal_dict() -> dict:
    return LOCAL_WORKSPACE.model_dump()
