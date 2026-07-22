"""Local workflow-template data transfer objects used by CE."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TemplateDTO(BaseModel):
    """A workflow definition stored in the single local CE workspace."""

    id: str
    name: str
    description: str | None = None
    version: str = "1"
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    color: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    ui: dict[str, Any] | None = None
    workflow_data: dict[str, Any] = Field(default_factory=dict)
    params_schema: dict[str, Any] = Field(default_factory=dict)
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    checkpoints: list[str] = Field(default_factory=list)
    error_workflow_id: str | None = None
    error_handling: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class TemplateCreateDTO(BaseModel):
    """Fields accepted when a local workflow definition is created."""

    name: str
    description: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    color: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    ui: dict[str, Any] | None = None
    workflow_data: dict[str, Any] | None = None
    params_schema: dict[str, Any] = Field(default_factory=dict)
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    checkpoints: list[str] = Field(default_factory=list)
    error_workflow_id: str | None = None
    error_handling: dict[str, Any] | None = None


class TemplateUpdateDTO(BaseModel):
    """Fields accepted when a local workflow definition is updated."""

    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    color: str | None = None
    steps: list[dict[str, Any]] | None = None
    ui: dict[str, Any] | None = None
    workflow_data: dict[str, Any] | None = None
    params_schema: dict[str, Any] | None = None
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    checkpoints: list[str] | None = None
    error_workflow_id: str | None = None
    error_handling: dict[str, Any] | None = None
