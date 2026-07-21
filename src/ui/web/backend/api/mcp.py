"""
HTTP transport for Flyto2 workflow MCP tools.

This route exposes workflows configured with trigger_type='mcp' through the
same JSON-RPC handler used by the stdio MCP bridge.
"""

import asyncio
import ipaddress
import os
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

import mcp_server


router = APIRouter(prefix="/mcp", tags=["MCP"])


def _media_ranges(accept: Optional[str]) -> set[str]:
    if not accept:
        return set()
    return {part.split(";", 1)[0].strip().lower() for part in accept.split(",") if part.strip()}


def _accepts(accept: Optional[str], media_type: str) -> bool:
    ranges = _media_ranges(accept)
    if not ranges:
        return False
    family = media_type.split("/", 1)[0]
    return "*/*" in ranges or media_type in ranges or f"{family}/*" in ranges


def _explicitly_accepts(accept: Optional[str], media_type: str) -> bool:
    ranges = _media_ranges(accept)
    family = media_type.split("/", 1)[0]
    return media_type in ranges or f"{family}/*" in ranges


def _allowed_origins() -> set[str]:
    raw = os.environ.get("FLYTO_MCP_ALLOWED_ORIGINS", "")
    return {origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()}


def _assert_origin_allowed(origin: Optional[str], host: Optional[str]) -> None:
    """Reject cross-origin browser requests unless explicitly allowed."""
    if not origin:
        return

    normalized_origin = origin.rstrip("/")
    allowed = _allowed_origins()
    if normalized_origin in allowed:
        return

    parsed = urlparse(normalized_origin)
    if host and parsed.netloc == host:
        return

    raise HTTPException(status_code=403, detail="Origin is not allowed for MCP access")


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Bearer token required for MCP access",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Bearer token required for MCP access",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def _is_offline_mode() -> bool:
    return os.environ.get("DEPLOYMENT_MODE", "").lower() == "offline"


def _is_loopback_host(host: Optional[str]) -> bool:
    if not host:
        return False
    normalized = host.strip().lower()
    if normalized in {"localhost", "testclient"}:
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _extract_mcp_token(authorization: Optional[str], request: Request) -> str:
    if authorization:
        return _extract_bearer_token(authorization)

    client_host = request.client.host if request.client else None
    if _is_offline_mode() and _is_loopback_host(client_host):
        return os.environ.get("FLYTO_OFFLINE_MCP_TOKEN", "offline-loopback")

    return _extract_bearer_token(authorization)


def _assert_post_accept_supported(accept: Optional[str]) -> None:
    if _accepts(accept, "application/json") and _accepts(accept, "text/event-stream"):
        return
    raise HTTPException(
        status_code=406,
        detail="MCP HTTP clients must accept application/json and text/event-stream",
    )


async def _dispatch_json_rpc(
    payload: dict,
    *,
    bearer_token: str,
    backend_url: str,
) -> Optional[dict]:
    return await asyncio.to_thread(
        mcp_server.handle_json_rpc_request,
        payload,
        bearer_token,
        backend_url,
    )


def _metadata_server_url(request: Request) -> str:
    try:
        return str(request.url_for("get_mcp_metadata")).rstrip("/")
    except Exception:
        return f"{str(request.base_url).rstrip('/')}/api/mcp"


def _api_base_url(server_url: str) -> str:
    if server_url.endswith("/api/mcp"):
        return server_url.removesuffix("/api/mcp")
    if server_url.endswith("/mcp"):
        return server_url.removesuffix("/mcp")
    return server_url


def _mcp_setup_payload(server_url: str) -> dict[str, Any]:
    backend_url = _api_base_url(server_url)
    common_env = {
        "FLYTO_BACKEND_URL": backend_url,
        "FLYTO_API_KEY": "<paste-runtime-token>",
    }
    return {
        "serverName": "flyto-workflows",
        "backendUrl": backend_url,
        "http": {
            "url": server_url,
            "headers": {"Authorization": "Bearer <paste-runtime-token>"},
        },
        "claudeCode": {
            "mcpServers": {
                "flyto-workflows": {
                    "command": "python",
                    "args": ["-m", "mcp_server"],
                    "cwd": "<flyto-cloud>/src/ui/web/backend",
                    "env": common_env,
                }
            }
        },
        "codexToml": (
            "[mcp_servers.flyto-workflows]\n"
            'command = "python"\n'
            'args = ["-m", "mcp_server"]\n'
            'cwd = "<flyto-cloud>/src/ui/web/backend"\n\n'
            "[mcp_servers.flyto-workflows.env]\n"
            f'FLYTO_BACKEND_URL = "{backend_url}"\n'
            'FLYTO_API_KEY = "<paste-runtime-token>"\n'
        ),
    }


async def _list_visible_tools(
    bearer_token: Optional[str],
    *,
    backend_url: str,
) -> tuple[list[dict[str, Any]], Optional[str]]:
    if not bearer_token:
        return [], None
    try:
        tools = await asyncio.to_thread(
            mcp_server._refresh_tools,
            bearer_token,
            force=True,
            backend_url=backend_url,
        )
    except Exception as exc:
        return [], str(exc)
    return tools, None


@router.get("")
@router.get("/")
async def get_mcp_metadata(
    request: Request,
    accept: Optional[str] = Header(default=None),
):
    """Return basic endpoint metadata for MCP client setup."""
    if _explicitly_accepts(accept, "text/event-stream"):
        return JSONResponse(
            {
                "detail": (
                    "SSE GET streams are not enabled for this endpoint; "
                    "use POST Streamable HTTP JSON-RPC."
                )
            },
            status_code=405,
            headers={"Allow": "POST"},
        )

    endpoint = _metadata_server_url(request)
    return {
        "name": "flyto-workflows",
        "title": "Flyto2 Workflow Tools",
        "transport": "streamable-http",
        "endpoint": "/api/mcp",
        "serverUrl": endpoint,
        "protocolVersions": list(mcp_server.SUPPORTED_PROTOCOL_VERSIONS),
        "capabilities": {"tools": {"listChanged": True}},
        "auth": {"type": "bearer"},
    }


@router.get("/status")
async def get_mcp_status(
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Return setup metadata and visible MCP tools for the current auth scope."""
    server_url = _metadata_server_url(request)
    backend_url = _api_base_url(server_url)
    bearer_token = None
    if authorization and authorization.startswith("Bearer "):
        bearer_token = authorization.split("Bearer ", 1)[1].strip() or None

    tools, tools_error = await _list_visible_tools(bearer_token, backend_url=backend_url)
    return {
        "ok": tools_error is None,
        "name": "flyto-workflows",
        "title": "Flyto2 Workflow Tools",
        "transport": "streamable-http",
        "endpoint": "/api/mcp",
        "serverUrl": server_url,
        "protocolVersions": list(mcp_server.SUPPORTED_PROTOCOL_VERSIONS),
        "capabilities": {"tools": {"listChanged": True}},
        "auth": {
            "type": "bearer",
            "required": True,
            "configured": bool(bearer_token),
            "tokenStored": False,
        },
        "setup": _mcp_setup_payload(server_url),
        "exposedToolCount": len(tools),
        "tools": tools,
        "toolsError": tools_error,
        "recentExecutions": [],
        "evidence": [],
    }


@router.post("")
@router.post("/")
async def post_mcp_json_rpc(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    accept: Optional[str] = Header(default=None),
    origin: Optional[str] = Header(default=None),
    host: Optional[str] = Header(default=None),
):
    """Handle MCP JSON-RPC over HTTP."""
    _assert_post_accept_supported(accept)
    _assert_origin_allowed(origin, host)
    bearer_token = _extract_mcp_token(authorization, request)
    backend_url = str(request.base_url).rstrip("/")

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    if isinstance(payload, list):
        if not payload:
            return JSONResponse(
                mcp_server.build_error_response(None, -32600, "Invalid Request"),
                status_code=400,
            )

        responses = []
        for item in payload:
            if not isinstance(item, dict):
                responses.append(mcp_server.build_error_response(None, -32600, "Invalid Request"))
                continue

            response = await _dispatch_json_rpc(
                item,
                bearer_token=bearer_token,
                backend_url=backend_url,
            )
            if response is not None:
                responses.append(response)
        if not responses:
            return Response(status_code=202)
        return JSONResponse(responses)

    if not isinstance(payload, dict):
        return JSONResponse(
            mcp_server.build_error_response(None, -32600, "Invalid Request"),
            status_code=400,
        )

    response = await _dispatch_json_rpc(payload, bearer_token=bearer_token, backend_url=backend_url)
    if response is None:
        return Response(status_code=202)
    return JSONResponse(response)
