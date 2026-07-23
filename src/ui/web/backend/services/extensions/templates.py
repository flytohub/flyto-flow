"""Strict semantic loading for verified workflow template packs."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from services.extensions.manifest import ExtensionKind, VerifiedExtension


STEP_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
MODULE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)+$")
TEMPLATE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)+$")


class PackedTemplateStep(BaseModel):
    id: str
    module: str
    label: str = Field(min_length=1, max_length=160)
    params: dict[str, Any] = Field(default_factory=dict)
    position_x: float = 0
    position_y: float = 0
    order_index: int = Field(ge=0)

    model_config = ConfigDict(frozen=True, extra="forbid")

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not STEP_ID_PATTERN.fullmatch(value):
            raise ValueError("Template step ID must be a lowercase slug")
        return value

    @field_validator("module")
    @classmethod
    def validate_module(cls, value: str) -> str:
        if not MODULE_ID_PATTERN.fullmatch(value):
            raise ValueError("Template module must be a namespaced lowercase identifier")
        return value


class PackedTemplate(BaseModel):
    id: str
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=80)
    tags: tuple[str, ...] = ()
    color: str | None = Field(default=None, max_length=32)
    steps: tuple[PackedTemplateStep, ...] = Field(min_length=1, max_length=500)
    ui: dict[str, Any] | None = None
    workflow_data: dict[str, Any] | None = None
    params_schema: dict[str, Any] = Field(default_factory=dict)
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    checkpoints: tuple[str, ...] = ()
    error_workflow_id: str | None = Field(default=None, max_length=128)
    error_handling: dict[str, Any] | None = None

    model_config = ConfigDict(frozen=True, extra="forbid")

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not TEMPLATE_ID_PATTERN.fullmatch(value):
            raise ValueError("Template ID must be a namespaced lowercase identifier")
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) > 32 or any(
            not value.strip() or len(value) > 64 for value in values
        ):
            raise ValueError("Template tags are invalid")
        if len(values) != len(set(values)):
            raise ValueError("Template tags must be unique")
        return values

    @model_validator(mode="after")
    def validate_steps(self):
        step_ids = [step.id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Template step IDs must be unique")
        order_indexes = [step.order_index for step in self.steps]
        if len(order_indexes) != len(set(order_indexes)):
            raise ValueError("Template step order indexes must be unique")
        if sorted(order_indexes) != list(range(len(order_indexes))):
            raise ValueError("Template step order indexes must be contiguous")
        return self

    def create_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="python", exclude={"id"})


class TemplatePack(BaseModel):
    schema_name: str = Field(alias="schema", pattern=r"^flyto\.template-pack\.v1$")
    templates: tuple[PackedTemplate, ...] = Field(min_length=1, max_length=500)

    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    @model_validator(mode="after")
    def validate_template_ids(self):
        identifiers = [template.id for template in self.templates]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Template IDs must be unique within a pack")
        return self


def load_template_pack(path: Path) -> TemplatePack:
    try:
        raw_pack = json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Template pack contains invalid JSON: {path.name}") from exc
    return TemplatePack.model_validate(raw_pack)


def load_template_packs(
    extensions: Iterable[VerifiedExtension],
) -> list[PackedTemplate]:
    templates: list[PackedTemplate] = []
    identifiers: set[str] = set()
    for extension in extensions:
        if extension.manifest.kind != ExtensionKind.TEMPLATE_PACK:
            continue
        artifact = extension.manifest.artifacts[0]
        pack = load_template_pack(extension.root / artifact.path)
        for template in pack.templates:
            if template.id in identifiers:
                raise ValueError(f"Duplicate template ID across packs: {template.id}")
            identifiers.add(template.id)
            templates.append(template)
    return templates
