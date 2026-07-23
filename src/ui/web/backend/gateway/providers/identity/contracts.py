"""Portable SSO and SCIM contracts implemented by downstream editions."""

from __future__ import annotations

from enum import Enum
import re
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator, model_validator


DNS_NAME_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)


class SSOProtocol(str, Enum):
    OIDC = "oidc"
    SAML2 = "saml2"


class SSOConfiguration(BaseModel):
    """Non-secret SSO metadata; credentials remain external references."""

    id: str
    organization_id: str
    protocol: SSOProtocol
    issuer: str
    discovery_url: HttpUrl | None = None
    metadata_url: HttpUrl | None = None
    client_id: str | None = None
    secret_ref: str | None = None
    allowed_domains: list[str] = Field(default_factory=list)
    enabled: bool = True

    model_config = ConfigDict(frozen=True, extra="forbid")

    @field_validator("allowed_domains")
    @classmethod
    def normalize_domains(cls, values: list[str]) -> list[str]:
        normalized = sorted(
            {value.strip().lower().rstrip(".") for value in values if value.strip()}
        )
        if any(not DNS_NAME_PATTERN.fullmatch(value) for value in normalized):
            raise ValueError("SSO allowed domains must be DNS names")
        return normalized

    @field_validator("discovery_url", "metadata_url")
    @classmethod
    def require_https_metadata(cls, value: HttpUrl | None) -> HttpUrl | None:
        if value is not None and value.scheme != "https":
            raise ValueError("SSO discovery and metadata URLs must use HTTPS")
        return value

    @field_validator("id", "organization_id", "issuer")
    @classmethod
    def require_nonempty_identity_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("SSO identity fields must not be empty")
        return value

    @model_validator(mode="after")
    def validate_protocol_fields(self):
        if self.protocol == SSOProtocol.OIDC:
            if self.discovery_url is None or not self.client_id:
                raise ValueError("OIDC requires discovery_url and client_id")
        elif self.metadata_url is None:
            raise ValueError("SAML 2.0 requires metadata_url")
        return self


class RoleBinding(BaseModel):
    role: str
    organization_id: str
    workspace_id: str | None = None

    model_config = ConfigDict(frozen=True, extra="forbid")

    @field_validator("role", "organization_id", "workspace_id")
    @classmethod
    def require_nonempty_scope(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Role binding fields must not be empty")
        return value


class PrincipalContext(BaseModel):
    id: str
    external_id: str | None = None
    organization_id: str
    workspace_ids: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    role_bindings: tuple[RoleBinding, ...] = ()
    email: str | None = None
    is_admin: bool = False
    is_active: bool = True

    model_config = ConfigDict(frozen=True, extra="forbid")

    @field_validator("id", "organization_id")
    @classmethod
    def require_nonempty_principal_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Principal identity fields must not be empty")
        return value

    @field_validator("workspace_ids", "roles")
    @classmethod
    def normalize_unique_values(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(sorted({value.strip() for value in values if value.strip()}))
        return normalized


class SCIMPrincipal(BaseModel):
    id: str
    external_id: str | None = None
    user_name: str
    display_name: str | None = None
    active: bool = True
    emails: list[EmailStr] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True, extra="forbid")


class SCIMGroup(BaseModel):
    id: str
    external_id: str | None = None
    display_name: str
    members: list[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True, extra="forbid")


@runtime_checkable
class IdentityProvider(Protocol):
    @property
    def name(self) -> str: ...

    async def begin_login(
        self,
        configuration: SSOConfiguration,
        redirect_uri: str,
        state: str,
    ) -> str: ...

    async def complete_login(
        self,
        configuration: SSOConfiguration,
        callback: dict[str, str],
    ) -> PrincipalContext: ...

    async def validate_session(self, token: str) -> PrincipalContext | None: ...

    async def logout(self, token: str) -> None: ...

    async def health_check(self) -> dict[str, Any]: ...


@runtime_checkable
class ProvisioningProvider(Protocol):
    """SCIM 2.0 storage contract with organization isolation."""

    async def list_principals(
        self,
        organization_id: str,
        *,
        filter_expression: str | None = None,
        start_index: int = 1,
        count: int = 100,
    ) -> tuple[list[SCIMPrincipal], int]: ...

    async def get_principal(
        self,
        organization_id: str,
        principal_id: str,
    ) -> SCIMPrincipal | None: ...

    async def upsert_principal(
        self,
        organization_id: str,
        principal: SCIMPrincipal,
    ) -> SCIMPrincipal: ...

    async def deactivate_principal(
        self,
        organization_id: str,
        principal_id: str,
    ) -> bool: ...

    async def list_groups(self, organization_id: str) -> list[SCIMGroup]: ...

    async def get_group(
        self,
        organization_id: str,
        group_id: str,
    ) -> SCIMGroup | None: ...

    async def upsert_group(
        self,
        organization_id: str,
        group: SCIMGroup,
    ) -> SCIMGroup: ...

    async def delete_group(
        self,
        organization_id: str,
        group_id: str,
    ) -> bool: ...

    async def health_check(self) -> dict[str, Any]: ...
