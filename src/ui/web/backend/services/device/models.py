"""
Device Models

Data classes for runner device registration and management.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class DeviceStatus(str, Enum):
    """Device registration status."""

    ACTIVE = "active"
    REVOKED = "revoked"


@dataclass
class Device:
    """
    Registered runner device.

    Devices are registered by users to claim and process trigger inbox events.
    Each device has a unique ID and belongs to a workspace.
    """

    id: str
    name: str
    workspace_id: str
    user_id: str

    # Status
    status: DeviceStatus = DeviceStatus.ACTIVE
    revoked: bool = False

    # Platform info
    platform: Optional[str] = None  # darwin, win32, linux
    version: Optional[str] = None  # App version

    # Network info
    local_url: Optional[str] = None  # e.g. http://192.168.1.5:9000

    # Activity tracking
    last_seen: Optional[str] = None
    events_processed: int = 0

    # Remote wake
    remote_wake_enabled: bool = False
    daemon_last_seen: Optional[str] = None  # Wake daemon heartbeat timestamp

    # Timestamps
    registered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def is_online(self, timeout_seconds: int = 90) -> bool:
        """Check if device is online (seen within timeout)."""
        if not self.last_seen:
            return False

        try:
            last_seen_dt = datetime.fromisoformat(self.last_seen.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (now - last_seen_dt).total_seconds() < timeout_seconds
        except (ValueError, TypeError):
            return False

    def is_daemon_online(self, timeout_seconds: int = 360) -> bool:
        """Check if wake daemon is alive (reported heartbeat within timeout)."""
        if not self.daemon_last_seen:
            return False
        try:
            dt = datetime.fromisoformat(self.daemon_last_seen.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (now - dt).total_seconds() < timeout_seconds
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "revoked": self.revoked,
            "platform": self.platform,
            "version": self.version,
            "local_url": self.local_url,
            "last_seen": self.last_seen,
            "events_processed": self.events_processed,
            "remote_wake_enabled": self.remote_wake_enabled,
            "daemon_last_seen": self.daemon_last_seen,
            "registered_at": self.registered_at,
            "is_online": self.is_online(),
            "daemon_online": self.is_daemon_online(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Device":
        """Create Device from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            workspace_id=data.get("workspace_id", ""),
            user_id=data.get("user_id", ""),
            status=DeviceStatus(data.get("status", "active")),
            revoked=data.get("revoked", False),
            platform=data.get("platform"),
            version=data.get("version"),
            local_url=data.get("local_url"),
            last_seen=data.get("last_seen"),
            events_processed=data.get("events_processed", 0),
            remote_wake_enabled=data.get("remote_wake_enabled", False),
            daemon_last_seen=data.get("daemon_last_seen"),
            registered_at=data.get("registered_at", ""),
        )
