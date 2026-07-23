"""Local connection catalog and profile management API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from gateway.local_context import LOCAL_WORKSPACE
from services.connections import (
    ConnectionProfile,
    ConnectionScope,
    ConnectionService,
    PolicyContext,
    get_connection_runtime,
)
from services.connections.contracts import CONNECTION_ID_PATTERN, PROFILE_ID_PATTERN


router = APIRouter(prefix="/connections")


class ConnectionProfileWrite(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: str
    schema_version: int = Field(ge=1)
    config: dict[str, Any] = Field(default_factory=dict)
    secret_refs: dict[str, dict[str, Any]] = Field(default_factory=dict)
    policy: dict[str, Any] = Field(default_factory=dict)
    disabled: bool = False
    expected_revision: int | None = Field(default=None, ge=0)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if not CONNECTION_ID_PATTERN.fullmatch(value):
            raise ValueError("Connection type is invalid")
        return value


def _validate_profile_id(profile_id: str) -> None:
    if not PROFILE_ID_PATTERN.fullmatch(profile_id):
        raise HTTPException(status_code=422, detail="Connection profile ID is invalid")


@router.get("/catalog")
async def list_connection_types():
    definitions = get_connection_runtime().catalog.list()
    return {
        "ok": True,
        "connection_types": [
            definition.model_dump(mode="json") for definition in definitions
        ],
    }


@router.get("/profiles")
async def list_connection_profiles():
    profiles = await ConnectionService.list_profiles(LOCAL_WORKSPACE.id)
    return {
        "ok": True,
        "profiles": [profile.model_dump(mode="json") for profile in profiles],
    }


@router.put("/profiles/{profile_id}")
async def put_connection_profile(
    profile_id: str,
    request: ConnectionProfileWrite,
):
    _validate_profile_id(profile_id)
    try:
        profile = ConnectionProfile(
            id=profile_id,
            name=request.name,
            type=request.type,
            schema_version=request.schema_version,
            scope=ConnectionScope(kind="workspace", id=LOCAL_WORKSPACE.id),
            config=request.config,
            secret_refs=request.secret_refs,
            policy=request.policy,
            disabled=request.disabled,
        )
        saved = await ConnectionService.put_profile(
            profile,
            expected_revision=request.expected_revision,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "profile": saved.model_dump(mode="json")}


@router.delete("/profiles/{profile_id}")
async def delete_connection_profile(
    profile_id: str,
    expected_revision: int | None = Query(default=None, ge=1),
):
    _validate_profile_id(profile_id)
    try:
        deleted = await ConnectionService.delete_profile(
            profile_id,
            LOCAL_WORKSPACE.id,
            expected_revision=expected_revision,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Connection profile not found")
    return {"ok": True}


@router.post("/profiles/{profile_id}/validate")
async def validate_connection_profile(profile_id: str):
    _validate_profile_id(profile_id)
    try:
        result = await ConnectionService.validate_access(
            profile_id,
            PolicyContext(
                actor_id=LOCAL_WORKSPACE.id,
                workspace_id=LOCAL_WORKSPACE.id,
                operation="test",
            ),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": result["allowed"], **result}
