"""Fail-closed loading helpers for edition-owned provider packages."""

from __future__ import annotations

import importlib
import os
import re
from collections.abc import Callable
from typing import Any


MODULE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")


def configured_provider_prefixes() -> tuple[str, ...]:
    configured = os.environ.get(
        "FLYTO_PROVIDER_MODULE_ALLOWLIST",
        "flyto2_enterprise_extensions",
    )
    prefixes = tuple(
        prefix.strip() for prefix in configured.split(",") if prefix.strip()
    )
    if not prefixes or any(not MODULE_PATTERN.fullmatch(prefix) for prefix in prefixes):
        raise ValueError(
            "FLYTO_PROVIDER_MODULE_ALLOWLIST must contain Python package names"
        )
    return prefixes


def is_provider_module_allowed(
    module_name: str,
    prefixes: tuple[str, ...] | None = None,
) -> bool:
    if not MODULE_PATTERN.fullmatch(module_name):
        return False
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for prefix in (prefixes or configured_provider_prefixes())
    )


def load_provider_factory(
    spec: str,
    *,
    setting_name: str,
) -> Callable[[], Any]:
    if spec.count(":") != 1:
        raise ValueError(f"{setting_name} must use module:factory syntax")
    module_name, factory_name = spec.split(":", 1)
    if (
        not module_name
        or not factory_name.isidentifier()
        or factory_name.startswith("_")
    ):
        raise ValueError(f"{setting_name} must use module:public_factory syntax")
    if not is_provider_module_allowed(module_name):
        raise ValueError(f"Provider module is not allowlisted: {module_name}")
    factory = getattr(importlib.import_module(module_name), factory_name, None)
    if not callable(factory):
        raise TypeError(f"Provider factory is not callable: {spec}")
    return factory
