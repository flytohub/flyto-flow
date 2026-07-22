"""Credential Models"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class CredentialScope(str, Enum):
    """Credential scope levels."""

    WORKSPACE = "workspace"
    PROJECT = "project"
    WORKFLOW = "workflow"


class CredentialType(str, Enum):
    """Credential type for structured input."""

    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    GENERIC = "generic"


@dataclass
class CredentialAccess:
    """Record of credential access."""

    id: str
    credential_name: str
    workspace_id: str
    action: str  # access, reveal, update, delete
    timestamp: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert access record to dict."""
        return {
            "id": self.id,
            "credential_name": self.credential_name,
            "workspace_id": self.workspace_id,
            "action": self.action,
            "timestamp": self.timestamp,
            "ip_address": self.ip_address,
            "success": self.success,
            "reason": self.reason,
        }


@dataclass
class Credential:
    """
    Secure credential definition.

    Credentials are always stored encrypted and require explicit access.
    """

    id: str
    name: str
    scope: CredentialScope
    scope_id: str

    # Encrypted storage
    encrypted_value: str

    # Type
    credential_type: CredentialType = CredentialType.GENERIC
    key_version: int = 1

    # Metadata
    description: Optional[str] = None
    created_by: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_accessed_at: Optional[str] = None
    access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict (never includes value)."""
        return {
            "id": self.id,
            "name": self.name,
            "scope": self.scope.value if isinstance(self.scope, CredentialScope) else self.scope,
            "scope_id": self.scope_id,
            "credential_type": self.credential_type.value if isinstance(self.credential_type, CredentialType) else self.credential_type,
            "key_version": self.key_version,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_accessed_at": self.last_accessed_at,
            "access_count": self.access_count,
        }


@dataclass
class SecretRef:
    """
    Reference to a credential (for use in workflow parameters).

    Instead of storing raw secrets in workflow configs,
    modules can reference credentials using SecretRef.
    The actual value is resolved at execution time via tokens.
    """

    type: str = "secretRef"  # Always "secretRef"
    credential_name: str = ""
    scope: str = "workflow"  # workspace, project, workflow
    scope_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert secret reference to dict."""
        return {
            "type": self.type,
            "credential_name": self.credential_name,
            "scope": self.scope,
            "scope_id": self.scope_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional["SecretRef"]:
        """Parse SecretRef from dict, or return None if not a secret ref."""
        if not isinstance(data, dict):
            return None
        if data.get("type") != "secretRef":
            return None
        return cls(
            credential_name=data.get("credential_name", ""),
            scope=data.get("scope", "workflow"),
            scope_id=data.get("scope_id", ""),
        )

    @classmethod
    def is_secret_ref(cls, value: Any) -> bool:
        """Check if a value is a SecretRef."""
        return isinstance(value, dict) and value.get("type") == "secretRef"


def extract_secret_refs(params: Dict[str, Any], scope_id: str = "") -> list:
    """
    Extract all SecretRef instances from a params dict (recursive).

    Args:
        params: Parameters dict to search
        scope_id: Default scope_id to use

    Returns:
        List of dicts with name, scope, scope_id
    """
    refs = []

    def _extract(obj: Any):
        if isinstance(obj, dict):
            if SecretRef.is_secret_ref(obj):
                refs.append({
                    "name": obj.get("credential_name", ""),
                    "scope": obj.get("scope", "workflow"),
                    "scope_id": obj.get("scope_id", scope_id),
                })
            else:
                for v in obj.values():
                    _extract(v)
        elif isinstance(obj, list):
            for item in obj:
                _extract(item)

    _extract(params)
    return refs
