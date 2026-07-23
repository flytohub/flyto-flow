"""Application service for scoped connection profiles and runtime acquisition."""

from __future__ import annotations

from time import monotonic
from typing import Any

from services.connections.contracts import (
    ConnectionProfile,
    PolicyContext,
)
from services.connections.runtime import (
    get_connection_runtime,
    validate_connection_profile,
)


class ConnectionService:
    @staticmethod
    async def list_profiles(scope_id: str) -> list[ConnectionProfile]:
        return await get_connection_runtime().profiles.list(scope_id)

    @staticmethod
    async def put_profile(
        profile: ConnectionProfile,
        *,
        expected_revision: int | None = None,
    ) -> ConnectionProfile:
        runtime = get_connection_runtime()
        definitions = {item.id: item for item in runtime.catalog.list()}
        validate_connection_profile(profile, definitions)
        return await runtime.profiles.put(
            profile,
            expected_revision=expected_revision,
        )

    @staticmethod
    async def delete_profile(
        profile_id: str,
        scope_id: str,
        *,
        expected_revision: int | None = None,
    ) -> bool:
        runtime = get_connection_runtime()
        current = await runtime.profiles.get(profile_id, scope_id)
        if current is None:
            return False
        if expected_revision is not None and current.revision != expected_revision:
            raise RuntimeError(
                f"Connection profile revision conflict: expected "
                f"{expected_revision}, found {current.revision}"
            )
        return await runtime.profiles.delete(profile_id, scope_id)

    @staticmethod
    async def acquire(profile_id: str, context: PolicyContext) -> Any:
        runtime = get_connection_runtime()
        profile = await runtime.profiles.get(profile_id, context.workspace_id)
        if profile is None:
            raise KeyError(f"Connection profile not found: {profile_id}")
        definition = runtime.catalog.get(profile.type)
        if definition is None:
            raise KeyError(f"Connection type not found: {profile.type}")
        started = monotonic()
        decision = await runtime.policy.authorize(definition, profile, context)
        if not decision.allowed:
            await runtime.audit.record(
                profile=profile,
                context=context,
                decision=decision,
                result="denied",
            )
            raise PermissionError(f"Connection policy denied access: {decision.reason}")
        if runtime.transports is None:
            await runtime.audit.record(
                profile=profile,
                context=context,
                decision=decision,
                result="transport_unavailable",
            )
            raise RuntimeError(f"No transport provider is installed for {profile.type}")
        try:
            secrets = await runtime.secrets.resolve(profile, context)
            transport = await runtime.transports.create(
                definition,
                profile,
                secrets,
                context,
            )
        except Exception:
            await runtime.audit.record(
                profile=profile,
                context=context,
                decision=decision,
                result="failed",
                duration_ms=int((monotonic() - started) * 1000),
            )
            raise
        await runtime.audit.record(
            profile=profile,
            context=context,
            decision=decision,
            result="allowed",
            duration_ms=int((monotonic() - started) * 1000),
        )
        return transport

    @staticmethod
    async def validate_access(
        profile_id: str,
        context: PolicyContext,
    ) -> dict[str, Any]:
        runtime = get_connection_runtime()
        profile = await runtime.profiles.get(profile_id, context.workspace_id)
        if profile is None:
            raise KeyError(f"Connection profile not found: {profile_id}")
        definition = runtime.catalog.get(profile.type)
        if definition is None:
            raise KeyError(f"Connection type not found: {profile.type}")
        started = monotonic()
        decision = await runtime.policy.authorize(definition, profile, context)
        result = "denied"
        resolved_slots: list[str] = []
        if decision.allowed:
            try:
                secrets = await runtime.secrets.resolve(profile, context)
                resolved_slots = sorted(secrets)
                result = "validated"
            except Exception:
                await runtime.audit.record(
                    profile=profile,
                    context=context,
                    decision=decision,
                    result="failed",
                    duration_ms=int((monotonic() - started) * 1000),
                )
                raise
        await runtime.audit.record(
            profile=profile,
            context=context,
            decision=decision,
            result=result,
            duration_ms=int((monotonic() - started) * 1000),
        )
        return {
            "allowed": decision.allowed,
            "reason": decision.reason,
            "resolved_slots": resolved_slots,
        }
