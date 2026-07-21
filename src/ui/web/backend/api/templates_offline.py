"""
Offline Templates API — lightweight CRUD without Firebase dependencies.

Replaces the full api/templates/ package in offline mode.
No marketplace, no collaboration, no library — just local template management.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from gateway.auth import get_current_user
from gateway.providers.base import UserInfo
from gateway.providers.hub import get_data_provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/templates", tags=["Templates"])


# --- Request/Response Models ---

class TemplateCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    category: Optional[str] = "general"
    tags: Optional[List[str]] = []
    steps: Optional[list] = []
    graph: Optional[dict] = {}
    params_schema: Optional[dict] = {}
    icon: Optional[str] = ""
    color: Optional[str] = ""
    is_public: Optional[bool] = False


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    steps: Optional[list] = None
    graph: Optional[dict] = None
    params_schema: Optional[dict] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_public: Optional[bool] = None


# --- Routes ---

@router.get("/")
async def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    user: UserInfo = Depends(get_current_user),
):
    """List current user's templates."""
    provider = get_data_provider()
    result = await provider.templates.list_user_templates(
        user_id=user.id, page=page, page_size=page_size,
    )
    return {"ok": True, **_paginated_to_dict(result)}


@router.get("/public")
async def list_public_templates(
    category: Optional[str] = None,
    tags: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List public templates (offline marketplace alternative)."""
    provider = get_data_provider()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    result = await provider.templates.list_public_templates(
        category=category, tags=tag_list, page=page, page_size=page_size,
    )
    return {"ok": True, **_paginated_to_dict(result)}


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    user: UserInfo = Depends(get_current_user),
):
    """Get a template by ID."""
    provider = get_data_provider()
    template = await provider.templates.get_template(template_id, user_id=user.id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"ok": True, "template": _dto_to_dict(template)}


@router.post("/")
async def create_template(
    data: TemplateCreateRequest,
    user: UserInfo = Depends(get_current_user),
):
    """Create a new template."""
    from gateway.providers.data.models import TemplateCreateDTO
    provider = get_data_provider()
    dto = TemplateCreateDTO(
        name=data.name,
        description=data.description or "",
        category=data.category or "general",
        tags=data.tags or [],
        steps=data.steps or [],
        graph=data.graph or {},
        params_schema=data.params_schema or {},
    )
    template = await provider.templates.create_template(user_id=user.id, data=dto)
    return {"ok": True, "template": _dto_to_dict(template)}


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    data: TemplateUpdateRequest,
    user: UserInfo = Depends(get_current_user),
):
    """Update a template."""
    from gateway.providers.data.models import TemplateUpdateDTO
    provider = get_data_provider()
    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    dto = TemplateUpdateDTO(**update_fields)
    template = await provider.templates.update_template(
        user_id=user.id, template_id=template_id, data=dto,
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"ok": True, "template": _dto_to_dict(template)}


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    user: UserInfo = Depends(get_current_user),
):
    """Delete a template."""
    provider = get_data_provider()
    deleted = await provider.templates.delete_template(user_id=user.id, template_id=template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"ok": True}


# --- Helpers ---

def _dto_to_dict(obj):
    """Convert DTO to dict, handling both Pydantic models and plain dicts."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    return vars(obj)


def _paginated_to_dict(result):
    """Convert paginated result to dict."""
    if hasattr(result, "model_dump"):
        d = result.model_dump()
        if "items" in d:
            d["items"] = [_dto_to_dict(i) for i in (result.items or [])]
        return d
    if isinstance(result, dict):
        return result
    return {"items": [], "total": 0, "page": 1, "page_size": 20}
