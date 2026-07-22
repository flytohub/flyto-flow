"""Local SQLite workflow-template CRUD for CE."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from gateway.local_context import LOCAL_WORKSPACE
from gateway.providers.hub import get_data_provider


router = APIRouter(prefix="/templates", tags=["Templates"])


class TemplateCreateRequest(BaseModel):
    name: str
    description: str = ""
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    ui: dict[str, Any] | None = None
    params_schema: dict[str, Any] = Field(default_factory=dict)
    color: str | None = None
    checkpoints: list[str] = Field(default_factory=list)
    error_workflow_id: str | None = None
    error_handling: dict[str, Any] | None = None


class TemplateUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    steps: list[dict[str, Any]] | None = None
    ui: dict[str, Any] | None = None
    params_schema: dict[str, Any] | None = None
    color: str | None = None
    checkpoints: list[str] | None = None
    error_workflow_id: str | None = None
    error_handling: dict[str, Any] | None = None


def _as_dict(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return vars(value)


@router.get("/")
async def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
):
    result = await get_data_provider().templates.list_workspace_templates(
        workspace_id=LOCAL_WORKSPACE.id,
        page=page,
        page_size=page_size,
    )
    items = [_as_dict(item) for item in (result.items or [])]
    return {
        "ok": True,
        "items": items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "has_next": result.has_next,
    }


@router.get("/{template_id}")
async def get_template(template_id: str):
    template = await get_data_provider().templates.get_template(
        template_id,
        workspace_id=LOCAL_WORKSPACE.id,
    )
    if not template:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"ok": True, "template": _as_dict(template)}


@router.post("/")
async def create_template(data: TemplateCreateRequest):
    from gateway.providers.data.models import TemplateCreateDTO

    template = await get_data_provider().templates.create_template(
        workspace_id=LOCAL_WORKSPACE.id,
        data=TemplateCreateDTO(
            name=data.name,
            description=data.description,
            category=data.category,
            tags=data.tags,
            steps=data.steps,
            ui=data.ui,
            params_schema=data.params_schema,
            checkpoints=data.checkpoints,
            error_workflow_id=data.error_workflow_id,
            error_handling=data.error_handling,
        ),
    )
    if data.color:
        from gateway.providers.data.models import TemplateUpdateDTO

        template = await get_data_provider().templates.update_template(
            workspace_id=LOCAL_WORKSPACE.id,
            template_id=template.id,
            data=TemplateUpdateDTO(color=data.color),
        )
    return {"ok": True, "template": _as_dict(template)}


@router.put("/{template_id}")
async def update_template(template_id: str, data: TemplateUpdateRequest):
    from gateway.providers.data.models import TemplateUpdateDTO

    fields = {key: value for key, value in data.model_dump().items() if value is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    template = await get_data_provider().templates.update_template(
        workspace_id=LOCAL_WORKSPACE.id,
        template_id=template_id,
        data=TemplateUpdateDTO(**fields),
    )
    if not template:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"ok": True, "template": _as_dict(template)}


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    deleted = await get_data_provider().templates.delete_template(
        workspace_id=LOCAL_WORKSPACE.id,
        template_id=template_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"ok": True}
