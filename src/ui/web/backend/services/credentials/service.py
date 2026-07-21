"""Credential Service — CRUD operations, audit logging, and orchestration."""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from gateway.storage.database import DatabaseManager
from services.credentials.models import Credential, CredentialAccess, CredentialScope, CredentialType
from services.credentials.encryption import EncryptionKey
from services.credentials.crypto import CredentialCryptoMixin
from services.credentials.tokens import CredentialTokenMixin

logger = logging.getLogger(__name__)


class CredentialService(CredentialCryptoMixin, CredentialTokenMixin):
    """
    Secure credential management service.

    Provides:
    - Encryption/decryption of secrets (via CredentialCryptoMixin)
    - Access control
    - Audit logging
    - Key rotation support
    - Execution token system (via CredentialTokenMixin)
    """

    _TABLE_NAME = "credentials"
    _AUDIT_TABLE = "credential_access_log"

    @classmethod
    def _ensure_tables(cls) -> None:
        """Ensure credential tables exist."""
        DatabaseManager.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                scope TEXT NOT NULL,
                scope_id TEXT NOT NULL,
                encrypted_value TEXT NOT NULL,
                key_version INTEGER DEFAULT 1,
                description TEXT,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at TEXT,
                access_count INTEGER DEFAULT 0
            )
            """
        )
        DatabaseManager.execute(
            f"""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_credentials_name
            ON {cls._TABLE_NAME}(scope, scope_id, name)
            """
        )
        DatabaseManager.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {cls._AUDIT_TABLE} (
                id TEXT PRIMARY KEY,
                credential_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                success INTEGER DEFAULT 1,
                reason TEXT
            )
            """
        )
        DatabaseManager.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_credential_audit_time
            ON {cls._AUDIT_TABLE}(timestamp)
            """
        )

        # Migration: add credential_type column
        try:
            DatabaseManager.execute(
                f"ALTER TABLE {cls._TABLE_NAME} ADD COLUMN credential_type TEXT DEFAULT 'generic'"
            )
        except Exception:
            pass  # Column already exists

    @classmethod
    def create(
        cls,
        name: str,
        value: str,
        scope: CredentialScope,
        scope_id: str,
        description: Optional[str] = None,
        user_id: str = "system",
        credential_type: CredentialType = CredentialType.GENERIC,
    ) -> Credential:
        """
        Create a new credential.

        Args:
            name: Credential name
            value: Secret value (will be encrypted)
            scope: Credential scope
            scope_id: Scope identifier
            description: Optional description
            user_id: Creating user
            credential_type: Type of credential

        Returns:
            Created credential (without value)
        """
        cls._ensure_tables()
        EncryptionKey.initialize()

        credential_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        key_version = EncryptionKey.get_current_version()
        encrypted = cls._encrypt(value, key_version)

        credential = Credential(
            id=credential_id,
            name=name,
            scope=scope,
            scope_id=scope_id,
            credential_type=credential_type,
            encrypted_value=encrypted,
            key_version=key_version,
            description=description,
            created_by=user_id,
            created_at=now,
            updated_at=now,
        )

        DatabaseManager.execute(
            f"""
            INSERT INTO {cls._TABLE_NAME}
            (id, name, scope, scope_id, credential_type, encrypted_value, key_version,
             description, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                credential.id,
                credential.name,
                credential.scope.value,
                credential.scope_id,
                credential.credential_type.value,
                credential.encrypted_value,
                credential.key_version,
                credential.description,
                credential.created_by,
                credential.created_at,
                credential.updated_at,
            ),
        )

        cls._audit_log(name, user_id, "create", True)
        logger.info(f"Created credential: {name}")

        return credential

    @classmethod
    def get(
        cls,
        name: str,
        scope: CredentialScope,
        scope_id: str,
        user_id: str,
        ip_address: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get decrypted credential value.

        Args:
            name: Credential name
            scope: Credential scope
            scope_id: Scope identifier
            user_id: Requesting user (for audit)
            ip_address: Client IP (for audit)

        Returns:
            Decrypted value or None
        """
        cls._ensure_tables()
        EncryptionKey.initialize()

        row = DatabaseManager.fetchone(
            f"""
            SELECT * FROM {cls._TABLE_NAME}
            WHERE name = ? AND scope = ? AND scope_id = ?
            """,
            (name, scope.value, scope_id),
        )

        if not row:
            cls._audit_log(name, user_id, "access", False, "not_found", ip_address)
            return None

        # Decrypt
        try:
            value = cls._decrypt(row["encrypted_value"], row["key_version"])
        except Exception as e:
            cls._audit_log(name, user_id, "access", False, str(e), ip_address)
            logger.error(f"Failed to decrypt credential {name}: {e}")
            return None

        # Update access tracking
        now = datetime.now(timezone.utc).isoformat()
        DatabaseManager.execute(
            f"""
            UPDATE {cls._TABLE_NAME}
            SET last_accessed_at = ?, access_count = access_count + 1
            WHERE id = ?
            """,
            (now, row["id"]),
        )

        cls._audit_log(name, user_id, "access", True, None, ip_address)
        return value

    @classmethod
    def get_masked(cls, name: str) -> str:
        """
        Get masked credential value (for UI display).

        Always returns masked string, never the actual value.
        """
        return "••••••••"

    @classmethod
    def reveal_once(
        cls,
        name: str,
        scope: CredentialScope,
        scope_id: str,
        user_id: str,
        reason: str,
        ip_address: Optional[str] = None,
    ) -> Optional[str]:
        """
        Reveal credential value with audit logging.

        Requires explicit reason for compliance.

        Args:
            name: Credential name
            scope: Credential scope
            scope_id: Scope identifier
            user_id: Requesting user
            reason: Reason for revealing
            ip_address: Client IP

        Returns:
            Decrypted value or None
        """
        value = cls.get(name, scope, scope_id, user_id, ip_address)

        if value:
            cls._audit_log(
                name, user_id, "reveal",
                True, f"Reason: {reason}", ip_address
            )

        return value

    @classmethod
    def update(
        cls,
        name: str,
        scope: CredentialScope,
        scope_id: str,
        new_value: str,
        user_id: str,
    ) -> bool:
        """
        Update credential value.

        Args:
            name: Credential name
            scope: Credential scope
            scope_id: Scope identifier
            new_value: New secret value
            user_id: Updating user

        Returns:
            True if updated
        """
        cls._ensure_tables()
        EncryptionKey.initialize()

        key_version = EncryptionKey.get_current_version()
        encrypted = cls._encrypt(new_value, key_version)
        now = datetime.now(timezone.utc).isoformat()

        result = DatabaseManager.execute(
            f"""
            UPDATE {cls._TABLE_NAME}
            SET encrypted_value = ?, key_version = ?, updated_at = ?
            WHERE name = ? AND scope = ? AND scope_id = ?
            """,
            (encrypted, key_version, now, name, scope.value, scope_id),
        )

        success = result.rowcount > 0
        cls._audit_log(name, user_id, "update", success)

        if success:
            logger.info(f"Updated credential: {name}")

        return success

    @classmethod
    def delete(
        cls,
        name: str,
        scope: CredentialScope,
        scope_id: str,
        user_id: str,
    ) -> bool:
        """
        Delete a credential.

        Args:
            name: Credential name
            scope: Credential scope
            scope_id: Scope identifier
            user_id: Deleting user

        Returns:
            True if deleted
        """
        cls._ensure_tables()

        result = DatabaseManager.execute(
            f"""
            DELETE FROM {cls._TABLE_NAME}
            WHERE name = ? AND scope = ? AND scope_id = ?
            """,
            (name, scope.value, scope_id),
        )

        success = result.rowcount > 0
        cls._audit_log(name, user_id, "delete", success)

        if success:
            logger.info(f"Deleted credential: {name}")

        return success

    @classmethod
    def list_credentials(
        cls,
        scope: CredentialScope,
        scope_id: str,
    ) -> List[Credential]:
        """
        List credentials (metadata only, no values).

        Args:
            scope: Credential scope
            scope_id: Scope identifier

        Returns:
            List of credentials without values
        """
        cls._ensure_tables()

        rows = DatabaseManager.fetchall(
            f"""
            SELECT id, name, scope, scope_id, credential_type, key_version, description,
                   created_by, created_at, updated_at, last_accessed_at, access_count
            FROM {cls._TABLE_NAME}
            WHERE scope = ? AND scope_id = ?
            ORDER BY name
            """,
            (scope.value, scope_id),
        )

        return [
            Credential(
                id=row["id"],
                name=row["name"],
                scope=CredentialScope(row["scope"]),
                scope_id=row["scope_id"],
                credential_type=CredentialType(row.get("credential_type", "generic")),
                encrypted_value="",  # Never expose
                key_version=row["key_version"],
                description=row.get("description"),
                created_by=row.get("created_by", ""),
                created_at=row.get("created_at", ""),
                updated_at=row.get("updated_at", ""),
                last_accessed_at=row.get("last_accessed_at"),
                access_count=row.get("access_count", 0),
            )
            for row in rows
        ]

    @classmethod
    def rotate_encryption_key(cls, new_master_key: str) -> int:
        """
        Rotate encryption key and re-encrypt all credentials.

        Args:
            new_master_key: New master key

        Returns:
            New key version
        """
        cls._ensure_tables()
        EncryptionKey.initialize()

        old_version = EncryptionKey.get_current_version()
        new_version = EncryptionKey.rotate_key(new_master_key)

        # Re-encrypt all credentials
        rows = DatabaseManager.fetchall(
            f"SELECT id, encrypted_value, key_version FROM {cls._TABLE_NAME}"
        )

        for row in rows:
            try:
                # Decrypt with old key
                value = cls._decrypt(row["encrypted_value"], row["key_version"])
                # Encrypt with new key
                encrypted = cls._encrypt(value, new_version)

                DatabaseManager.execute(
                    f"""
                    UPDATE {cls._TABLE_NAME}
                    SET encrypted_value = ?, key_version = ?
                    WHERE id = ?
                    """,
                    (encrypted, new_version, row["id"]),
                )
            except Exception as e:
                logger.error(f"Failed to re-encrypt credential {row['id']}: {e}")

        logger.info(f"Rotated encryption key from v{old_version} to v{new_version}")
        return new_version

    @classmethod
    def _audit_log(
        cls,
        credential_name: str,
        user_id: str,
        action: str,
        success: bool,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Record credential access in audit log."""
        try:
            DatabaseManager.execute(
                f"""
                INSERT INTO {cls._AUDIT_TABLE}
                (id, credential_name, user_id, action, timestamp, ip_address, success, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    credential_name,
                    user_id,
                    action,
                    datetime.now(timezone.utc).isoformat(),
                    ip_address,
                    1 if success else 0,
                    reason,
                ),
            )
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    @classmethod
    def get_access_log(
        cls,
        credential_name: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[CredentialAccess]:
        """
        Get credential access audit log.

        Args:
            credential_name: Filter by credential name
            user_id: Filter by user
            limit: Maximum records

        Returns:
            List of access records
        """
        cls._ensure_tables()

        conditions = []
        params = []

        if credential_name:
            conditions.append("credential_name = ?")
            params.append(credential_name)

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        rows = DatabaseManager.fetchall(
            f"""
            SELECT * FROM {cls._AUDIT_TABLE}
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            tuple(params),
        )

        return [
            CredentialAccess(
                id=row["id"],
                credential_name=row["credential_name"],
                user_id=row["user_id"],
                action=row["action"],
                timestamp=row["timestamp"],
                ip_address=row.get("ip_address"),
                success=bool(row.get("success", 1)),
                reason=row.get("reason"),
            )
            for row in rows
        ]
