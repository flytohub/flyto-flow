"""
Capabilities System

Dual-axis feature gate system:
- Axis A: LicenseType (business rights)
- Axis B: DeploymentMode (technical constraints)

Feature Enabled = License Gate ∩ Deployment Gate
"""

# Re-export from new capabilities module for backward compatibility
from capabilities import (
    LicenseType,
    DeploymentMode,
    Feature,
    CapabilityContext,
    init_capability_context,
    get_capability_context,
    has_capability_context,
    reset_capability_context,
    auto_init_context,
    require_feature,
    require_any_feature,
    UIConfig,
    get_page_visibility,
)

# Keep old definitions for backward compatibility
from gateway.capabilities.definitions import Capability, CLOUD_CAPABILITIES, LOCAL_CAPABILITIES, ENTERPRISE_CAPABILITIES

__all__ = [
    # New system
    "LicenseType",
    "DeploymentMode",
    "Feature",
    "CapabilityContext",
    "init_capability_context",
    "get_capability_context",
    "has_capability_context",
    "reset_capability_context",
    "auto_init_context",
    "require_feature",
    "require_any_feature",
    "UIConfig",
    "get_page_visibility",
    # Legacy (for backward compatibility)
    "Capability",
    "CLOUD_CAPABILITIES",
    "LOCAL_CAPABILITIES",
    "ENTERPRISE_CAPABILITIES",
]
