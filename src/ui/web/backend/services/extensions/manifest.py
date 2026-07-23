"""Supply-chain validation for Flyto2 extension bundles."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)+$")
SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
ALLOWED_PERMISSIONS = frozenset(
    {
        "browser",
        "filesystem.read",
        "filesystem.write",
        "network",
        "process",
        "secrets.read",
    }
)


class ExtensionKind(str, Enum):
    CONNECTOR = "connector"
    PLUGIN = "plugin"
    TEMPLATE_PACK = "template-pack"


class ExtensionArtifact(BaseModel):
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    model_config = ConfigDict(frozen=True, extra="forbid")

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        path = Path(value)
        if not value.strip() or path == Path("."):
            raise ValueError("Extension artifact paths must not be empty")
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Extension artifact paths must remain inside the bundle")
        return path.as_posix()


class ExtensionSignature(BaseModel):
    algorithm: str = Field(pattern=r"^ed25519$")
    key_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,127}$")
    value: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True, extra="forbid")

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        try:
            decoded = base64.b64decode(value, validate=True)
        except ValueError as exc:
            raise ValueError("Extension signature must be valid base64") from exc
        if len(decoded) != 64:
            raise ValueError("Ed25519 signatures must contain 64 bytes")
        return value


class ExtensionManifest(BaseModel):
    schema_name: str = Field(alias="schema", pattern=r"^flyto\.extension\.v1$")
    id: str
    name: str = Field(min_length=1)
    version: str
    api_version: str = Field(pattern=r"^v1$")
    kind: ExtensionKind
    permissions: tuple[str, ...] = ()
    artifacts: tuple[ExtensionArtifact, ...] = Field(min_length=1)
    connection_types: tuple[dict[str, Any], ...] = ()
    signature: ExtensionSignature | None = None

    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError("Extension id must be a namespaced lowercase identifier")
        return value

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if not SEMVER_PATTERN.fullmatch(value):
            raise ValueError("Extension version must use strict SemVer")
        return value

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        unknown = sorted(set(values) - ALLOWED_PERMISSIONS)
        if unknown:
            raise ValueError(f"Unknown extension permissions: {', '.join(unknown)}")
        return tuple(sorted(set(values)))

    @field_validator("artifacts")
    @classmethod
    def validate_artifacts(
        cls,
        values: tuple[ExtensionArtifact, ...],
    ) -> tuple[ExtensionArtifact, ...]:
        paths = [artifact.path for artifact in values]
        if len(paths) != len(set(paths)):
            raise ValueError("Extension artifact paths must be unique")
        return values

    @field_validator("connection_types")
    @classmethod
    def validate_connection_types(
        cls,
        values: tuple[dict[str, Any], ...],
    ) -> tuple[dict[str, Any], ...]:
        from services.connections.contracts import ConnectionDefinition

        definitions = [
            ConnectionDefinition.model_validate(value).model_dump(mode="json")
            for value in values
        ]
        identifiers = [definition["id"] for definition in definitions]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Connection type IDs must be unique within an extension")
        return tuple(definitions)

    @model_validator(mode="after")
    def validate_kind_contract(self):
        if self.connection_types and self.kind != ExtensionKind.CONNECTOR:
            raise ValueError("Only connector extensions may declare connection_types")
        if self.kind == ExtensionKind.TEMPLATE_PACK:
            if self.permissions:
                raise ValueError("Template packs cannot request runtime permissions")
            if (
                len(self.artifacts) != 1
                or not self.artifacts[0].path.endswith(".json")
            ):
                raise ValueError("Template packs must declare exactly one JSON artifact")
        return self


class ExtensionPolicy(str, Enum):
    ALLOW_UNSIGNED = "allow-unsigned"
    REQUIRE_SIGNATURE = "require-signature"


@dataclass(frozen=True)
class VerifiedExtension:
    root: Path
    manifest: ExtensionManifest
    manifest_sha256: str
    signed: bool


def _canonical_payload(data: dict[str, Any]) -> bytes:
    payload = dict(data)
    payload.pop("signature", None)
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def _verify_signature(
    data: dict[str, Any],
    signature: ExtensionSignature,
    trusted_keys: Mapping[str, str],
) -> None:
    encoded_key = trusted_keys.get(signature.key_id)
    if not encoded_key:
        raise ValueError(f"Extension signing key is not trusted: {signature.key_id}")
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        raw_public_key = base64.b64decode(encoded_key, validate=True)
        if len(raw_public_key) != 32:
            raise ValueError("Ed25519 public keys must contain 32 bytes")
        public_key = Ed25519PublicKey.from_public_bytes(raw_public_key)
        public_key.verify(
            base64.b64decode(signature.value, validate=True),
            _canonical_payload(data),
        )
    except Exception as exc:
        raise ValueError("Extension signature verification failed") from exc


def load_extension_manifest(
    path: Path,
    *,
    policy: ExtensionPolicy = ExtensionPolicy.REQUIRE_SIGNATURE,
    trusted_keys: Mapping[str, str] | None = None,
) -> VerifiedExtension:
    path = path.resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    manifest = ExtensionManifest.model_validate(data)
    if policy == ExtensionPolicy.REQUIRE_SIGNATURE and manifest.signature is None:
        raise ValueError(f"Extension signature required: {path}")
    if manifest.signature:
        revoked = {
            key.strip()
            for key in os.environ.get("FLYTO_EXTENSION_REVOKED_KEYS", "").split(",")
            if key.strip()
        }
        if manifest.signature.key_id in revoked:
            raise ValueError(
                f"Extension signing key is revoked: {manifest.signature.key_id}"
            )
        _verify_signature(data, manifest.signature, trusted_keys or {})

    root = path.parent
    max_artifact_bytes = int(
        os.environ.get(
            "FLYTO_EXTENSION_MAX_ARTIFACT_BYTES",
            str(512 * 1024 * 1024),
        )
    )
    if max_artifact_bytes < 1:
        raise ValueError("FLYTO_EXTENSION_MAX_ARTIFACT_BYTES must be positive")
    for artifact in manifest.artifacts:
        artifact_path = (root / artifact.path).resolve()
        unresolved_path = root / artifact.path
        if unresolved_path.is_symlink():
            raise ValueError(f"Extension artifacts must not be symlinks: {artifact.path}")
        if root not in artifact_path.parents or not artifact_path.is_file():
            raise ValueError(f"Extension artifact is missing or escapes bundle: {artifact.path}")
        if artifact_path.stat().st_size > max_artifact_bytes:
            raise ValueError(f"Extension artifact exceeds the size limit: {artifact.path}")
        digest = hashlib.sha256()
        with artifact_path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        actual = digest.hexdigest()
        if actual != artifact.sha256:
            raise ValueError(f"Extension artifact digest mismatch: {artifact.path}")

    declared_paths = {artifact.path for artifact in manifest.artifacts}
    unmanaged_paths = sorted(
        candidate.relative_to(root).as_posix()
        for candidate in root.rglob("*")
        if (
            candidate.is_symlink()
            or (
                candidate.is_file()
                and candidate.name != "flyto-extension.json"
                and candidate.relative_to(root).as_posix() not in declared_paths
            )
        )
    )
    if unmanaged_paths:
        raise ValueError(
            "Extension bundle contains undeclared files: " + ", ".join(unmanaged_paths)
        )

    return VerifiedExtension(
        root=root,
        manifest=manifest,
        manifest_sha256=hashlib.sha256(_canonical_payload(data)).hexdigest(),
        signed=manifest.signature is not None,
    )


def discover_extensions(
    root: Path,
    *,
    policy: ExtensionPolicy = ExtensionPolicy.REQUIRE_SIGNATURE,
    trusted_keys: Mapping[str, str] | None = None,
) -> list[VerifiedExtension]:
    if not root.is_dir():
        return []
    manifests = [
        load_extension_manifest(path, policy=policy, trusted_keys=trusted_keys)
        for path in sorted(root.glob("*/flyto-extension.json"))
    ]
    identifiers = [extension.manifest.id for extension in manifests]
    duplicates = sorted(
        identifier for identifier in set(identifiers) if identifiers.count(identifier) > 1
    )
    if duplicates:
        raise ValueError(f"Duplicate extension ids: {', '.join(duplicates)}")

    missing_manifests = [
        child.name
        for child in sorted(root.iterdir())
        if child.is_dir()
        and not child.name.startswith(".")
        and any(child.iterdir())
        and not (child / "flyto-extension.json").is_file()
    ]
    if missing_manifests:
        raise ValueError(
            "Extension bundles are missing flyto-extension.json: "
            + ", ".join(missing_manifests)
        )
    return manifests
