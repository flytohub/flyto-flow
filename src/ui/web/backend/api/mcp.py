"""Accountless local MCP transport for Flyto2 Flow workflows."""

from __future__ import annotations

import asyncio
import hmac
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
    family = media_type.split("/", 1)[0]
    return "*/*" in ranges or media_type in ranges or f"{family}/*" in ranges


def _explicitly_accepts(accept: Optional[str], media_type: str) -> bool:
    ranges = _media_ranges(accept)
    family = media_type.split("/", 1)[0]
    return media_type in ranges or f"{family}/*" in ranges


def _configured_token() -> str:
    return os.environ.get("FLYTO_FLOW_MCP_TOKEN", "").strip()


def _allowed_origins() -> set[str]:
    raw = os.environ.get("FLYTO_MCP_ALLOWED_ORIGINS", "")
    return {origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()}


def _assert_origin_allowed(origin: Optional[str], host: Optional[str]) -> None:
    """Reject cross-origin browser calls unless the operator explicitly allows them."""
    if not origin:
        return
    normalized = origin.rstrip("/")
    if normalized in _allowed_origins():
        return
    if host and urlparse(normalized).netloc == host:
        return
    raise HTTPException(status_code=403, detail="Origin is not allowed for MCP access")


def _is_loopback_host(value: Optional[str]) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    if normalized in {"localhost", "testclient"} or normalized.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _request_is_loopback(request: Request, host: Optional[str]) -> bool:
    client_host = request.client.host if request.client else None
    host_name = urlparse(f"//{host}").hostname if host else None
    return _is_loopback_host(client_host) and _is_loopback_host(host_name)


def _assert_mcp_access(
    request: Request,
    authorization: Optional[str],
    host: Optional[str],
) -> None:
    """Keep the default endpoint loopback-only; a token is an operator guard, not an account."""
    if _request_is_loopback(request, host):
        return

    expected = _configured_token()
    if not expected:
        raise HTTPException(
            status_code=403,
            detail="MCP HTTP is loopback-only unless FLYTO_FLOW_MCP_TOKEN is configured",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Operator bearer token required for non-loopback MCP access",
            headers={"WWW-Authenticate": "Bearer"},
        )
    supplied = authorization.split("Bearer ", 1)[1].strip()
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=403, detail="Invalid operator bearer token")


def _assert_post_accept_supported(accept: Optional[str]) -> None:
    if _accepts(accept, "application/json") and _accepts(accept, "text/event-stream"):
        return
    raise HTTPException(
        status_code=406,
        detail="MCP HTTP clients must accept application/json and text/event-stream",
    )


async def _dispatch_json_rpc(payload: dict) -> Optional[dict]:
    return await asyncio.to_thread(
        mcp_server.handle_json_rpc_request,
        payload,
        None,
        mcp_server.BACKEND_URL,
    )


def _metadata_server_url(request: Request) -> str:
    try:
        return str(request.url_for("get_mcp_metadata")).rstrip("/")
    except Exception:
        return f"{str(request.base_url).rstrip('/')}/api/mcp"


def _mcp_setup_payload(server_url: str) -> dict[str, Any]:
    common_env = {"FLYTO_BACKEND_URL": mcp_server.BACKEND_URL}
    http: dict[str, Any] = {"url": server_url}
    if _configured_token():
        http["headers"] = {"Authorization": "Bearer <operator-token>"}
    return {
        "serverName": "flyto2-flow",
        "backendUrl": mcp_server.BACKEND_URL,
        "http": http,
        "claudeCode": {
            "mcpServers": {
                "flyto2-flow": {
                    "command": "python",
                    "args": ["-m", "mcp_server"],
                    "cwd": "<flyto-flow>/src/ui/web/backend",
                    "env": common_env,
                }
            }
        },
        "codexToml": (
            "[mcp_servers.flyto2-flow]\n"
            'command = "python"\n'
            'args = ["-m", "mcp_server"]\n'
            'cwd = "<flyto-flow>/src/ui/web/backend"\n\n'
            "[mcp_servers.flyto2-flow.env]\n"
            f'FLYTO_BACKEND_URL = "{mcp_server.BACKEND_URL}"\n'
        ),
    }


async def _list_visible_tools() -> tuple[list[dict[str, Any]], Optional[str]]:
    try:
        tools = await asyncio.to_thread(
            mcp_server._refresh_tools,
            None,
            force=True,
            backend_url=mcp_server.BACKEND_URL,
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
    return {
        "name": "flyto2-flow",
        "title": "Flyto2 Flow MCP Tools",
        "transport": "streamable-http",
        "endpoint": "/api/mcp",
        "serverUrl": _metadata_server_url(request),
        "protocolVersions": list(mcp_server.SUPPORTED_PROTOCOL_VERSIONS),
        "capabilities": {"tools": {"listChanged": True}},
        "access": {"loopback": "accountless", "nonLoopback": "operator-token"},
    }


@router.get("/status")
async def get_mcp_status(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    host: Optional[str] = Header(default=None),
):
    """Return local MCP setup metadata and tools without a user identity."""
    _assert_mcp_access(request, authorization, host)
    tools, tools_error = await _list_visible_tools()
    server_url = _metadata_server_url(request)
    return {
        "ok": tools_error is None,
        "name": "flyto2-flow",
        "title": "Flyto2 Flow MCP Tools",
        "transport": "streamable-http",
        "endpoint": "/api/mcp",
        "serverUrl": server_url,
        "protocolVersions": list(mcp_server.SUPPORTED_PROTOCOL_VERSIONS),
        "capabilities": {"tools": {"listChanged": True}},
        "auth": {
            "type": "operator-token",
            "required": False,
            "requiredForNonLoopback": True,
            "configured": bool(_configured_token()),
            "localLoopbackAccountless": True,
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
    """Handle MCP JSON-RPC over local Streamable HTTP."""
    _assert_post_accept_supported(accept)
    _assert_origin_allowed(origin, host)
    _assert_mcp_access(request, authorization, host)

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
            response = await _dispatch_json_rpc(item)
            if response is not None:
                responses.append(response)
        return JSONResponse(responses) if responses else Response(status_code=202)

    if not isinstance(payload, dict):
        return JSONResponse(
            mcp_server.build_error_response(None, -32600, "Invalid Request"),
            status_code=400,
        )
    response = await _dispatch_json_rpc(payload)
    return JSONResponse(response) if response is not None else Response(status_code=202)
