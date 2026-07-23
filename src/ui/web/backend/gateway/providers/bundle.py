"""Composition contract for private self-hosted and hosted provider bundles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gateway.providers.identity.contracts import IdentityProvider, ProvisioningProvider
from gateway.providers.loading import load_provider_factory
from gateway.storage.queue_interface import QueueInterface
from services.credentials.backends import KeyManagementBackend


@dataclass(frozen=True)
class ProviderBundle:
    access: Any
    audit: Any
    data: Any
    identity: IdentityProvider
    provisioning: ProvisioningProvider
    queue: QueueInterface
    secrets: KeyManagementBackend


def load_provider_bundle(spec: str) -> ProviderBundle:
    """Load one explicitly allowlisted ``module:factory`` provider bundle."""
    factory = load_provider_factory(
        spec,
        setting_name="FLYTO_PROVIDER_BUNDLE",
    )
    bundle = factory()
    if not isinstance(bundle, ProviderBundle):
        raise TypeError("Provider bundle factory must return ProviderBundle")
    if not isinstance(bundle.identity, IdentityProvider):
        raise TypeError("Provider bundle identity adapter is incomplete")
    if not isinstance(bundle.provisioning, ProvisioningProvider):
        raise TypeError("Provider bundle provisioning adapter is incomplete")
    if not isinstance(bundle.queue, QueueInterface):
        raise TypeError("Provider bundle queue adapter is incomplete")
    if not isinstance(bundle.secrets, KeyManagementBackend):
        raise TypeError("Provider bundle secret adapter is incomplete")
    for adapter_name, methods in {
        "access": ("check_permission",),
        "audit": ("log",),
    }.items():
        adapter = getattr(bundle, adapter_name)
        missing = [method for method in methods if not callable(getattr(adapter, method, None))]
        if missing:
            raise TypeError(
                f"Provider bundle {adapter_name} adapter is incomplete"
            )
    if bundle.data is None:
        raise TypeError("Provider bundle data adapter is incomplete")
    bundle.secrets.validate_configuration()
    return bundle
