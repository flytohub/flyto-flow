"""Connection runtime composition and fail-closed profile validation."""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from typing import Any

from gateway.providers.loading import load_provider_factory
from jsonschema import Draft202012Validator, FormatChecker
from services.connections.builtin import BUILTIN_CONNECTIONS
from services.connections.contracts import (
    ConnectionDefinition,
    ConnectionProfile,
    ConnectionRuntime,
)
from services.connections.local import create_local_connection_runtime
from services.extensions.manifest import VerifiedExtension


_runtime: ConnectionRuntime | None = None
_FORMAT_CHECKER = FormatChecker()
_POLICY_OPERATIONS = frozenset({"create", "read", "update", "delete", "test", "use"})
_POLICY_FIELDS = frozenset(
    {
        "allow_private_networks",
        "allowed_hosts",
        "allowed_operations",
        "allowed_ports",
        "allowed_protocols",
        "allowed_transport_kinds",
        "allowed_workflow_ids",
        "denied_workflow_ids",
    }
)
_SECRET_REF_FIELDS = frozenset({"type", "credential_name", "scope", "scope_id"})
_SECRET_SCOPES = frozenset({"organization", "workspace", "project", "workflow", "local"})
_SENSITIVE_NAMES = frozenset(
    {
        "authorization",
        "api_key",
        "apikey",
        "client_secret",
        "password",
        "private_key",
        "secret",
        "token",
        "webhook_url",
    }
)


def _is_sensitive_name(value: str) -> bool:
    normalized = value.lower().replace("-", "_")
    return normalized in _SENSITIVE_NAMES or normalized.endswith(("_password", "_secret", "_token"))


def _reject_plaintext_secrets(value: Any, path: str = "config") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if _is_sensitive_name(str(key)):
                raise ValueError(
                    f"Sensitive connection value must use secret_refs instead of {path}.{key}"
                )
            _reject_plaintext_secrets(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_plaintext_secrets(nested, f"{path}[{index}]")


def _validate_secret_references(profile: ConnectionProfile) -> None:
    for slot, reference in profile.secret_refs.items():
        if not isinstance(reference, Mapping):
            raise ValueError(f"Connection secret reference must be an object: {slot}")
        unknown_fields = sorted(set(reference) - _SECRET_REF_FIELDS)
        if unknown_fields:
            raise ValueError(
                f"Unknown connection secret reference fields for {slot}: "
                f"{', '.join(unknown_fields)}"
            )
        if reference.get("type") != "secretRef":
            raise ValueError(f"Connection secret slot must use SecretRef: {slot}")
        credential_name = reference.get("credential_name")
        if (
            not isinstance(credential_name, str)
            or not credential_name.strip()
            or len(credential_name) > 256
        ):
            raise ValueError(f"Connection secret credential_name is invalid: {slot}")
        scope = reference.get("scope", "workspace")
        if scope not in _SECRET_SCOPES:
            raise ValueError(f"Connection secret scope is invalid: {slot}")
        scope_id = reference.get("scope_id")
        if scope_id is not None and (
            not isinstance(scope_id, str) or not scope_id.strip() or len(scope_id) > 128
        ):
            raise ValueError(f"Connection secret scope_id is invalid: {slot}")
        if scope != profile.scope.kind or scope_id not in {None, profile.scope.id}:
            raise ValueError(
                f"Connection secret crosses {profile.scope.kind} boundary: {slot}"
            )


def _validate_policy(policy: Mapping[str, Any]) -> None:
    unknown_fields = sorted(set(policy) - _POLICY_FIELDS)
    if unknown_fields:
        raise ValueError(f"Unknown connection policy fields: {', '.join(unknown_fields)}")
    operations = policy.get("allowed_operations")
    if operations is not None:
        if (
            not isinstance(operations, list)
            or not operations
            or any(operation not in _POLICY_OPERATIONS for operation in operations)
        ):
            raise ValueError("Connection allowed_operations policy is invalid")
    for field in ("allowed_workflow_ids", "denied_workflow_ids"):
        values = policy.get(field)
        if values is not None and (
            not isinstance(values, list)
            or any(
                not isinstance(value, str) or not value.strip() or len(value) > 128
                for value in values
            )
        ):
            raise ValueError(f"Connection {field} policy is invalid")
    for field in ("allowed_hosts", "allowed_protocols", "allowed_transport_kinds"):
        values = policy.get(field)
        if values is not None and (
            not isinstance(values, list)
            or not values
            or any(
                not isinstance(value, str) or not value.strip() or len(value) > 253
                for value in values
            )
        ):
            raise ValueError(f"Connection {field} policy is invalid")
    ports = policy.get("allowed_ports")
    if ports is not None and (
        not isinstance(ports, list)
        or not ports
        or any(
            isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535
            for port in ports
        )
    ):
        raise ValueError("Connection allowed_ports policy is invalid")
    allow_private = policy.get("allow_private_networks")
    if allow_private is not None and not isinstance(allow_private, bool):
        raise ValueError("Connection allow_private_networks policy is invalid")


def validate_connection_profile(
    profile: ConnectionProfile,
    definitions: Mapping[str, ConnectionDefinition],
) -> None:
    definition = definitions.get(profile.type)
    if definition is None or definition.deprecated:
        raise ValueError(f"Connection type is unavailable: {profile.type}")
    if profile.schema_version != definition.schema_version:
        raise ValueError(
            f"Connection schema version mismatch for {profile.type}: "
            f"expected {definition.schema_version}, found {profile.schema_version}"
        )
    unknown_slots = sorted(set(profile.secret_refs) - set(definition.secret_slots))
    if unknown_slots:
        raise ValueError(f"Unknown connection secret slots: {', '.join(unknown_slots)}")
    _validate_secret_references(profile)
    _validate_policy(profile.policy)
    _reject_plaintext_secrets(profile.config)

    schema = definition.config_schema
    missing = sorted(set(schema.get("required", ())) - set(profile.config))
    if missing:
        raise ValueError(f"Missing required connection config: {', '.join(missing)}")
    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}))
        unknown = sorted(set(profile.config) - allowed)
        if unknown:
            raise ValueError(f"Unknown connection config fields: {', '.join(unknown)}")
    validator = Draft202012Validator(schema, format_checker=_FORMAT_CHECKER)
    errors = sorted(
        validator.iter_errors(profile.config),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            tuple(str(part) for part in error.absolute_schema_path),
        ),
    )
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise ValueError(
            f"Invalid connection config at {path} ({error.validator})"
        )


def _external_runtime(spec: str) -> ConnectionRuntime:
    factory = load_provider_factory(
        spec,
        setting_name="FLYTO_CONNECTION_RUNTIME_FACTORY",
    )
    runtime = factory()
    if not isinstance(runtime, ConnectionRuntime):
        raise TypeError("Connection runtime factory must return ConnectionRuntime")
    return runtime


def configure_connection_runtime(
    extensions: Iterable[VerifiedExtension] = (),
) -> ConnectionRuntime:
    global _runtime
    factory = os.environ.get("FLYTO_CONNECTION_RUNTIME_FACTORY", "").strip()
    if factory:
        _runtime = _external_runtime(factory)
        return _runtime

    definitions = {definition.id: definition for definition in BUILTIN_CONNECTIONS}
    for extension in extensions:
        for raw_definition in extension.manifest.connection_types:
            definition = ConnectionDefinition.model_validate(raw_definition)
            if definition.id in definitions:
                raise ValueError(f"Duplicate connection type: {definition.id}")
            definitions[definition.id] = definition
    _runtime = create_local_connection_runtime(definitions.values())
    return _runtime


def get_connection_runtime() -> ConnectionRuntime:
    return _runtime or configure_connection_runtime()


def reset_connection_runtime() -> None:
    global _runtime
    _runtime = None
