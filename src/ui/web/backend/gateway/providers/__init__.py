"""
Gateway Providers

Pluggable provider abstractions for different backend implementations.

Provider Types:
- AuthProvider: Authentication (Firebase, LDAP, SAML)
- IdentityProvider: User data storage (Firestore, PostgreSQL)
- AccessControlProvider: Authorization (Simple roles, RBAC)
- AuditProvider: Audit logging (NoOp, Full)
- MarketplaceProvider: Marketplace features (Cloud-only)
"""

from gateway.providers.base import (
    UserInfo,
    AuthResult,
    AuthProvider,
    IdentityProvider,
    AccessControlProvider,
    AuditProvider,
    MarketplaceProvider,
)
from gateway.providers.hub import (
    ProviderHub,
    get_provider_hub,
    get_auth_provider,
    get_access_provider,
    get_audit_provider,
    reset_provider_hub,
)

__all__ = [
    # Base classes
    "UserInfo",
    "AuthResult",
    "AuthProvider",
    "IdentityProvider",
    "AccessControlProvider",
    "AuditProvider",
    "MarketplaceProvider",
    # Hub
    "ProviderHub",
    "get_provider_hub",
    "get_auth_provider",
    "get_access_provider",
    "get_audit_provider",
    "reset_provider_hub",
]
