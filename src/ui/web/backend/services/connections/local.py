"""Local connection profile, policy, secret, and audit adapters."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from gateway.providers.audit.local import LocalAuditProvider
from gateway.storage.offline_db import get_offline_cursor, offline_transaction
from services.connections.contracts import (
    ConnectionDefinition,
    ConnectionProfile,
    ConnectionRuntime,
    PolicyContext,
    PolicyDecision,
)
from services.credentials.models import CredentialScope
from services.credentials.service import CredentialService


class StaticConnectionCatalog:
    def __init__(self, definitions: Iterable[ConnectionDefinition] = ()) -> None:
        self._definitions = {definition.id: definition for definition in definitions}

    def get(self, type_id: str) -> ConnectionDefinition | None:
        return self._definitions.get(type_id)

    def list(self) -> list[ConnectionDefinition]:
        return sorted(self._definitions.values(), key=lambda definition: definition.id)


class LocalConnectionProfileStore:
    @staticmethod
    def _ensure_table() -> None:
        with get_offline_cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS connection_profiles (
                    id TEXT NOT NULL,
                    scope_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    revision INTEGER NOT NULL,
                    scope TEXT NOT NULL,
                    config TEXT NOT NULL,
                    secret_refs TEXT NOT NULL,
                    policy TEXT NOT NULL,
                    disabled INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (id, scope_id)
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_connection_profiles_scope "
                "ON connection_profiles(scope_id, name)"
            )

    async def get(self, profile_id: str, scope_id: str) -> ConnectionProfile | None:
        self._ensure_table()
        with get_offline_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM connection_profiles WHERE id = ? AND scope_id = ?",
                (profile_id, scope_id),
            )
            row = cursor.fetchone()
        return self._decode(row) if row else None

    async def list(self, scope_id: str) -> list[ConnectionProfile]:
        self._ensure_table()
        with get_offline_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM connection_profiles WHERE scope_id = ? ORDER BY name, id",
                (scope_id,),
            )
            rows = cursor.fetchall()
        return [self._decode(row) for row in rows]

    async def put(
        self,
        profile: ConnectionProfile,
        *,
        expected_revision: int | None = None,
    ) -> ConnectionProfile:
        self._ensure_table()
        now = datetime.now(timezone.utc).isoformat()
        with offline_transaction(immediate=True) as connection:
            current = connection.execute(
                "SELECT revision, created_at FROM connection_profiles "
                "WHERE id = ? AND scope_id = ?",
                (profile.id, profile.scope.id),
            ).fetchone()
            if expected_revision is not None:
                actual = int(current["revision"]) if current else 0
                if actual != expected_revision:
                    raise RuntimeError(
                        f"Connection profile revision conflict: expected "
                        f"{expected_revision}, found {actual}"
                    )
            revision = int(current["revision"]) + 1 if current else 1
            created_at = current["created_at"] if current else now
            payload = (
                profile.id,
                profile.scope.id,
                profile.name,
                profile.type,
                profile.schema_version,
                revision,
                profile.scope.model_dump_json(),
                json.dumps(profile.config, sort_keys=True, separators=(",", ":")),
                json.dumps(profile.secret_refs, sort_keys=True, separators=(",", ":")),
                json.dumps(profile.policy, sort_keys=True, separators=(",", ":")),
                int(profile.disabled),
                created_at,
                now,
            )
            connection.execute(
                """
                INSERT INTO connection_profiles (
                    id, scope_id, name, type, schema_version, revision, scope,
                    config, secret_refs, policy, disabled, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id, scope_id) DO UPDATE SET
                    name = excluded.name,
                    type = excluded.type,
                    schema_version = excluded.schema_version,
                    revision = excluded.revision,
                    scope = excluded.scope,
                    config = excluded.config,
                    secret_refs = excluded.secret_refs,
                    policy = excluded.policy,
                    disabled = excluded.disabled,
                    updated_at = excluded.updated_at
                """,
                payload,
            )
        saved = profile.model_copy(
            update={"revision": revision, "created_at": created_at, "updated_at": now}
        )
        return saved

    async def delete(self, profile_id: str, scope_id: str) -> bool:
        self._ensure_table()
        with get_offline_cursor() as cursor:
            cursor.execute(
                "DELETE FROM connection_profiles WHERE id = ? AND scope_id = ?",
                (profile_id, scope_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def _decode(row: dict[str, Any]) -> ConnectionProfile:
        return ConnectionProfile(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            schema_version=row["schema_version"],
            revision=row["revision"],
            scope=json.loads(row["scope"]),
            config=json.loads(row["config"]),
            secret_refs=json.loads(row["secret_refs"]),
            policy=json.loads(row["policy"]),
            disabled=bool(row["disabled"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class LocalConnectionPolicy:
    async def authorize(
        self,
        definition: ConnectionDefinition,
        profile: ConnectionProfile,
        context: PolicyContext,
    ) -> PolicyDecision:
        if profile.disabled:
            return PolicyDecision(allowed=False, reason="profile_disabled")
        if profile.scope.id != context.workspace_id:
            return PolicyDecision(allowed=False, reason="workspace_mismatch")
        if definition.id != profile.type:
            return PolicyDecision(allowed=False, reason="definition_mismatch")
        if context.operation not in {"create", "read", "update", "delete", "test", "use"}:
            return PolicyDecision(allowed=False, reason="unknown_operation")
        allowed_operations = profile.policy.get("allowed_operations")
        if isinstance(allowed_operations, list) and context.operation not in allowed_operations:
            return PolicyDecision(allowed=False, reason="operation_not_allowed")
        denied_workflows = profile.policy.get("denied_workflow_ids", [])
        if context.workflow_id and context.workflow_id in denied_workflows:
            return PolicyDecision(allowed=False, reason="workflow_denied")
        allowed_workflows = profile.policy.get("allowed_workflow_ids")
        if (
            context.workflow_id
            and isinstance(allowed_workflows, list)
            and context.workflow_id not in allowed_workflows
        ):
            return PolicyDecision(allowed=False, reason="workflow_not_allowed")
        return PolicyDecision(allowed=True, reason="local_workspace_policy")


class LocalSecretResolver:
    async def resolve(
        self,
        profile: ConnectionProfile,
        context: PolicyContext,
    ) -> Mapping[str, str]:
        resolved: dict[str, str] = {}
        for slot, reference in profile.secret_refs.items():
            if reference.get("type") != "secretRef":
                raise ValueError(f"Connection secret slot {slot!r} is not a SecretRef")
            raw_scope = reference.get("scope", "workspace")
            try:
                scope = CredentialScope(raw_scope)
            except ValueError as exc:
                raise ValueError(f"Unsupported credential scope: {raw_scope}") from exc
            scope_id = reference.get("scope_id") or context.workspace_id
            value = CredentialService.get(
                reference.get("credential_name", ""),
                scope,
                scope_id,
                context.workspace_id,
            )
            if value is None:
                raise KeyError(f"Connection secret slot is unavailable: {slot}")
            resolved[slot] = value
        return resolved


class LocalConnectionAuditSink:
    def __init__(self, audit: LocalAuditProvider | None = None) -> None:
        self._audit = audit or LocalAuditProvider()

    async def record(
        self,
        *,
        profile: ConnectionProfile,
        context: PolicyContext,
        decision: PolicyDecision,
        result: str,
        duration_ms: int | None = None,
    ) -> None:
        await self._audit.log(
            action=f"connection.{context.operation}",
            actor_id=context.actor_id,
            resource_type="connection",
            resource_id=profile.id,
            result=result,
            details={
                "workspace_id": context.workspace_id,
                "workflow_id": context.workflow_id,
                "execution_id": context.execution_id,
                "connection_type": profile.type,
                "profile_revision": profile.revision,
                "policy_allowed": decision.allowed,
                "policy_reason": decision.reason,
                "duration_ms": duration_ms,
            },
        )


def create_local_connection_runtime(
    definitions: Iterable[ConnectionDefinition] = (),
) -> ConnectionRuntime:
    return ConnectionRuntime(
        catalog=StaticConnectionCatalog(definitions),
        profiles=LocalConnectionProfileStore(),
        policy=LocalConnectionPolicy(),
        secrets=LocalSecretResolver(),
        transports=None,
        audit=LocalConnectionAuditSink(),
    )
