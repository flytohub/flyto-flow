"""Fail-closed extension verification for application startup."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping

from services.extensions.manifest import (
    ALLOWED_PERMISSIONS,
    ExtensionPolicy,
    VerifiedExtension,
    discover_extensions,
)


def _trusted_keys() -> Mapping[str, str]:
    configured = os.environ.get("FLYTO_EXTENSION_TRUSTED_KEYS", "").strip()
    if not configured:
        return {}
    try:
        keys = json.loads(configured)
    except json.JSONDecodeError as exc:
        raise RuntimeError("FLYTO_EXTENSION_TRUSTED_KEYS must be valid JSON") from exc
    if not isinstance(keys, dict) or not all(
        isinstance(key, str) and key and isinstance(value, str) and value
        for key, value in keys.items()
    ):
        raise RuntimeError(
            "FLYTO_EXTENSION_TRUSTED_KEYS must be an object of key IDs to public keys"
        )
    return keys


def _permission_grants() -> Mapping[str, frozenset[str]]:
    configured = os.environ.get("FLYTO_EXTENSION_PERMISSION_GRANTS", "").strip()
    if not configured:
        return {}
    try:
        grants = json.loads(configured)
    except json.JSONDecodeError as exc:
        raise RuntimeError("FLYTO_EXTENSION_PERMISSION_GRANTS must be valid JSON") from exc
    if not isinstance(grants, dict):
        raise RuntimeError("FLYTO_EXTENSION_PERMISSION_GRANTS must be a JSON object")
    normalized: dict[str, frozenset[str]] = {}
    for extension_id, permissions in grants.items():
        if (
            not isinstance(extension_id, str)
            or not isinstance(permissions, list)
            or not all(isinstance(permission, str) for permission in permissions)
        ):
            raise RuntimeError(
                "Extension permission grants must map IDs to string arrays"
            )
        unknown = sorted(set(permissions) - ALLOWED_PERMISSIONS)
        if unknown:
            raise RuntimeError(
                f"Unknown permissions granted to {extension_id}: "
                + ", ".join(unknown)
            )
        normalized[extension_id] = frozenset(permissions)
    return normalized


def configured_plugin_root() -> Path:
    configured = os.environ.get(
        "FLYTO_PLUGINS_DIR",
        os.environ.get(
            "FLYTO_PLUGIN_DIR",
            str(Path.home() / ".flyto" / "plugins"),
        ),
    )
    return Path(configured).expanduser().resolve()


def configured_extension_root() -> Path:
    configured = os.environ.get("FLYTO_EXTENSIONS_DIR", "").strip()
    return (
        Path(configured).expanduser().resolve()
        if configured
        else configured_plugin_root()
    )


def verify_configured_extensions() -> list[VerifiedExtension]:
    raw_policy = os.environ.get(
        "FLYTO_EXTENSION_SIGNATURE_POLICY",
        ExtensionPolicy.REQUIRE_SIGNATURE.value,
    ).strip()
    try:
        policy = ExtensionPolicy(raw_policy)
    except ValueError as exc:
        raise RuntimeError(
            f"Unsupported FLYTO_EXTENSION_SIGNATURE_POLICY: {raw_policy}"
        ) from exc
    trusted_keys = _trusted_keys()
    permission_grants = _permission_grants()
    roots = {configured_extension_root(), configured_plugin_root()}
    verified: list[VerifiedExtension] = []
    identifiers: set[str] = set()
    for root in sorted(roots):
        for extension in discover_extensions(
            root,
            policy=policy,
            trusted_keys=trusted_keys,
        ):
            if extension.manifest.id in identifiers:
                raise ValueError(
                    f"Duplicate configured extension id: {extension.manifest.id}"
                )
            identifiers.add(extension.manifest.id)
            missing_permissions = sorted(
                set(extension.manifest.permissions)
                - permission_grants.get(extension.manifest.id, frozenset())
            )
            if missing_permissions:
                raise PermissionError(
                    f"Extension {extension.manifest.id} requires ungranted permissions: "
                    + ", ".join(missing_permissions)
                )
            verified.append(extension)
    return verified
