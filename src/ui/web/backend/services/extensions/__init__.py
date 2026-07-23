"""Signed connector, plugin, and template-pack manifests."""

from services.extensions.manifest import (
    ExtensionManifest,
    ExtensionPolicy,
    discover_extensions,
    load_extension_manifest,
)
from services.extensions.runtime import (
    configured_extension_root,
    configured_plugin_root,
    verify_configured_extensions,
)
from services.extensions.templates import load_template_packs

__all__ = [
    "ExtensionManifest",
    "ExtensionPolicy",
    "discover_extensions",
    "load_extension_manifest",
    "configured_extension_root",
    "configured_plugin_root",
    "verify_configured_extensions",
    "load_template_packs",
]
