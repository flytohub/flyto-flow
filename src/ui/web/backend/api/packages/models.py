"""
Pydantic models for the Package Manager API.
"""

from typing import Optional

from pydantic import BaseModel


class PackageStatus(BaseModel):
    """Status information for a system package including version and update state."""
    id: str
    name: str
    description: str
    icon: str
    color: str
    category: str
    removable: bool
    installed: bool
    installed_version: Optional[str] = None
    latest_version: Optional[str] = None
    update_available: bool = False
    auto_update: bool = False
    last_check: Optional[str] = None


class PackageActionResult(BaseModel):
    """Result of a package install, update, or remove operation."""
    ok: bool
    message: str
    package_id: str
    from_version: Optional[str] = None
    to_version: Optional[str] = None


class AutoUpdateRequest(BaseModel):
    """Request body for toggling auto-update on a package."""
    enabled: bool
