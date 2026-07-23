"""Edition-neutral external connection models and provider ports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Literal, Mapping, Protocol

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CONNECTION_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)+$")
PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")


def _empty_config_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }


class ConnectionScope(BaseModel):
    kind: Literal["organization", "workspace", "project", "workflow", "local"]
    id: str = Field(min_length=1, max_length=128)

    model_config = ConfigDict(frozen=True, extra="forbid")


class ConnectionDefinition(BaseModel):
    id: str
    name: str = ""
    description: str = ""
    category: str = "other"
    schema_version: int = Field(ge=1)
    config_schema: dict[str, Any] = Field(default_factory=_empty_config_schema)
    secret_slots: tuple[str, ...] = ()
    authentication_methods: tuple[str, ...] = ()
    transport_kinds: tuple[str, ...] = ()
    module_ids: tuple[str, ...] = ()
    deprecated: bool = False

    model_config = ConfigDict(frozen=True, extra="forbid")

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not CONNECTION_ID_PATTERN.fullmatch(value):
            raise ValueError("Connection type must be a namespaced lowercase identifier")
        return value

    @model_validator(mode="after")
    def validate_config_schema(self) -> ConnectionDefinition:
        if self.config_schema.get("type") != "object":
            raise ValueError("Connection config_schema must describe an object")
        if self.config_schema.get("additionalProperties") is not False:
            raise ValueError("Connection config_schema must reject additional properties")
        try:
            Draft202012Validator.check_schema(self.config_schema)
        except SchemaError as exc:
            raise ValueError(
                "Connection config_schema must be valid Draft 2020-12 JSON Schema"
            ) from exc
        return self


class ConnectionProfile(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=160)
    type: str
    schema_version: int = Field(ge=1)
    revision: int = Field(default=1, ge=1)
    scope: ConnectionScope
    config: dict[str, Any] = Field(default_factory=dict)
    secret_refs: dict[str, dict[str, Any]] = Field(default_factory=dict)
    policy: dict[str, Any] = Field(default_factory=dict)
    disabled: bool = False
    created_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("id")
    @classmethod
    def validate_profile_id(cls, value: str) -> str:
        if not PROFILE_ID_PATTERN.fullmatch(value):
            raise ValueError("Connection profile ID must be a lowercase slug")
        return value

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if not CONNECTION_ID_PATTERN.fullmatch(value):
            raise ValueError("Connection type must be a namespaced lowercase identifier")
        return value


class PolicyContext(BaseModel):
    actor_id: str
    workspace_id: str
    workflow_id: str | None = None
    execution_id: str | None = None
    operation: str

    model_config = ConfigDict(frozen=True, extra="forbid")


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str

    model_config = ConfigDict(frozen=True, extra="forbid")


class ConnectionCatalog(Protocol):
    def get(self, type_id: str) -> ConnectionDefinition | None: ...

    def list(self) -> list[ConnectionDefinition]: ...


class ConnectionProfileStore(Protocol):
    async def get(self, profile_id: str, scope_id: str) -> ConnectionProfile | None: ...

    async def list(self, scope_id: str) -> list[ConnectionProfile]: ...

    async def put(
        self,
        profile: ConnectionProfile,
        *,
        expected_revision: int | None = None,
    ) -> ConnectionProfile: ...

    async def delete(self, profile_id: str, scope_id: str) -> bool: ...


class ConnectionPolicy(Protocol):
    async def authorize(
        self,
        definition: ConnectionDefinition,
        profile: ConnectionProfile,
        context: PolicyContext,
    ) -> PolicyDecision: ...


class SecretResolver(Protocol):
    async def resolve(
        self,
        profile: ConnectionProfile,
        context: PolicyContext,
    ) -> Mapping[str, str]: ...


class TransportFactory(Protocol):
    async def create(
        self,
        definition: ConnectionDefinition,
        profile: ConnectionProfile,
        secrets: Mapping[str, str],
        context: PolicyContext,
    ) -> Any: ...


class ConnectionAuditSink(Protocol):
    async def record(
        self,
        *,
        profile: ConnectionProfile,
        context: PolicyContext,
        decision: PolicyDecision,
        result: str,
        duration_ms: int | None = None,
    ) -> None: ...


@dataclass(frozen=True)
class ConnectionRuntime:
    catalog: ConnectionCatalog
    profiles: ConnectionProfileStore
    policy: ConnectionPolicy
    secrets: SecretResolver
    transports: TransportFactory | None
    audit: ConnectionAuditSink
