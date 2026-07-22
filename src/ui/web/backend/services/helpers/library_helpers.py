"""Resolve IDs for workflow definitions stored in the local CE workspace."""

from typing import Literal


SourceType = Literal["local"]


def resolve_library_id(template: dict) -> tuple[str | None, SourceType]:
    if not isinstance(template, dict):
        return None, "local"
    return template.get("template_id") or template.get("id"), "local"


def get_library_id(template: dict) -> str | None:
    return resolve_library_id(template)[0]
