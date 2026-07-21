"""
Device Service

Business logic for runner device management.
"""

import logging
from typing import Dict, List, Optional
from uuid import uuid4

from services.device.models import Device, DeviceStatus
from services.device.repository import DeviceRepository

logger = logging.getLogger(__name__)


class DeviceService:
    """Service for managing runner devices."""

    @classmethod
    def register(
        cls,
        name: str,
        workspace_id: str,
        user_id: str,
        platform: Optional[str] = None,
        version: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> Device:
        """
        Register a new device.

        Args:
            name: Human-readable device name
            workspace_id: Workspace the device belongs to
            user_id: User who owns the device
            platform: OS platform (darwin, win32, linux)
            version: App version
            device_id: Optional specific device ID (for re-registration)

        Returns:
            Registered device
        """
        device = Device(
            id=device_id or str(uuid4()),
            name=name,
            workspace_id=workspace_id,
            user_id=user_id,
            platform=platform,
            version=version,
        )

        return DeviceRepository.create(device)

    @classmethod
    def get(cls, device_id: str) -> Optional[Device]:
        """Get device by ID."""
        return DeviceRepository.get(device_id)

    @classmethod
    def get_for_user(cls, device_id: str, user_id: str) -> Optional[Device]:
        """Get device by ID if owned by user."""
        device = DeviceRepository.get(device_id)
        if device and device.user_id == user_id and not device.revoked:
            return device
        return None

    @classmethod
    def list_by_user(cls, user_id: str) -> List[Device]:
        """List all devices for a user."""
        return DeviceRepository.list_by_user(user_id)

    @classmethod
    def list_by_workspace(cls, workspace_id: str) -> List[Device]:
        """List all devices in a workspace."""
        return DeviceRepository.list_by_workspace(workspace_id)

    @classmethod
    def heartbeat(cls, device_id: str, user_id: str, local_url: Optional[str] = None) -> bool:
        """
        Update device heartbeat.

        Args:
            device_id: Device ID
            user_id: User ID (for ownership validation)
            local_url: Optional local network URL (e.g. http://192.168.1.5:9000)

        Returns:
            True if heartbeat was recorded
        """
        device = DeviceRepository.get(device_id)
        if not device or device.user_id != user_id or device.revoked:
            return False

        return DeviceRepository.update_heartbeat(device_id, local_url=local_url)

    @classmethod
    def revoke(cls, device_id: str, user_id: str) -> bool:
        """
        Revoke a device (soft delete).

        Args:
            device_id: Device to revoke
            user_id: User ID (for ownership validation)

        Returns:
            True if device was revoked
        """
        return DeviceRepository.revoke(device_id, user_id)

    @classmethod
    def unregister(cls, device_id: str, user_id: str) -> bool:
        """
        Unregister (delete) a device.

        Args:
            device_id: Device to unregister
            user_id: User ID (for ownership validation)

        Returns:
            True if device was unregistered
        """
        return DeviceRepository.delete(device_id, user_id)

    @classmethod
    def is_valid_device(
        cls, device_id: str, workspace_id: str, user_id: str
    ) -> bool:
        """
        Check if device is valid for claiming events.

        Args:
            device_id: Device ID
            workspace_id: Expected workspace
            user_id: Expected user

        Returns:
            True if device is valid and active
        """
        device = DeviceRepository.get(device_id)
        if not device:
            return False

        return (
            device.workspace_id == workspace_id
            and device.user_id == user_id
            and device.status == DeviceStatus.ACTIVE
            and not device.revoked
        )

    @classmethod
    def get_stats(cls, user_id: str) -> Dict:
        """
        Get device statistics for a user.

        Returns:
            Dict with device counts and stats
        """
        devices = DeviceRepository.list_by_user(user_id)

        total = len(devices)
        online = sum(1 for d in devices if d.is_online())
        total_processed = sum(d.events_processed for d in devices)

        return {
            "total_devices": total,
            "online_devices": online,
            "offline_devices": total - online,
            "total_events_processed": total_processed,
        }

    @classmethod
    def mark_offline(cls, device_id: str, user_id: str) -> bool:
        """Mark device as offline by setting last_seen to epoch."""
        device = DeviceRepository.get(device_id)
        if not device or device.user_id != user_id or device.revoked:
            return False
        return DeviceRepository.mark_offline(device_id)

    @classmethod
    def increment_processed(cls, device_id: str) -> None:
        """Increment the events_processed counter for a device."""
        DeviceRepository.increment_processed(device_id)

    @classmethod
    def set_remote_wake(cls, device_id: str, user_id: str, enabled: bool) -> bool:
        """Enable or disable remote wake for a device."""
        device = DeviceRepository.get(device_id)
        if not device or device.user_id != user_id or device.revoked:
            return False
        return DeviceRepository.set_remote_wake(device_id, enabled)

    @classmethod
    def daemon_heartbeat(cls, device_id: str, user_id: str) -> bool:
        """Record wake daemon heartbeat for a device."""
        device = DeviceRepository.get(device_id)
        if not device or device.user_id != user_id or device.revoked:
            return False
        return DeviceRepository.update_daemon_heartbeat(device_id)
