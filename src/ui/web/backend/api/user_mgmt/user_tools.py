"""
User Tools API

Endpoints for user custom tools/plugins.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any

from api.auth import get_current_user
from gateway.providers.hub import get_provider_hub

router = APIRouter(prefix="/user-tools", tags=["User Tools"])


class CreateToolRequest(BaseModel):
    """Request body for creating a custom user tool."""
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    code: str
    language: str = "javascript"
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    is_public: bool = False


class UpdateToolRequest(BaseModel):
    """Request body for updating a custom user tool."""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    code: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None
    is_public: Optional[bool] = None


class ExecuteToolRequest(BaseModel):
    """Request body for executing a custom user tool."""
    params: Dict[str, Any] = {}


@router.get("/")
async def list_my_tools(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """List my custom tools."""
    hub = get_provider_hub()

    result = await hub.data.user_tools.list_user_tools(
        user_id=user["id"],
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


@router.get("/public")
async def list_public_tools(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """List public tools."""
    hub = get_provider_hub()

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


@router.get("/{tool_id}")
async def get_tool(
    tool_id: str,
    user: dict = Depends(get_current_user),
):
    """Get single tool."""
    hub = get_provider_hub()

    tool = await hub.data.user_tools.get_tool(
        user_id=user["id"],
        tool_id=tool_id,
    )

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return {"ok": True, "tool": tool.model_dump()}


@router.post("/")
async def create_tool(
    request: CreateToolRequest,
    user: dict = Depends(get_current_user),
):
    """Create a custom tool."""
    hub = get_provider_hub()

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


@router.put("/{tool_id}")
async def update_tool(
    tool_id: str,
    request: UpdateToolRequest,
    user: dict = Depends(get_current_user),
):
    """Update a custom tool."""
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
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a custom tool."""
    hub = get_provider_hub()

    try:
        success = await hub.data.user_tools.delete_tool(
            user_id=user["id"],
            tool_id=tool_id,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Tool not found")

        return {"ok": True}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{tool_id}/execute")
async def execute_tool(
    tool_id: str,
    request: ExecuteToolRequest,
    user: dict = Depends(get_current_user),
):
    """Execute a tool."""
    hub = get_provider_hub()

    try:
        result = await hub.data.user_tools.execute_tool(
            user_id=user["id"],
            tool_id=tool_id,
            params=request.params,
        )

        return {"ok": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
