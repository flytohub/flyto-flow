"""
Enterprise Gateway Module

Provides abstraction layer for Cloud (Firebase) and Enterprise (On-prem) deployments.

Key components:
- providers: Pluggable authentication, identity, access control, audit providers
- capabilities: Dual-axis feature gate system (License × Deployment)
- routing: Conditional route mounting and feature-based gating
"""

from gateway.config import get_gateway_config, GatewayConfig

# Re-export from new capabilities module
from capabilities import (
    LicenseType,
    DeploymentMode,
    Feature,
    get_capability_context,
    has_capability_context,
    auto_init_context,
    require_feature,
)

# Legacy exports for backward compatibility
from gateway.capabilities.definitions import Capability

__all__ = [
    "get_gateway_config",
    "GatewayConfig",
    # New system
    "LicenseType",
    "DeploymentMode",
    "Feature",
    "get_capability_context",
    "has_capability_context",
    "auto_init_context",
    "require_feature",
    # Legacy
    "Capability",
]
