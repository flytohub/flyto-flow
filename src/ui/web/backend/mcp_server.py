#!/usr/bin/env python3
"""
Flyto2 Workflow MCP Server

Exposes workflows with trigger_type='mcp' as MCP tools for AI agents.
Communicates with the flyto-cloud backend via HTTP API.

Usage:
    python -m mcp_server

Claude Code config (~/.claude/mcp_servers.json):
{
    "flyto-workflows": {
        "command": "python",
        "args": ["-m", "mcp_server"],
        "cwd": "/path/to/flyto-cloud/src/ui/web/backend"
    }
}
"""

import json
import os
import sys
import time as _time
from hashlib import sha256
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError

import yaml

# Backend API base URL (flyto-cloud local runner)
BACKEND_URL = os.environ.get("FLYTO_BACKEND_URL", "http://127.0.0.1:9000")
# API key for authentication (optional, for cloud mode)
API_KEY = os.environ.get("FLYTO_API_KEY", "")
ALLOW_UNAUTH_LOCAL = os.environ.get("FLYTO_MCP_ALLOW_UNAUTH_LOCAL", "").lower() in ("1", "true", "yes")
# Poll interval for refreshing workflow list (seconds)
TOOL_CACHE_TTL = int(os.environ.get("FLYTO_MCP_CACHE_TTL", "30"))
# Max execution wait time (seconds)
MAX_WAIT_SECONDS = int(os.environ.get("FLYTO_MCP_MAX_WAIT", "300"))

# MCP protocol versions we support, newest first. Server echoes the client's
# requested version when supported, otherwise returns SUPPORTED_PROTOCOL_VERSIONS[0]
# and lets the client decide whether to disconnect.
# Reference: https://modelcontextprotocol.io/specification/versioning
SUPPORTED_PROTOCOL_VERSIONS = (
    "2025-11-25",
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
)


def negotiate_protocol_version(client_version: Optional[str]) -> str:
    """Echo client's requested MCP protocol version when supported, else server preferred."""
    if client_version and client_version in SUPPORTED_PROTOCOL_VERSIONS:
        return client_version
    return SUPPORTED_PROTOCOL_VERSIONS[0]


# MCP Protocol helpers
def send_response(id: Any, result: Any):
    """Send a JSON-RPC 2.0 success response to stdout."""
    response = {"jsonrpc": "2.0", "id": id, "result": result}
    print(json.dumps(response), flush=True)

def send_error(id: Any, code: int, message: str):
    """Send a JSON-RPC 2.0 error response to stdout."""
    response = {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}
    print(json.dumps(response), flush=True)

def _log(msg: str):
    """Write a prefixed log message to stderr."""
    sys.stderr.write(f"[flyto-mcp] {msg}\n")
    sys.stderr.flush()


def _is_loopback_backend_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    return hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(".localhost")


def _assert_unauth_local_allowed(backend_url: str) -> None:
    if not _is_loopback_backend_url(backend_url):
        raise PermissionError(
            "FLYTO_MCP_ALLOW_UNAUTH_LOCAL only permits loopback backend URLs"
        )
    if not (os.environ.get("FLYTO_SIDECAR_SECRET") or os.environ.get("FLYTO_LOCAL_SECRET")):
        raise PermissionError(
            "FLYTO_MCP_ALLOW_UNAUTH_LOCAL requires FLYTO_SIDECAR_SECRET or FLYTO_LOCAL_SECRET"
        )


# =============================================================================
# Backend API Client
# =============================================================================

def _api_request(
    method: str,
    path: str,
    body: Optional[dict] = None,
    timeout: int = 30,
    bearer_token: Optional[str] = None,
    backend_url: Optional[str] = None,
) -> dict:
    """Make an HTTP request to the flyto-cloud backend."""
    auth_token = bearer_token or API_KEY
    base_url = (backend_url or BACKEND_URL).rstrip("/")
    if not auth_token:
        if not ALLOW_UNAUTH_LOCAL:
            raise PermissionError(
                "FLYTO_API_KEY is required for MCP workflow access "
                "(set FLYTO_MCP_ALLOW_UNAUTH_LOCAL=1 only for explicit local development)"
            )
        _assert_unauth_local_allowed(base_url)
    url = f"{base_url}{path}"
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except URLError as e:
        raise ConnectionError(f"Backend unavailable at {url}: {e}") from e


# =============================================================================
# Workflow → MCP Tool Conversion
# =============================================================================

_tool_cache: List[dict] = []
_tool_cache_time: float = 0
_workflow_map: Dict[str, dict] = {}  # tool_name → workflow info
_tool_cache_by_auth: Dict[str, dict] = {}


def _auth_cache_key(bearer_token: Optional[str], backend_url: Optional[str] = None) -> str:
    """Return a stable cache key without storing bearer tokens in memory."""
    if not bearer_token:
        return "__default__"
    return sha256(f"{backend_url or BACKEND_URL}|{bearer_token}".encode()).hexdigest()


def _refresh_tools(
    bearer_token: Optional[str] = None,
    *,
    force: bool = False,
    backend_url: Optional[str] = None,
) -> List[dict]:
    """Fetch workflows with trigger_type=mcp and convert to MCP tools."""
    global _tool_cache, _tool_cache_time, _workflow_map

    now = _time.monotonic()
    if bearer_token:
        cache_key = _auth_cache_key(bearer_token, backend_url)
        cached = _tool_cache_by_auth.get(cache_key)
        if not force and cached and (now - cached["time"]) < TOOL_CACHE_TTL:
            return cached["tools"]
    elif not force and _tool_cache and (now - _tool_cache_time) < TOOL_CACHE_TTL:
        return _tool_cache

    try:
        # Get all user templates from the backend
        result = _api_request(
            "GET",
            "/api/templates/?page=1&page_size=200",
            bearer_token=bearer_token,
            backend_url=backend_url,
        )
        templates = result.get("items", result.get("templates", []))
    except Exception as e:
        _log(f"Failed to fetch templates: {e}")
        if bearer_token:
            return _tool_cache_by_auth.get(_auth_cache_key(bearer_token, backend_url), {}).get("tools", [])
        return _tool_cache  # Return stale cache on error

    tools = []
    new_map = {}

    for tmpl in templates:
        # Find flow.trigger step with trigger_type=mcp
        steps = tmpl.get("steps") or tmpl.get("nodes") or []
        trigger_params = None
        for step in steps:
            module = step.get("module") or step.get("module_id", "")
            params = step.get("params", {})
            if module == "flow.trigger" and params.get("trigger_type") == "mcp":
                trigger_params = params
                break

        if not trigger_params:
            continue

        tool_name = trigger_params.get("tool_name", "")
        if not tool_name:
            continue

        # Build input schema from workflow's input fields (if defined in config)
        input_schema = _build_input_schema(tmpl, trigger_params)

        tool = {
            "name": tool_name,
            "description": trigger_params.get("tool_description", f"Run workflow: {tmpl.get('name', '')}"),
            "inputSchema": input_schema,
        }
        tools.append(tool)

        new_map[tool_name] = {
            "workflow_id": tmpl.get("id"),
            "workflow_name": tmpl.get("name"),
            "steps": steps,
            "user_id": tmpl.get("user_id"),
        }

    if bearer_token:
        _tool_cache_by_auth[_auth_cache_key(bearer_token, backend_url)] = {
            "tools": tools,
            "time": now,
            "workflow_map": new_map,
        }
    else:
        _tool_cache = tools
        _tool_cache_time = now
        _workflow_map = new_map
    _log(f"Refreshed tools: {len(tools)} MCP workflows found")
    return tools


def _build_input_schema(template: dict, trigger_params: dict) -> dict:
    """Build JSON Schema for MCP tool inputs from workflow config."""
    config = trigger_params.get("config", {})
    input_fields = config.get("input_fields", [])

    if not input_fields:
        # Default: accept arbitrary JSON input
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "object",
                    "description": "Input data for the workflow",
                },
            },
        }

    properties = {}
    required = []
    for field_def in input_fields:
        name = field_def.get("name", "")
        if not name:
            continue
        properties[name] = {
            "type": field_def.get("type", "string"),
            "description": field_def.get("description", ""),
        }
        if field_def.get("required"):
            required.append(name)

    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


# =============================================================================
# Workflow Execution
# =============================================================================

def _get_workflow_info(
    tool_name: str,
    bearer_token: Optional[str] = None,
    backend_url: Optional[str] = None,
) -> Optional[dict]:
    """Resolve a tool name to a workflow within the current auth scope."""
    if bearer_token:
        cache_key = _auth_cache_key(bearer_token, backend_url)
        wf_info = _tool_cache_by_auth.get(cache_key, {}).get("workflow_map", {}).get(tool_name)
        if wf_info:
            return wf_info
        _refresh_tools(bearer_token=bearer_token, force=True, backend_url=backend_url)
        return _tool_cache_by_auth.get(cache_key, {}).get("workflow_map", {}).get(tool_name)

    wf_info = _workflow_map.get(tool_name)
    if wf_info:
        return wf_info
    _refresh_tools()
    return _workflow_map.get(tool_name)


def _workflow_yaml_from_info(wf_info: dict) -> str:
    """Build executable workflow YAML from a cached MCP workflow template."""
    workflow = {
        "name": wf_info.get("workflow_name") or wf_info.get("workflow_id") or "MCP Workflow",
        "steps": wf_info.get("steps") or [],
        "metadata": {
            "trigger_type": "mcp",
            "workflow_id": wf_info.get("workflow_id"),
        },
    }
    return yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True)


def _execute_workflow_sync(
    tool_name: str,
    arguments: dict,
    bearer_token: Optional[str] = None,
    backend_url: Optional[str] = None,
) -> dict:
    """Execute a workflow by tool name and wait for result."""
    wf_info = _get_workflow_info(tool_name, bearer_token=bearer_token, backend_url=backend_url)
    if not wf_info:
        return {"error": f"Unknown tool: {tool_name}"}

    workflow_id = wf_info["workflow_id"]
    workflow_arguments = dict(arguments) if isinstance(arguments, dict) else {}
    mode = workflow_arguments.pop("_mode", "sync")

    # Start execution via the backend API
    try:
        result = _api_request("POST", "/api/executions/run", body={
            "workflow_yaml": _workflow_yaml_from_info(wf_info),
            "workflow_id": workflow_id,
            "variables": {
                **workflow_arguments,
                "_trigger_payload": {
                    "trigger_type": "mcp",
                    "tool_name": tool_name,
                    "arguments": workflow_arguments,
                },
            },
            "trigger_payload": {
                "trigger_type": "mcp",
                "tool_name": tool_name,
                "arguments": workflow_arguments,
            },
        }, bearer_token=bearer_token, backend_url=backend_url)
        execution_id = result.get("execution_id")
        if not execution_id:
            return {"error": "Failed to start execution", "detail": result}
    except Exception as e:
        return {"error": f"Failed to start execution: {e}"}

    if mode == "async":
        return {
            "status": "started",
            "execution_id": execution_id,
            "message": f"Workflow '{wf_info['workflow_name']}' started. Use execution_id to check status.",
        }

    # Sync mode: poll for completion
    return _wait_for_execution(
        execution_id,
        wf_info["workflow_name"],
        bearer_token=bearer_token,
        backend_url=backend_url,
    )


def _wait_for_execution(
    execution_id: str,
    workflow_name: str,
    bearer_token: Optional[str] = None,
    backend_url: Optional[str] = None,
) -> dict:
    """Poll execution status until completion or timeout."""
    start = _time.monotonic()
    poll_interval = 0.5  # Start with 500ms, increase gradually

    while (_time.monotonic() - start) < MAX_WAIT_SECONDS:
        try:
            status = _api_request(
                "GET",
                f"/api/executions/{execution_id}",
                bearer_token=bearer_token,
                backend_url=backend_url,
            )
        except Exception as e:
            _log(f"Status check failed: {e}")
            _time.sleep(poll_interval)
            continue

        execution = status.get("execution") if isinstance(status.get("execution"), dict) else status
        exec_status = str(execution.get("status", "")).lower()

        if exec_status in ("completed", "success"):
            # Extract output from the last step
            outputs = execution.get("outputs") or execution.get("result") or {}
            node_states = execution.get("node_states", {})

            # Try to extract meaningful output from node states
            if node_states and not outputs:
                for node_id in reversed(execution.get("node_order", [])):
                    node = node_states.get(node_id, {})
                    if node.get("outputs"):
                        outputs = node["outputs"]
                        break

            return {
                "status": "completed",
                "execution_id": execution_id,
                "workflow": workflow_name,
                "outputs": outputs,
            }

        if exec_status in ("failed", "error"):
            error = execution.get("error") or execution.get("message", "Execution failed")
            return {
                "status": "failed",
                "execution_id": execution_id,
                "workflow": workflow_name,
                "error": error,
            }

        if exec_status in ("cancelled",):
            return {
                "status": "cancelled",
                "execution_id": execution_id,
                "workflow": workflow_name,
            }

        # Still running
        _time.sleep(poll_interval)
        poll_interval = min(poll_interval * 1.5, 5.0)  # Backoff to max 5s

    return {
        "status": "timeout",
        "execution_id": execution_id,
        "workflow": workflow_name,
        "message": f"Execution did not complete within {MAX_WAIT_SECONDS}s. Check status via execution_id.",
    }


def _is_error_result(result: dict) -> bool:
    """Return whether a workflow result should be marked as MCP tool error."""
    status = str(result.get("status", "")).lower()
    return status in {"failed", "error"} or result.get("ok") is False or bool(result.get("error"))


def _tool_call_result(result: dict) -> dict:
    """Build an MCP tools/call result with typed content for capable clients."""
    return {
        "content": [{
            "type": "text",
            "text": json.dumps(result, ensure_ascii=False, indent=2),
        }],
        "structuredContent": result,
        "isError": _is_error_result(result),
    }


# =============================================================================
# MCP Request Handler
# =============================================================================

def build_success_response(id: Any, result: Any) -> dict:
    """Build a JSON-RPC 2.0 success response."""
    return {"jsonrpc": "2.0", "id": id, "result": result}


def build_error_response(id: Any, code: int, message: str) -> dict:
    """Build a JSON-RPC 2.0 error response."""
    return {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}


def _maybe_response(id: Any, result: Any) -> Optional[dict]:
    """Return no body for JSON-RPC notifications."""
    if id is None:
        return None
    return build_success_response(id, result)


def handle_json_rpc_request(
    request: dict,
    bearer_token: Optional[str] = None,
    backend_url: Optional[str] = None,
) -> Optional[dict]:
    """Handle an MCP JSON-RPC 2.0 request and return the response payload."""
    if "method" not in request:
        if "result" in request or "error" in request:
            return None
        return build_error_response(request.get("id"), -32600, "Invalid Request")

    if request.get("jsonrpc") not in (None, "2.0"):
        return build_error_response(request.get("id"), -32600, "Invalid Request")

    method = request.get("method", "")
    id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        client_version = params.get("protocolVersion") if isinstance(params, dict) else None
        server_version = negotiate_protocol_version(client_version)

        return _maybe_response(id, {
            "protocolVersion": server_version,
            "capabilities": {
                "tools": {"listChanged": True},
            },
            "serverInfo": {
                "name": "flyto-workflows",
                "title": "Flyto2 Workflow Tools",
                "version": "1.0.0",
                "description": "Execute flyto workflows as MCP tools. Workflows with trigger_type='mcp' are exposed as callable tools.",
            },
            "instructions": (
                "This server exposes flyto workflows as tools. "
                "Each tool runs a pre-configured workflow and returns its output. "
                "Tools are defined by workflow creators who set trigger_type='mcp' in their workflow trigger."
            ),
        })

    elif method == "tools/list":
        try:
            tools = _refresh_tools(bearer_token=bearer_token, backend_url=backend_url)
            return _maybe_response(id, {"tools": tools})
        except Exception as e:
            _log(f"tools/list error: {e}")
            return _maybe_response(id, {"tools": []})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            result = _execute_workflow_sync(
                tool_name,
                arguments,
                bearer_token=bearer_token,
                backend_url=backend_url,
            )
            return _maybe_response(id, _tool_call_result(result))
        except Exception as e:
            _log(f"tools/call error: {e}")
            return build_error_response(id, -32000, str(e))

    elif method == "notifications/initialized":
        return None  # No response needed

    elif method == "notifications/cancelled":
        return None  # No response needed

    elif method == "ping":
        return _maybe_response(id, {})

    elif method == "logging/setLevel":
        return _maybe_response(id, {})

    else:
        if id is not None:
            return build_error_response(id, -32601, f"Method not found: {method}")
        return None


def handle_request(request: dict):
    """Handle MCP JSON-RPC 2.0 request and write any response to stdout."""
    response = handle_json_rpc_request(request)
    if response is None:
        return
    if "error" in response:
        error = response["error"]
        send_error(response.get("id"), error.get("code", -32000), error.get("message", "Error"))
    else:
        send_response(response.get("id"), response.get("result"))


def main():
    """MCP Server main loop — reads JSON-RPC from stdin."""
    _log(f"Starting MCP server (pid={os.getpid()}, backend={BACKEND_URL})")

    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            handle_request(request)
        except json.JSONDecodeError as e:
            _log(f"JSON decode error: {e}")
        except Exception as e:
            _log(f"Error: {e}")
            print(json.dumps({
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
            }), flush=True)


if __name__ == "__main__":
    main()
