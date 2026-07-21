"""
Device Repository

Database persistence for registered runner devices.
Uses Firestore in cloud mode, SQLite in local mode.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from services.device.models import Device, DeviceStatus

logger = logging.getLogger(__name__)


def _is_cloud_mode() -> bool:
    """Check if running in cloud deployment mode."""
    from gateway.config import get_gateway_config
    return get_gateway_config().is_cloud


# =============================================================================
# Cloud Repository (Cloud Run - provider-backed)
# =============================================================================


class _CloudDeviceRepository:
    """Device persistence using the active cloud data provider."""

    @classmethod
    def _provider(cls):
        from gateway.providers.hub import get_data_provider

        return get_data_provider().devices

    @classmethod
    def create(cls, device: Device) -> Device:
        """Register or update a device through the active provider."""
        return cls._provider().create_device(device)

    @classmethod
    def get(cls, device_id: str) -> Optional[Device]:
        """Retrieve a device by ID through the active provider."""
        return cls._provider().get_device(device_id)

    @classmethod
    def list_by_user(cls, user_id: str) -> List[Device]:
        """List active devices for a user through the active provider."""
        return cls._provider().list_devices_by_user(user_id)

    @classmethod
    def list_by_workspace(cls, workspace_id: str) -> List[Device]:
        """List active devices in a workspace through the active provider."""
        return cls._provider().list_devices_by_workspace(workspace_id)

    @classmethod
    def update_heartbeat(cls, device_id: str, local_url: str | None = None) -> bool:
        """Update last_seen timestamp through the active provider."""
        return cls._provider().update_device_heartbeat(device_id, local_url=local_url)

    @classmethod
    def mark_offline(cls, device_id: str) -> bool:
        """Mark a device as offline through the active provider."""
        return cls._provider().mark_device_offline(device_id)

    @classmethod
    def increment_processed(cls, device_id: str) -> None:
        """Increment processed-event count through the active provider."""
        cls._provider().increment_device_processed(device_id)

    @classmethod
    def set_remote_wake(cls, device_id: str, enabled: bool) -> bool:
        """Enable or disable remote wake through the active provider."""
        return cls._provider().set_remote_wake(device_id, enabled)

    @classmethod
    def update_daemon_heartbeat(cls, device_id: str) -> bool:
        """Update the wake daemon's last_seen timestamp through the provider."""
        return cls._provider().update_daemon_heartbeat(device_id)

    @classmethod
    def revoke(cls, device_id: str, user_id: str) -> bool:
        """Revoke a device through the active provider."""
        return cls._provider().revoke_device(device_id, user_id)

    @classmethod
    def delete(cls, device_id: str, user_id: str) -> bool:
        """Delete a device through the active provider."""
        return cls._provider().delete_device(device_id, user_id)


# =============================================================================
# SQLite Repository (Local Runner — desktop app)
# =============================================================================

class _SqliteDeviceRepository:
    """Device persistence using SQLite."""

    _TABLE_NAME = "devices"

    @classmethod
    def _ensure_table(cls) -> None:
        """Create the devices table and indexes if they don't exist."""
        from gateway.storage.database import DatabaseManager

        DatabaseManager.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                revoked INTEGER DEFAULT 0,
                platform TEXT,
                version TEXT,
                local_url TEXT,
                last_seen TEXT,
                events_processed INTEGER DEFAULT 0,
                remote_wake_enabled INTEGER DEFAULT 0,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Migration: add remote_wake_enabled if missing (existing tables)
        try:
            DatabaseManager.execute(
                f"ALTER TABLE {cls._TABLE_NAME} ADD COLUMN remote_wake_enabled INTEGER DEFAULT 0"
            )
        except Exception:
            pass  # Column already exists
        try:
            DatabaseManager.execute(
                f"ALTER TABLE {cls._TABLE_NAME} ADD COLUMN daemon_last_seen TEXT"
            )
        except Exception:
            pass  # Column already exists
        DatabaseManager.execute(
            f"CREATE INDEX IF NOT EXISTS idx_devices_user ON {cls._TABLE_NAME}(user_id)"
        )
        DatabaseManager.execute(
            f"CREATE INDEX IF NOT EXISTS idx_devices_workspace ON {cls._TABLE_NAME}(workspace_id)"
        )

    @classmethod
    def create(cls, device: Device) -> Device:
        """Register or update a device in SQLite."""
        from gateway.storage.database import DatabaseManager
        cls._ensure_table()

        if not device.id:
            device.id = str(uuid4())

        now = datetime.now(timezone.utc).isoformat()

        DatabaseManager.execute(
            f"""
            INSERT OR REPLACE INTO {cls._TABLE_NAME}
            (id, name, workspace_id, user_id, status, revoked,
             platform, version, local_url, last_seen, events_processed,
             remote_wake_enabled, registered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                device.id, device.name, device.workspace_id, device.user_id,
                device.status.value, 1 if device.revoked else 0,
                device.platform, device.version, device.local_url, now,
                device.events_processed, 1 if device.remote_wake_enabled else 0,
                now,
            ),
        )

        device.last_seen = now
        device.registered_at = now
        logger.info(f"Device registered (SQLite): {device.id} ({device.name})")
        return device

    @classmethod
    def get(cls, device_id: str) -> Optional[Device]:
        """Retrieve a device by ID from SQLite."""
        from gateway.storage.database import DatabaseManager
        cls._ensure_table()

        rows = DatabaseManager.fetch_all(
            f"SELECT * FROM {cls._TABLE_NAME} WHERE id = ?",
            (device_id,),
        )
        if not rows:
            return None
        return cls._row_to_device(rows[0])

    @classmethod
    def list_by_user(cls, user_id: str) -> List[Device]:
        """List all active devices for a user, sorted by registration date."""
        from gateway.storage.database import DatabaseManager
        cls._ensure_table()

        rows = DatabaseManager.fetch_all(
            f"""
            SELECT * FROM {cls._TABLE_NAME}
            WHERE user_id = ? AND revoked = 0
            ORDER BY registered_at DESC
            """,
            (user_id,),
        )
        return [cls._row_to_device(row) for row in rows]

    @classmethod
    def list_by_workspace(cls, workspace_id: str) -> List[Device]:
        """List all active devices in a workspace."""
        from gateway.storage.database import DatabaseManager
        cls._ensure_table()

        rows = DatabaseManager.fetch_all(
            f"""
            SELECT * FROM {cls._TABLE_NAME}
            WHERE workspace_id = ? AND revoked = 0
            ORDER BY last_seen DESC
            """,
            (workspace_id,),
        )
        return [cls._row_to_device(row) for row in rows]

    @classmethod
    def update_heartbeat(cls, device_id: str, local_url: str | None = None) -> bool:
        """Update last_seen timestamp (and optionally local_url) for an active device."""
        from gateway.storage.database import DatabaseManager
        cls._ensure_table()
        now = datetime.now(timezone.utc).isoformat()

        if local_url is not None:
            cursor = DatabaseManager.execute(
                f"UPDATE {cls._TABLE_NAME} SET last_seen = ?, local_url = ? WHERE id = ? AND revoked = 0",
                (now, local_url, device_id),
            )
        else:
            cursor = DatabaseManager.execute(
                f"UPDATE {cls._TABLE_NAME} SET last_seen = ? WHERE id = ? AND revoked = 0",
                (now, device_id),
            )
        return cursor.rowcount > 0

    @classmethod
    def mark_offline(cls, device_id: str) -> bool:
        """Mark a device as offline by resetting its last_seen timestamp."""
        from gateway.storage.database import DatabaseManager
        cls._ensure_table()
        cursor = DatabaseManager.execute(
            f"UPDATE {cls._TABLE_NAME} SET last_seen = ? WHERE id = ? AND revoked = 0",
            ("1970-01-01T00:00:00+00:00", device_id),
        )
        return cursor.rowcount > 0

    @classmethod
    def increment_processed(cls, device_id: str) -> None:
        """Increment the events_processed counter for a device."""
        from gateway.storage.database import DatabaseManager
        cls._ensure_table()

        DatabaseManager.execute(
            f"""
            UPDATE {cls._TABLE_NAME}
            SET events_processed = events_processed + 1
            WHERE id = ?
            """,
            (device_id,),
        )

    @classmethod
    def set_remote_wake(cls, device_id: str, enabled: bool) -> bool:
        """Enable or disable remote wake for a device."""
        from gateway.storage.database import DatabaseManager
        cls._ensure_table()
        cursor = DatabaseManager.execute(
            f"UPDATE {cls._TABLE_NAME} SET remote_wake_enabled = ? WHERE id = ? AND revoked = 0",
            (1 if enabled else 0, device_id),
        )
        return cursor.rowcount > 0

    @classmethod
    def update_daemon_heartbeat(cls, device_id: str) -> bool:
        """Update the wake daemon's last_seen timestamp."""
        from gateway.storage.database import DatabaseManager
        cls._ensure_table()
        now = datetime.now(timezone.utc).isoformat()
        cursor = DatabaseManager.execute(
            f"UPDATE {cls._TABLE_NAME} SET daemon_last_seen = ? WHERE id = ? AND revoked = 0",
            (now, device_id),
        )
        return cursor.rowcount > 0

    @classmethod
    def revoke(cls, device_id: str, user_id: str) -> bool:
        """Revoke a device, verifying ownership by user_id."""
        from gateway.storage.database import DatabaseManager
        cls._ensure_table()

        cursor = DatabaseManager.execute(
            f"""
            UPDATE {cls._TABLE_NAME}
            SET revoked = 1, status = ?
            WHERE id = ? AND user_id = ?
            """,
            (DeviceStatus.REVOKED.value, device_id, user_id),
        )
        if cursor.rowcount > 0:
            logger.info(f"Device revoked: {device_id}")
            return True
        return False

    @classmethod
    def delete(cls, device_id: str, user_id: str) -> bool:
        """Delete a device from SQLite, verifying ownership."""
        from gateway.storage.database import DatabaseManager
        cls._ensure_table()

        cursor = DatabaseManager.execute(
            f"DELETE FROM {cls._TABLE_NAME} WHERE id = ? AND user_id = ?",
            (device_id, user_id),
        )
        return cursor.rowcount > 0

    @classmethod
    def _row_to_device(cls, row) -> Device:
        """Convert database row (dict) to Device object."""
        return Device(
            id=row["id"],
            name=row["name"],
            workspace_id=row["workspace_id"],
            user_id=row["user_id"],
            status=DeviceStatus(row["status"]) if row.get("status") else DeviceStatus.ACTIVE,
            revoked=bool(row.get("revoked", 0)),
            platform=row.get("platform"),
            version=row.get("version"),
            local_url=row.get("local_url"),
            last_seen=row.get("last_seen"),
            events_processed=row.get("events_processed", 0) or 0,
            remote_wake_enabled=bool(row.get("remote_wake_enabled", 0)),
            daemon_last_seen=row.get("daemon_last_seen"),
            registered_at=row.get("registered_at"),
        )


# =============================================================================
# Public facade — auto-selects backend based on deployment mode
# =============================================================================

class DeviceRepository:
    """Device repository that delegates to Firestore (cloud) or SQLite (local)."""

    @classmethod
    def _backend(cls):
        """Return the appropriate repository backend for the current mode."""
        if _is_cloud_mode():
            return _CloudDeviceRepository
        return _SqliteDeviceRepository

    @classmethod
    def create(cls, device: Device) -> Device:
        """Register or update a device."""
        return cls._backend().create(device)

    @classmethod
    def get(cls, device_id: str) -> Optional[Device]:
        """Retrieve a device by ID."""
        return cls._backend().get(device_id)

    @classmethod
    def list_by_user(cls, user_id: str) -> List[Device]:
        """List all active devices for a user."""
        return cls._backend().list_by_user(user_id)

    @classmethod
    def list_by_workspace(cls, workspace_id: str) -> List[Device]:
        """List all active devices in a workspace."""
        return cls._backend().list_by_workspace(workspace_id)

    @classmethod
    def update_heartbeat(cls, device_id: str, local_url: str | None = None) -> bool:
        """Update last_seen timestamp (and optionally local_url) for a device."""
        return cls._backend().update_heartbeat(device_id, local_url=local_url)

    @classmethod
    def mark_offline(cls, device_id: str) -> bool:
        """Mark a device as offline."""
        return cls._backend().mark_offline(device_id)

    @classmethod
    def increment_processed(cls, device_id: str) -> None:
        """Increment the events_processed counter."""
        cls._backend().increment_processed(device_id)

    @classmethod
    def set_remote_wake(cls, device_id: str, enabled: bool) -> bool:
        """Enable or disable remote wake."""
        return cls._backend().set_remote_wake(device_id, enabled)

    @classmethod
    def update_daemon_heartbeat(cls, device_id: str) -> bool:
        """Update the wake daemon's last_seen timestamp."""
        return cls._backend().update_daemon_heartbeat(device_id)

    @classmethod
    def revoke(cls, device_id: str, user_id: str) -> bool:
        """Revoke a device."""
        return cls._backend().revoke(device_id, user_id)

    @classmethod
    def delete(cls, device_id: str, user_id: str) -> bool:
        """Delete a device."""
        return cls._backend().delete(device_id, user_id)
