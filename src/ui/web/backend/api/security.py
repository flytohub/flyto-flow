"""
Security API

Provides security validation endpoints for step execution.
All security-critical logic is server-side to prevent client-side bypass.

Endpoints:
- GET /api/security/step-gate-config - Get permission mappings (for UI hints only)
- POST /api/security/validate-step - Authoritative step validation
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from gateway.auth import get_optional_user
from gateway.providers.base import UserInfo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/security", tags=["Security"])


# =============================================================================
# Security Configuration (Server-side only, authoritative source)
# =============================================================================

class CapabilityToken:
    """Capability tokens define permission levels for tool execution"""
    READ_ONLY = "cap_read_only"
    READ_WRITE_LOCAL = "cap_read_write_local_only"
    RUN_TESTS = "cap_run_tests"
    NETWORK_LIMITED = "cap_network_limited"
    DANGEROUS = "cap_dangerous"


# Permission sets for each capability token
CAPABILITY_PERMISSIONS: Dict[str, Set[str]] = {
    CapabilityToken.READ_ONLY: {
        "file.read",
        "file.list",
        "code.search",
        "project.tree",
        "project.route_map",
    },
    CapabilityToken.READ_WRITE_LOCAL: {
        "file.read",
        "file.write",
        "file.create",
        "file.delete",
        "code.search",
        "code.patch",
        "project.tree",
    },
    CapabilityToken.RUN_TESTS: {
        "test.unit.run",
        "test.e2e.run",
        "test.integration.run",
        "shell.exec:npm test",
        "shell.exec:pytest",
        "shell.exec:playwright",
    },
    CapabilityToken.NETWORK_LIMITED: {
        "http.get",
        "http.post",
        "api.call",
    },
    CapabilityToken.DANGEROUS: {
        "shell.exec",
        "deploy.run",
        "payment.process",
        "email.send",
    },
}

# Dangerous operation patterns (regex)
DANGEROUS_PATTERNS: List[str] = [
    r"rm\s+-rf",
    r"sudo",
    r"chmod\s+[0-7]{3,4}",
    r"chown",
    r"deploy",
    r"prod(?:uction)?",
    r"payment",
    r"delete.*(?:all|database|table)",
    r"drop\s+(?:table|database)",
    r"truncate",
]

# Compiled patterns for efficiency
_COMPILED_DANGEROUS_PATTERNS = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]

# Safe shell command patterns (whitelist)
SAFE_SHELL_COMMANDS: List[str] = [
    r"^npm\s+(?:test|run\s+test|run\s+lint)",
    r"^pytest",
    r"^jest",
    r"^playwright\s+test",
    r"^ls\b",
    r"^cat\b",
    r"^pwd\b",
    r"^echo\b",
    r"^git\s+(?:status|log|diff|branch)",
]

# Compiled safe patterns
_COMPILED_SAFE_PATTERNS = [re.compile(p) for p in SAFE_SHELL_COMMANDS]


# =============================================================================
# Request/Response Models
# =============================================================================

class ToolRequest(BaseModel):
    """A tool request to validate"""
    name: str = Field(..., description="Tool name (e.g., file.read, shell.exec)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class ValidateStepRequest(BaseModel):
    """Request to validate tool requests against capability token"""
    tools: List[ToolRequest] = Field(..., description="Tool requests to validate")
    capability: str = Field(..., description="Capability token")


class ValidateStepResponse(BaseModel):
    """Validation result"""
    ok: bool = Field(..., description="Whether the request is valid")
    allowed: bool = Field(..., description="Whether the operation is allowed")
    reason: Optional[str] = Field(default=None, description="Reason if not allowed")
    requires_confirmation: bool = Field(default=False, description="Whether user confirmation is required")
    blocked_tools: List[str] = Field(default_factory=list, description="List of blocked tool names")


class CapabilityInfo(BaseModel):
    """Information about a capability token"""
    name: str
    description: str
    risk_level: str  # low, medium, high


class StepGateConfigResponse(BaseModel):
    """Step gate configuration response"""
    ok: bool = True
    permissions: Dict[str, List[str]] = Field(..., description="Capability -> operations mapping")
    capabilities: Dict[str, CapabilityInfo] = Field(..., description="Capability info for UI")


# =============================================================================
# Helper Functions
# =============================================================================

def _is_tool_allowed(tool_name: str, allowed_ops: Set[str]) -> bool:
    """
    Check if a tool is allowed under given permissions.

    Args:
        tool_name: Tool name to check
        allowed_ops: Set of allowed operations

    Returns:
        True if allowed, False otherwise
    """
    # Exact match
    if tool_name in allowed_ops:
        return True

    # Prefix match (e.g., 'file.' matches 'file.read')
    for op in allowed_ops:
        if op.endswith(".") and tool_name.startswith(op):
            return True
        # Command-specific match (e.g., 'shell.exec:npm test')
        if tool_name.startswith(op.split(":")[0]) and ":" in op:
            return True

    return False


def _is_dangerous(tool: ToolRequest) -> bool:
    """
    Check if a tool request contains dangerous operations.

    Args:
        tool: Tool request to check

    Returns:
        True if dangerous, False otherwise
    """
    import json
    params_str = json.dumps(tool.params)

    # Check against dangerous patterns
    for pattern in _COMPILED_DANGEROUS_PATTERNS:
        if pattern.search(params_str):
            return True

    # Special handling for shell commands
    if tool.name == "shell.exec" or tool.name.startswith("shell."):
        command = tool.params.get("command") or tool.params.get("cmd", "")
        return not _is_safe_shell_command(command)

    return False


def _is_safe_shell_command(command: str) -> bool:
    """
    Check if a shell command is in the safe whitelist.

    Args:
        command: Shell command to check

    Returns:
        True if safe, False otherwise
    """
    return any(pattern.search(command) for pattern in _COMPILED_SAFE_PATTERNS)


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/step-gate-config", response_model=StepGateConfigResponse)
async def get_step_gate_config(
    user: Optional[UserInfo] = Depends(get_optional_user)
) -> StepGateConfigResponse:
    """
    Get step gate configuration.

    Returns permission mappings for UI hints only.
    Actual validation must use POST /validate-step.

    Note: This is for UI display purposes. Frontend should NOT use
    this for security decisions - always call /validate-step for
    authoritative validation.
    """
    # Convert sets to lists for JSON serialization
    permissions = {k: list(v) for k, v in CAPABILITY_PERMISSIONS.items()}

    capabilities = {
        CapabilityToken.READ_ONLY: CapabilityInfo(
            name="Read Only",
            description="Can only read files and search code",
            risk_level="low",
        ),
        CapabilityToken.READ_WRITE_LOCAL: CapabilityInfo(
            name="Local Read/Write",
            description="Can modify local files and code",
            risk_level="medium",
        ),
        CapabilityToken.RUN_TESTS: CapabilityInfo(
            name="Test Execution",
            description="Can run tests (npm test, pytest, etc.)",
            risk_level="medium",
        ),
        CapabilityToken.NETWORK_LIMITED: CapabilityInfo(
            name="Limited Network",
            description="Can make HTTP requests to whitelisted domains",
            risk_level="medium",
        ),
        CapabilityToken.DANGEROUS: CapabilityInfo(
            name="Dangerous Operations",
            description="Can perform dangerous operations with user confirmation",
            risk_level="high",
        ),
    }

    return StepGateConfigResponse(
        ok=True,
        permissions=permissions,
        capabilities=capabilities,
    )


@router.post("/validate-step", response_model=ValidateStepResponse)
async def validate_step(
    request: ValidateStepRequest,
    user: Optional[UserInfo] = Depends(get_optional_user)
) -> ValidateStepResponse:
    """
    Validate tool requests against capability token.

    This is the AUTHORITATIVE security check. All tool execution
    must pass this validation before proceeding.

    Args:
        request: Tools to validate and capability token

    Returns:
        Validation result with allowed/blocked tools
    """
    allowed_ops = CAPABILITY_PERMISSIONS.get(request.capability, set())
    blocked_tools: List[str] = []
    requires_confirmation = False

    for tool in request.tools:
        tool_name = tool.name

        # Check if tool is in allowed list
        if not _is_tool_allowed(tool_name, allowed_ops):
            blocked_tools.append(tool_name)
            continue

        # Check for dangerous patterns
        if _is_dangerous(tool):
            if request.capability != CapabilityToken.DANGEROUS:
                blocked_tools.append(f"{tool_name} (dangerous)")
            else:
                requires_confirmation = True

    if blocked_tools:
        return ValidateStepResponse(
            ok=True,
            allowed=False,
            reason=f"The following tools exceed permission scope: {', '.join(blocked_tools)}",
            requires_confirmation=False,
            blocked_tools=blocked_tools,
        )

    return ValidateStepResponse(
        ok=True,
        allowed=True,
        requires_confirmation=requires_confirmation,
        blocked_tools=[],
    )


@router.post("/validate-shell-command")
async def validate_shell_command(
    command: str,
    capability: str,
    user: Optional[UserInfo] = Depends(get_optional_user)
) -> Dict[str, Any]:
    """
    Validate a shell command specifically.

    Convenience endpoint for shell command validation.

    Args:
        command: Shell command to validate
        capability: Capability token

    Returns:
        Validation result
    """
    tool = ToolRequest(name="shell.exec", params={"command": command})
    request = ValidateStepRequest(tools=[tool], capability=capability)
    result = await validate_step(request, user)

    return {
        "ok": True,
        "allowed": result.allowed,
        "is_safe": _is_safe_shell_command(command),
        "requires_confirmation": result.requires_confirmation,
        "reason": result.reason,
    }
