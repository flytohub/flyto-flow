"""Execution token system for credential separation."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import uuid4

from gateway.storage.database import DatabaseManager
from services.credentials.encryption import EncryptionKey
from services.credentials.models import CredentialScope

logger = logging.getLogger(__name__)


class CredentialTokenMixin:
    """Mixin providing execution token management for credentials.

    Requires the host class to define:
        _TABLE_NAME: str
        _encrypt(value, key_version) -> str
        _decrypt(encrypted, key_version) -> str
        _audit_log(name, workspace_id, action, success, reason=None, ip=None)
        _ensure_tables()
    """

    _TOKEN_TABLE = "credential_tokens"
    _TOKEN_EXPIRY_SECONDS = 3600  # 1 hour default

    @classmethod
    def _ensure_token_table(cls) -> None:
        """Ensure token table exists."""
        DatabaseManager.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {cls._TOKEN_TABLE} (
                token TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                credential_id TEXT NOT NULL,
                credential_name TEXT NOT NULL,
                scope TEXT NOT NULL,
                scope_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                used_at TEXT,
                FOREIGN KEY (credential_id) REFERENCES {cls._TABLE_NAME}(id) ON DELETE CASCADE
            )
            """
        )
        DatabaseManager.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_tokens_execution_id
            ON {cls._TOKEN_TABLE}(execution_id)
            """
        )
        DatabaseManager.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_tokens_expires_at
            ON {cls._TOKEN_TABLE}(expires_at)
            """
        )

    @classmethod
    def create_execution_token(
        cls,
        execution_id: str,
        credential_name: str,
        scope: CredentialScope,
        scope_id: str,
        workspace_id: str,
        expiry_seconds: Optional[int] = None,
    ) -> Optional[str]:
        """
        Create a temporary token for accessing a credential during execution.

        The token can only be resolved within the same execution context.
        Tokens expire after the specified duration and can only be used once.

        Args:
            execution_id: Workflow execution ID
            credential_name: Name of the credential
            scope: Credential scope
            scope_id: Scope identifier
            workspace_id: Workspace ID for audit
            expiry_seconds: Token lifetime (default: 1 hour)

        Returns:
            Token string or None if credential not found
        """
        cls._ensure_tables()
        cls._ensure_token_table()

        # Verify credential exists
        row = DatabaseManager.fetchone(
            f"""
            SELECT id FROM {cls._TABLE_NAME}
            WHERE name = ? AND scope = ? AND scope_id = ?
            """,
            (credential_name, scope.value, scope_id),
        )

        if not row:
            logger.warning(f"Credential not found for token: {credential_name}")
            return None

        credential_id = row["id"]

        # Generate secure token
        token = f"flyto_cred_{secrets.token_urlsafe(32)}"
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(seconds=expiry_seconds or cls._TOKEN_EXPIRY_SECONDS)

        DatabaseManager.execute(
            f"""
            INSERT INTO {cls._TOKEN_TABLE}
            (token, execution_id, credential_id, credential_name, scope, scope_id, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                token,
                execution_id,
                credential_id,
                credential_name,
                scope.value,
                scope_id,
                now.isoformat(),
                expiry.isoformat(),
            ),
        )

        cls._audit_log(credential_name, workspace_id, "create_token", True, f"execution:{execution_id}")
        logger.debug(f"Created execution token for {credential_name} in {execution_id}")

        return token

    @classmethod
    def resolve_execution_token(
        cls,
        token: str,
        execution_id: str,
        single_use: bool = True,
    ) -> Optional[str]:
        """
        Resolve an execution token to the actual credential value.

        Args:
            token: The token string
            execution_id: Execution ID (must match token's execution)
            single_use: If True, token is marked as used after resolution

        Returns:
            Decrypted credential value or None
        """
        cls._ensure_tables()
        cls._ensure_token_table()
        EncryptionKey.initialize()

        now = datetime.now(timezone.utc)

        # Get token and validate
        row = DatabaseManager.fetchone(
            f"""
            SELECT t.*, c.encrypted_value, c.key_version
            FROM {cls._TOKEN_TABLE} t
            JOIN {cls._TABLE_NAME} c ON t.credential_id = c.id
            WHERE t.token = ? AND t.execution_id = ?
            """,
            (token, execution_id),
        )

        if not row:
            logger.warning("Token not found or execution mismatch")
            return None

        # Check expiration
        expires_at = datetime.fromisoformat(row["expires_at"].replace('Z', '+00:00'))
        if now > expires_at:
            logger.warning(f"Token expired for {row['credential_name']}")
            cls._audit_log(row["credential_name"], "system", "resolve_token", False, "expired")
            return None

        # Check if already used (for single-use tokens)
        if single_use and row["used"]:
            logger.warning(f"Token already used for {row['credential_name']}")
            cls._audit_log(row["credential_name"], "system", "resolve_token", False, "already_used")
            return None

        # Decrypt credential
        try:
            value = cls._decrypt(row["encrypted_value"], row["key_version"])
        except Exception as e:
            logger.error(f"Failed to decrypt credential via token: {e}")
            cls._audit_log(row["credential_name"], "system", "resolve_token", False, str(e))
            return None

        # Mark as used
        if single_use:
            DatabaseManager.execute(
                f"""
                UPDATE {cls._TOKEN_TABLE}
                SET used = 1, used_at = ?
                WHERE token = ?
                """,
                (now.isoformat(), token),
            )

        cls._audit_log(row["credential_name"], "system", "resolve_token", True, f"execution:{execution_id}")
        return value

    @classmethod
    def cleanup_execution_tokens(cls, execution_id: str) -> int:
        """
        Clean up all tokens for a completed execution.

        Args:
            execution_id: Execution ID

        Returns:
            Number of tokens deleted
        """
        cls._ensure_token_table()

        result = DatabaseManager.execute(
            f"DELETE FROM {cls._TOKEN_TABLE} WHERE execution_id = ?",
            (execution_id,),
        )

        count = result.rowcount
        if count > 0:
            logger.debug(f"Cleaned up {count} tokens for execution {execution_id}")

        return count

    @classmethod
    def cleanup_expired_tokens(cls) -> int:
        """
        Clean up all expired tokens.

        Should be called periodically by a background job.

        Returns:
            Number of tokens deleted
        """
        cls._ensure_token_table()
        now = datetime.now(timezone.utc).isoformat()

        result = DatabaseManager.execute(
            f"DELETE FROM {cls._TOKEN_TABLE} WHERE expires_at < ?",
            (now,),
        )

        count = result.rowcount
        if count > 0:
            logger.info(f"Cleaned up {count} expired credential tokens")

        return count

    @classmethod
    def create_tokens_for_execution(
        cls,
        execution_id: str,
        credential_refs: List[dict],
        workspace_id: str,
    ) -> dict:
        """
        Create tokens for all credential references in a workflow execution.

        Args:
            execution_id: Execution ID
            credential_refs: List of credential references, each with:
                - name: Credential name
                - scope: Scope string
                - scope_id: Scope ID
            workspace_id: Workspace ID

        Returns:
            Dict mapping credential name to token
        """
        tokens = {}

        for ref in credential_refs:
            try:
                scope = CredentialScope(ref.get("scope", "workflow"))
                token = cls.create_execution_token(
                    execution_id=execution_id,
                    credential_name=ref["name"],
                    scope=scope,
                    scope_id=ref["scope_id"],
                    workspace_id=workspace_id,
                )
                if token:
                    tokens[ref["name"]] = token
            except Exception as e:
                logger.error(f"Failed to create token for {ref.get('name')}: {e}")

        return tokens
