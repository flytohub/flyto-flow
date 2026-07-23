"""
Variables API

REST endpoints for managing workflow variables and credentials.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from gateway.storage.variable_repo import (
    Variable,
    VariableRepository,
    VariableScope,
    VariableType,
    Environment,
)
from services.credentials import (
    Credential,
    CredentialService,
    CredentialScope,
    CredentialType,
    get_type_schemas,
    pack_credential_value,
)

logger = logging.getLogger(__name__)
LOCAL_ACTOR_ID = "local-workspace"

router = APIRouter(prefix="/variables", tags=["variables"])


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateVariableRequest(BaseModel):
    """Request to create a variable."""

    name: str = Field(..., min_length=1, max_length=100)
    value: str
    value_type: str = "string"
    scope: str = "workflow"
    scope_id: str
    environment: str = "all"
    is_secret: bool = False
    description: Optional[str] = None


class UpdateVariableRequest(BaseModel):
    """Request to update a variable."""

    name: Optional[str] = None
    value: Optional[str] = None
    value_type: Optional[str] = None
    environment: Optional[str] = None
    description: Optional[str] = None


class VariableResponse(BaseModel):
    """Variable response."""

    id: str
    name: str
    value: Optional[str] = None
    value_type: str
    scope: str
    scope_id: str
    environment: str
    is_secret: bool
    description: Optional[str] = None
    created_at: str
    updated_at: str


class CreateCredentialRequest(BaseModel):
    """Request to create a credential."""

    name: str = Field(..., min_length=1, max_length=100)
    value: Optional[str] = None
    fields: Optional[Dict[str, str]] = None
    credential_type: str = "generic"
    scope: str = "workflow"
    scope_id: str
    description: Optional[str] = None


class RevealCredentialRequest(BaseModel):
    """Request to reveal a credential value."""

    reason: str = Field(..., min_length=10, max_length=500)


class CredentialResponse(BaseModel):
    """Credential response (never includes value)."""

    id: str
    name: str
    credential_type: str = "generic"
    scope: str
    scope_id: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
    last_accessed_at: Optional[str] = None
    access_count: int


# ============================================================================
# Variable Endpoints
# ============================================================================


@router.post("/", response_model=VariableResponse)
async def create_variable(
    request: CreateVariableRequest,
) -> Dict[str, Any]:
    """
    Create a new variable.

    Variables can be scoped to this workspace, a project, or a workflow.
    Secrets are stored encrypted.
    """
    try:
        scope = VariableScope(request.scope)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope: {request.scope}",
        )

    try:
        value_type = VariableType(request.value_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid value_type: {request.value_type}",
        )

    try:
        environment = Environment(request.environment)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid environment: {request.environment}",
        )

    variable = Variable(
        id="",
        name=request.name,
        value=request.value,
        value_type=value_type,
        scope=scope,
        scope_id=request.scope_id,
        environment=environment,
        is_secret=request.is_secret,
        description=request.description,
        created_by=LOCAL_ACTOR_ID,
    )

    try:
        created = VariableRepository.create(variable)
        return created.to_dict()
    except Exception as e:
        logger.error(f"Failed to create variable: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/")
async def list_variables(
    scope: Optional[str] = None,
    scope_id: Optional[str] = None,
    environment: Optional[str] = None,
    group_by: Optional[str] = Query(default=None, description="Group by: 'scope' or 'environment'"),
) -> Dict[str, Any]:
    """
    List variables with optional filters.

    S-Grade: Returns pre-grouped data when group_by is specified.

    Args:
        scope: Filter by scope (workspace, project, workflow)
        scope_id: Filter by scope ID
        environment: Filter by environment
        group_by: Group results by 'scope' or 'environment'
    """
    var_scope = None
    if scope:
        try:
            var_scope = VariableScope(scope)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid scope: {scope}")

    var_env = None
    if environment:
        try:
            var_env = Environment(environment)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid environment: {environment}",
            )

    variables = VariableRepository.list_variables(
        scope=var_scope,
        scope_id=scope_id,
        environment=var_env,
    )

    variable_dicts = [v.to_dict() for v in variables]
    result = {"ok": True, "variables": variable_dicts}

    # S-Grade: Pre-compute groupings on backend
    if group_by == "scope":
        result["by_scope"] = _group_variables_by_scope(variable_dicts)
    elif group_by == "environment":
        result["by_environment"] = _group_variables_by_environment(variable_dicts)
    elif group_by == "all":
        result["by_scope"] = _group_variables_by_scope(variable_dicts)
        result["by_environment"] = _group_variables_by_environment(variable_dicts)

    return result


def _group_variables_by_scope(variables: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group variables by scope (backend computation)."""
    grouped = {
        "workspace": [],
        "project": [],
        "workflow": []
    }
    for v in variables:
        scope = v.get("scope", "workflow")
        if scope in grouped:
            grouped[scope].append(v)
    return grouped


def _group_variables_by_environment(variables: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group variables by environment (backend computation)."""
    grouped = {
        "all": [],
        "development": [],
        "staging": [],
        "production": []
    }
    for v in variables:
        env = v.get("environment", "all")
        if env in grouped:
            grouped[env].append(v)
    return grouped


@router.patch("/{variable_id}", response_model=VariableResponse)
async def update_variable(
    variable_id: str,
    request: UpdateVariableRequest,
) -> Dict[str, Any]:
    """Update a variable."""
    updates = request.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No fields to update",
        )

    success = VariableRepository.update(variable_id, **updates)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Variable {variable_id} not found",
        )

    variable = VariableRepository.get(variable_id)
    return variable.to_dict()


@router.delete("/{variable_id}")
async def delete_variable(variable_id: str) -> Dict[str, Any]:
    """Delete a variable."""
    success = VariableRepository.delete(variable_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Variable {variable_id} not found",
        )

    return {"ok": True, "deleted": variable_id}


@router.get("/resolve/{workflow_id}")
async def resolve_variables(
    workflow_id: str,
    project_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    environment: str = "development",
) -> Dict[str, Any]:
    """
    Resolve all variables for a workflow execution.

    Applies inheritance: workspace -> project -> workflow.
    """
    try:
        env = Environment(environment)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid environment: {environment}",
        )

    resolved = VariableRepository.resolve_variables(
        workflow_id=workflow_id,
        project_id=project_id,
        workspace_id=workspace_id,
        environment=env,
        include_secrets=False,
    )

    return {"ok": True, "resolved": resolved, "count": len(resolved)}


# ============================================================================
# Credential Endpoints
# ============================================================================


@router.post("/credentials", response_model=CredentialResponse)
async def create_credential(
    request: CreateCredentialRequest,
) -> Dict[str, Any]:
    """
    Create a new credential (secret).

    Credentials are always stored encrypted.
    """
    try:
        scope = CredentialScope(request.scope)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope: {request.scope}",
        )

    try:
        cred_type = CredentialType(request.credential_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid credential_type: {request.credential_type}",
        )

    # Resolve the stored value from either `value` or `fields`
    if request.fields:
        stored_value = pack_credential_value(request.credential_type, request.fields)
    elif request.value:
        stored_value = request.value
    else:
        raise HTTPException(status_code=400, detail="Either value or fields is required")

    try:
        credential = CredentialService.create(
            name=request.name,
            value=stored_value,
            scope=scope,
            scope_id=request.scope_id,
            description=request.description,
            workspace_id=LOCAL_ACTOR_ID,
            credential_type=cred_type,
        )
        return credential.to_dict()
    except Exception as e:
        logger.error(f"Failed to create credential: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/credentials")
async def list_credentials(
    scope: Optional[str] = None,
    scope_id: Optional[str] = None,
    group_by: Optional[str] = Query(default=None, description="Group by: 'type' or 'scope'"),
) -> Dict[str, Any]:
    """
    List credentials (metadata only, no values).

    S-Grade: Returns pre-grouped data when group_by is specified.
    """
    if not scope or not scope_id:
        # Return empty list if no scope specified
        return {"ok": True, "credentials": []}

    try:
        cred_scope = CredentialScope(scope)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope: {scope}",
        )

    credentials = CredentialService.list_credentials(cred_scope, scope_id)
    credential_dicts = [c.to_dict() for c in credentials]
    result = {"ok": True, "credentials": credential_dicts, "type_schemas": get_type_schemas()}

    # S-Grade: Pre-compute groupings on backend
    if group_by == "type":
        result["by_type"] = _group_credentials_by_type(credential_dicts)
    elif group_by == "scope":
        result["by_scope"] = _group_credentials_by_scope(credential_dicts)
    elif group_by == "all":
        result["by_type"] = _group_credentials_by_type(credential_dicts)
        result["by_scope"] = _group_credentials_by_scope(credential_dicts)

    return result


def _group_credentials_by_type(credentials: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group credentials by type (backend computation)."""
    grouped = {}
    for c in credentials:
        cred_type = c.get("type", "generic")
        if cred_type not in grouped:
            grouped[cred_type] = []
        grouped[cred_type].append(c)
    return grouped


def _group_credentials_by_scope(credentials: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group credentials by scope (backend computation)."""
    grouped = {
        "workspace": [],
        "project": [],
        "workflow": []
    }
    for c in credentials:
        scope = c.get("scope", "workflow")
        if scope in grouped:
            grouped[scope].append(c)
    return grouped


@router.post("/credentials/{name}/reveal")
async def reveal_credential(
    name: str,
    request: RevealCredentialRequest,
    scope: str = Query(...),
    scope_id: str = Query(...),
) -> Dict[str, Any]:
    """
    Reveal a credential value (requires reason for audit).

    This action is logged for compliance.
    """
    try:
        cred_scope = CredentialScope(scope)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope: {scope}",
        )

    value = CredentialService.reveal_once(
        name=name,
        scope=cred_scope,
        scope_id=scope_id,
        workspace_id=LOCAL_ACTOR_ID,
        reason=request.reason,
    )

    if value is None:
        raise HTTPException(
            status_code=404,
            detail=f"Credential {name} not found",
        )

    return {"ok": True, "name": name, "value": value}


@router.delete("/credentials/{name}")
async def delete_credential(
    name: str,
    scope: str = Query(...),
    scope_id: str = Query(...),
) -> Dict[str, Any]:
    """Delete a credential."""
    try:
        cred_scope = CredentialScope(scope)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope: {scope}",
        )

    success = CredentialService.delete(
        name=name,
        scope=cred_scope,
        scope_id=scope_id,
        workspace_id=LOCAL_ACTOR_ID,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Credential {name} not found",
        )

    return {"ok": True, "deleted": name}


@router.get("/credentials/audit")
async def get_credential_audit_log(
    credential_name: Optional[str] = None,
    workspace_id: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
) -> Dict[str, Any]:
    """
    Get credential access audit log.

    For compliance and security monitoring.
    """
    records = CredentialService.get_access_log(
        credential_name=credential_name,
        workspace_id=workspace_id,
        limit=limit,
    )

    return {
        "ok": True,
        "logs": [r.to_dict() for r in records],
        "count": len(records),
    }


# ============================================================================
# Single Variable Endpoint (MUST be last to avoid catching other routes)
# ============================================================================


@router.get("/{variable_id}", response_model=VariableResponse)
async def get_variable(variable_id: str) -> Dict[str, Any]:
    """Get a variable by ID."""
    variable = VariableRepository.get(variable_id)

    if not variable:
        raise HTTPException(
            status_code=404,
            detail=f"Variable {variable_id} not found",
        )

    return variable.to_dict()
