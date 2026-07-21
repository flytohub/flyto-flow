"""
Nonce Store

Storage for webhook nonces to prevent replay attacks.
"""

import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class NonceStore:
    """
    Nonce storage for replay attack prevention.

    Stores used nonces with TTL to prevent webhook replay attacks.
    """

    _TABLE_NAME = "webhook_nonces"

    @classmethod
    def _ensure_table(cls) -> None:
        """Ensure nonces table exists."""
        from gateway.storage.database import DatabaseManager

        DatabaseManager.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                nonce TEXT PRIMARY KEY,
                webhook_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        DatabaseManager.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_nonces_expires
            ON {cls._TABLE_NAME}(expires_at)
            """
        )

    @classmethod
    def exists(cls, nonce: str) -> bool:
        """Check if nonce has been used."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        row = DatabaseManager.fetchone(
            f"SELECT 1 FROM {cls._TABLE_NAME} WHERE nonce = ?",
            (nonce,),
        )

        return row is not None

    @classmethod
    def store(
        cls,
        nonce: str,
        webhook_id: str,
        ttl_seconds: int = 600,
    ) -> None:
        """
        Store a used nonce.

        Args:
            nonce: The nonce value
            webhook_id: Associated webhook
            ttl_seconds: Time to live (default 10 minutes)
        """
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        try:
            DatabaseManager.execute(
                f"""
                INSERT INTO {cls._TABLE_NAME} (nonce, webhook_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (nonce, webhook_id, now.isoformat(), expires_at.isoformat()),
            )
        except Exception:
            # Already exists (race condition)
            pass

    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove expired nonces."""
        from gateway.storage.database import DatabaseManager

        cls._ensure_table()

        now = datetime.now(timezone.utc).isoformat()

        result = DatabaseManager.execute(
            f"DELETE FROM {cls._TABLE_NAME} WHERE expires_at < ?",
            (now,),
        )

        return result.rowcount
