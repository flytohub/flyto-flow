"""Fail-closed organization and workspace RBAC primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from gateway.providers.identity.contracts import PrincipalContext


BUILTIN_ROLES: dict[str, frozenset[str]] = {
    "viewer": frozenset(
        {
            "workflow.read",
            "execution.read",
            "template.read",
            "connection.read",
            "audit.read",
        }
    ),
    "editor": frozenset(
        {
            "workflow.*",
            "execution.read",
            "execution.run",
            "template.*",
            "connection.read",
            "connection.use",
        }
    ),
    "operator": frozenset(
        {
            "workflow.*",
            "execution.*",
            "template.*",
            "connection.*",
            "credential.use",
            "audit.read",
        }
    ),
    "workspace-admin": frozenset(
        {
            "workflow.*",
            "execution.*",
            "template.*",
            "connection.*",
            "credential.*",
            "audit.read",
            "workspace.*",
        }
    ),
    "organization-admin": frozenset(
        {
            "workflow.*",
            "execution.*",
            "template.*",
            "connection.*",
            "credential.*",
            "audit.*",
            "workspace.*",
            "organization.*",
        }
    ),
}


@dataclass(frozen=True)
class AccessRequest:
    permission: str
    organization_id: str
    workspace_id: str | None = None


def _permission_matches(granted: str, requested: str) -> bool:
    if granted == requested:
        return True
    if granted.endswith(".*"):
        prefix = granted[:-1]
        return requested.startswith(prefix)
    return False


class RBACAccessProvider:
    """RBAC evaluator for external identity providers and private editions."""

    def __init__(
        self,
        roles: Mapping[str, Iterable[str]] | None = None,
    ) -> None:
        merged = {name: frozenset(values) for name, values in BUILTIN_ROLES.items()}
        if roles:
            merged.update({name: frozenset(values) for name, values in roles.items()})
        self._roles = merged

    @property
    def name(self) -> str:
        return "scoped-rbac"

    async def check_permission(
        self,
        actor: PrincipalContext,
        permission: str,
        resource: str | None = None,
    ) -> bool:
        organization_id, workspace_id = self._parse_resource(resource)
        request = AccessRequest(permission, organization_id, workspace_id)
        return self.authorize(actor, request)

    def authorize(self, actor: PrincipalContext, request: AccessRequest) -> bool:
        if (
            not request.permission
            or not request.organization_id
            or not actor.is_active
            or actor.organization_id != request.organization_id
        ):
            return False
        if request.workspace_id and request.workspace_id not in actor.workspace_ids:
            if not actor.is_admin:
                return False
        if actor.is_admin:
            return True
        roles = set(actor.roles)
        roles.update(
            binding.role
            for binding in actor.role_bindings
            if binding.organization_id == request.organization_id
            and (
                (request.workspace_id is None and binding.workspace_id is None)
                or (
                    request.workspace_id is not None
                    and binding.workspace_id in {None, request.workspace_id}
                )
            )
        )
        granted = {
            permission
            for role in roles
            for permission in self._roles.get(role, ())
        }
        return any(_permission_matches(permission, request.permission) for permission in granted)

    async def get_accessible_pages(self, actor: PrincipalContext) -> list[str]:
        if not actor.is_active:
            return []
        pages = ["/", "/my-templates", "/mcp"]
        if actor.is_admin or set(actor.roles) & {"operator", "workspace-admin", "organization-admin"}:
            pages.extend(("/variables", "/observability"))
        return pages

    @staticmethod
    def _parse_resource(resource: str | None) -> tuple[str, str | None]:
        if not resource:
            return "", None
        parts = resource.split("/", 1)
        organization_id = parts[0]
        workspace_id = parts[1] if len(parts) == 2 else None
        if not organization_id or workspace_id == "":
            return "", None
        return organization_id, workspace_id
