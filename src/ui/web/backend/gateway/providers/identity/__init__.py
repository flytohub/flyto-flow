"""Edition-neutral identity and provisioning provider contracts."""

from gateway.providers.identity.contracts import (
    IdentityProvider,
    PrincipalContext,
    ProvisioningProvider,
    SCIMGroup,
    SCIMPrincipal,
    SSOConfiguration,
    SSOProtocol,
)

__all__ = [
    "IdentityProvider",
    "PrincipalContext",
    "ProvisioningProvider",
    "SCIMGroup",
    "SCIMPrincipal",
    "SSOConfiguration",
    "SSOProtocol",
]
