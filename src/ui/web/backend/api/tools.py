"""
Tools API

Provides /tools endpoints for backwards compatibility.
Delegates to user_tools for actual implementation.
Also provides utility tools like curl parsing.
"""

import logging
import re
import secrets
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlparse, parse_qs

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.auth import get_current_user, get_optional_user
from gateway.providers.hub import get_provider_hub

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["Tools"])


class CreateToolRequest(BaseModel):
    """Request to create a tool"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    code: str = ""
    language: str = "javascript"
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False
    meta: Optional[Dict[str, Any]] = None


class UpdateToolRequest(BaseModel):
    """Request to update a tool"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    code: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None
    is_public: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None


class ExecuteToolRequest(BaseModel):
    """Request to execute a tool"""
    inputs: Dict[str, Any] = Field(default_factory=dict)


class DuplicateToolRequest(BaseModel):
    """Request to duplicate a tool"""
    name: Optional[str] = None


# Tool categories (same as frontend defaults)
TOOL_CATEGORIES = [
    {"id": "image", "name": "Image Processing", "icon": "Image"},
    {"id": "text", "name": "Text Processing", "icon": "FileText"},
    {"id": "data", "name": "Data Transform", "icon": "Database"},
    {"id": "file", "name": "File Operations", "icon": "Folder"},
    {"id": "web", "name": "Web Scraping", "icon": "Globe"},
    {"id": "api", "name": "API Integration", "icon": "Zap"},
    {"id": "automation", "name": "Automation", "icon": "Bot"},
    {"id": "other", "name": "Other", "icon": "Box"},
]


@router.get("/")
async def list_tools(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: Optional[dict] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """List tools (user's tools if authenticated, public tools otherwise)."""
    hub = get_provider_hub()

    try:
        if user:
            result = await hub.data.user_tools.list_user_tools(
                user_id=user["id"],
                page=page,
                page_size=page_size,
            )
        else:
            result = await hub.data.user_tools.list_public_tools(
                page=page,
                page_size=page_size,
            )

        return {
            "ok": True,
            "tools": [t.model_dump() for t in result.items],
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
        }
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        return {
            "ok": True,
            "tools": [],
            "total": 0,
        }


@router.get("/categories")
async def get_tool_categories() -> Dict[str, Any]:
    """Get tool categories."""
    return {
        "ok": True,
        "categories": TOOL_CATEGORIES,
    }


@router.get("/public")
async def list_public_tools(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Dict[str, Any]:
    """List all public tools."""
    hub = get_provider_hub()

    try:
        result = await hub.data.user_tools.list_public_tools(
            page=page,
            page_size=page_size,
        )

        return {
            "ok": True,
            "tools": [t.model_dump() for t in result.items],
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
        }
    except Exception as e:
        logger.error(f"Failed to list public tools: {e}")
        return {
            "ok": True,
            "tools": [],
            "total": 0,
        }


@router.get("/search")
async def search_tools(
    q: str = Query(..., min_length=1),
    category: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Dict[str, Any]:
    """Search public tools."""
    hub = get_provider_hub()

    try:
        result = await hub.data.user_tools.list_public_tools(
            page=page,
            page_size=page_size,
        )

        tools = [t.model_dump() for t in result.items]

        # Apply search filter
        q_lower = q.lower()
        filtered = [
            t for t in tools
            if q_lower in (t.get("name", "") or "").lower()
            or q_lower in (t.get("description", "") or "").lower()
        ]

        # Apply category filter
        if category:
            filtered = [t for t in filtered if t.get("category") == category]

        return {
            "ok": True,
            "tools": filtered,
            "total": len(filtered),
        }
    except Exception as e:
        logger.error(f"Failed to search tools: {e}")
        return {
            "ok": True,
            "tools": [],
            "total": 0,
        }


@router.post("/")
async def create_tool(
    request: CreateToolRequest,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a new tool."""
    hub = get_provider_hub()

    try:
        from gateway.providers.data.models import UserToolCreateDTO

        tool = await hub.data.user_tools.create_tool(
            user_id=user["id"],
            data=UserToolCreateDTO(
                name=request.name,
                description=request.description,
                icon=request.icon,
                code=request.code,
                language=request.language,
                input_schema=request.input_schema,
                output_schema=request.output_schema,
                is_public=request.is_public,
            ),
        )

        return {"ok": True, "tool": tool.model_dump()}
    except Exception as e:
        logger.error(f"Failed to create tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tool_id}")
async def get_tool(
    tool_id: str,
    user: Optional[dict] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """Get tool by ID."""
    hub = get_provider_hub()

    try:
        if user:
            tool = await hub.data.user_tools.get_tool(
                user_id=user["id"],
                tool_id=tool_id,
            )
        else:
            # Try to get public tool
            tool = await hub.data.user_tools.get_public_tool(tool_id)

        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")

        return {"ok": True, "tool": tool.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool: {e}")
        raise HTTPException(status_code=404, detail="Tool not found")


@router.put("/{tool_id}")
async def update_tool(
    tool_id: str,
    request: UpdateToolRequest,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update a tool."""
    hub = get_provider_hub()

    try:
        from gateway.providers.data.models import UserToolUpdateDTO

        tool = await hub.data.user_tools.update_tool(
            user_id=user["id"],
            tool_id=tool_id,
            data=UserToolUpdateDTO(
                name=request.name,
                description=request.description,
                icon=request.icon,
                code=request.code,
                input_schema=request.input_schema,
                output_schema=request.output_schema,
                is_enabled=request.is_enabled,
                is_public=request.is_public,
            ),
        )

        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")

        return {"ok": True, "tool": tool.model_dump()}
    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: str,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Delete a tool."""
    hub = get_provider_hub()

    try:
        success = await hub.data.user_tools.delete_tool(
            user_id=user["id"],
            tool_id=tool_id,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Tool not found")

        return {"ok": True}
    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tool_id}/execute")
async def execute_tool(
    tool_id: str,
    request: ExecuteToolRequest,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Execute a tool."""
    hub = get_provider_hub()

    try:
        result = await hub.data.user_tools.execute_tool(
            user_id=user["id"],
            tool_id=tool_id,
            params=request.inputs,
        )

        return {"ok": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tool_id}/duplicate")
async def duplicate_tool(
    tool_id: str,
    request: DuplicateToolRequest,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Duplicate a tool."""
    hub = get_provider_hub()

    try:
        # Get original tool
        original = await hub.data.user_tools.get_tool(
            user_id=user["id"],
            tool_id=tool_id,
        )

        if not original:
            raise HTTPException(status_code=404, detail="Tool not found")

        from gateway.providers.data.models import UserToolCreateDTO

        # Create duplicate
        new_name = request.name or f"{original.name} (Copy)"
        tool = await hub.data.user_tools.create_tool(
            user_id=user["id"],
            data=UserToolCreateDTO(
                name=new_name,
                description=original.description,
                icon=original.icon,
                code=original.code,
                language=original.language,
                input_schema=original.input_schema,
                output_schema=original.output_schema,
                is_public=False,  # Duplicates are private by default
            ),
        )

        return {"ok": True, "tool": tool.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to duplicate tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Curl Parser Utility
# =============================================================================

class ParseCurlRequest(BaseModel):
    """Request to parse a curl command"""
    curl_command: str = Field(..., min_length=4, description="The curl command to parse")


class ParseCurlResponse(BaseModel):
    """Response from curl parsing"""
    ok: bool
    method: str = "GET"
    url: str = ""
    headers: Dict[str, str] = Field(default_factory=dict)
    query: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Union[Dict[str, Any], str]] = None
    content_type: Optional[str] = None
    auth: Optional[Dict[str, str]] = None
    compressed: bool = False
    insecure: bool = False
    follow_redirects: bool = False
    error: Optional[str] = None


def _extract_curl_url(normalized: str) -> tuple:
    """Extract URL and query params from a normalized curl command. Returns (url, query_dict)."""
    url = ""
    query = {}
    for pattern in [
        r'curl\s+[\'"]?(https?://[^\s\'"]+)[\'"]?',
        r'[\'"]?(https?://[^\s\'"]+)[\'"]?',
    ]:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match and match.group(1):
            url = match.group(1)
            break

    if url:
        try:
            parsed = urlparse(url)
            if parsed.query:
                query = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}
            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        except Exception:
            pass
    return url, query


def _extract_curl_headers(normalized: str) -> tuple:
    """Extract headers and content_type from a normalized curl command."""
    headers = {}
    content_type = None
    header_regex = re.compile(r'(?:-H|--header)\s+[\'"]([^\'"]+)[\'"]', re.IGNORECASE)
    for match in header_regex.finditer(normalized):
        header_str = match.group(1)
        colon_index = header_str.find(':')
        if colon_index > 0:
            key = header_str[:colon_index].strip()
            value = header_str[colon_index + 1:].strip()
            headers[key] = value
            if key.lower() == 'content-type':
                content_type = value.split(';')[0].strip()
    return headers, content_type


def _extract_curl_body(normalized: str, content_type: str) -> tuple:
    """Extract body and inferred content_type from a normalized curl command."""
    import json

    body_patterns = [
        r"(?:-d|--data|--data-raw|--data-binary)\s+'([^']+)'",
        r'(?:-d|--data|--data-raw|--data-binary)\s+"([^"]+)"',
        r'(?:-d|--data|--data-raw|--data-binary)\s+(\S+)',
    ]
    for pattern in body_patterns:
        match = re.search(pattern, normalized)
        if match and match.group(1):
            body_str = match.group(1)
            try:
                body = json.loads(body_str)
                return body, content_type or "application/json"
            except json.JSONDecodeError:
                if '=' in body_str and '{' not in body_str:
                    return body_str, content_type or "application/x-www-form-urlencoded"
                return body_str, content_type
            break

    # Check form data (-F or --form)
    form_regex = re.compile(r"(?:-F|--form)\s+['\"]?([^'\"\s]+(?:=[^'\"\s]+)?)['\"]?", re.IGNORECASE)
    form_data = {}
    for match in form_regex.finditer(normalized):
        form_str = match.group(1)
        eq_index = form_str.find('=')
        if eq_index > 0:
            form_data[form_str[:eq_index]] = form_str[eq_index + 1:]
    if form_data:
        return form_data, "multipart/form-data"

    return None, content_type


def _parse_curl_command(curl_command: str) -> Dict[str, Any]:
    """Parse a curl command string into HTTP request parameters."""
    result = {
        "method": "GET", "url": "", "headers": {}, "query": {},
        "body": None, "content_type": None, "auth": None,
        "compressed": False, "insecure": False, "follow_redirects": False,
    }

    if not curl_command or not isinstance(curl_command, str):
        return result

    normalized = re.sub(r'\\\r?\n', ' ', curl_command)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    if not normalized.lower().startswith('curl'):
        return result

    # Method
    method_match = re.search(r'-X\s+[\'"]?(\w+)[\'"]?|--request\s+[\'"]?(\w+)[\'"]?', normalized, re.IGNORECASE)
    if method_match:
        result["method"] = (method_match.group(1) or method_match.group(2)).upper()

    result["url"], result["query"] = _extract_curl_url(normalized)
    result["headers"], result["content_type"] = _extract_curl_headers(normalized)
    result["body"], result["content_type"] = _extract_curl_body(normalized, result["content_type"])

    # Basic auth
    auth_match = re.search(r"(?:-u|--user)\s+['\"]?([^:'\"\s]+):([^'\"\s]+)['\"]?", normalized, re.IGNORECASE)
    if auth_match:
        result["auth"] = {"type": "basic", "username": auth_match.group(1), "password": auth_match.group(2)}

    if result["body"] and result["method"] == "GET":
        result["method"] = "POST"

    result["compressed"] = "--compressed" in normalized
    result["insecure"] = "-k" in normalized or "--insecure" in normalized
    result["follow_redirects"] = "-L" in normalized or "--location" in normalized

    return result


@router.post("/parse-curl")
async def parse_curl(
    request: ParseCurlRequest,
) -> ParseCurlResponse:
    """
    Parse a curl command into structured HTTP request parameters.

    This endpoint processes curl commands on the backend to ensure:
    - Consistent parsing across all clients
    - Secure handling of credentials (not exposed in frontend code)
    - Single source of truth for curl parsing logic

    The endpoint does not require authentication as it's a stateless
    utility that doesn't access any user data or modify system state.
    """
    try:
        parsed = _parse_curl_command(request.curl_command)

        return ParseCurlResponse(
            ok=True,
            method=parsed["method"],
            url=parsed["url"],
            headers=parsed["headers"],
            query=parsed["query"],
            body=parsed["body"],
            content_type=parsed["content_type"],
            auth=parsed["auth"],
            compressed=parsed["compressed"],
            insecure=parsed["insecure"],
            follow_redirects=parsed["follow_redirects"],
        )
    except Exception as e:
        logger.error(f"Failed to parse curl command: {e}")
        return ParseCurlResponse(
            ok=False,
            error=str(e),
        )
