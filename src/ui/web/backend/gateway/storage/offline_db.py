"""
Offline SQLite Database Setup

Local storage for offline mode data: users, templates, workflows,
notifications, audit logs, and API keys.

Separate from the executions database (database.py) to keep concerns isolated.
"""

import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default database path
DEFAULT_OFFLINE_DB_PATH = Path.home() / ".flyto" / "offline.db"
OFFLINE_DB_PATH_ENV = "FLYTO_OFFLINE_DB_PATH"

# Global connection + lock for thread-safe access from async tasks
_connection: Optional[sqlite3.Connection] = None
_db_path: Optional[Path] = None
_db_lock = threading.Lock()


def get_default_offline_db_path() -> Path:
    """Resolve the configured offline database path for the current process."""
    configured = os.environ.get(OFFLINE_DB_PATH_ENV, "").strip()
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_OFFLINE_DB_PATH


def get_offline_db_path() -> Path:
    """Return the active database path, or the path that will be used on init."""
    return _db_path or get_default_offline_db_path()


def init_offline_db(db_path: Path = None) -> None:
    """
    Initialize offline SQLite database and create tables.

    Args:
        db_path: Path to database file. Defaults to FLYTO_OFFLINE_DB_PATH or
            ~/.flyto/offline.db.
    """
    global _connection, _db_path

    configured_path = os.environ.get("FLYTO_OFFLINE_DB_PATH", "").strip()
    requested_path = db_path or (Path(configured_path) if configured_path else DEFAULT_OFFLINE_DB_PATH)
    requested_path = requested_path.expanduser().resolve()

    if _connection is not None:
        if _db_path == requested_path:
            return
        _connection.close()

    _db_path = requested_path
    _db_path.parent.mkdir(parents=True, exist_ok=True)

    _connection = sqlite3.connect(str(_db_path), check_same_thread=False, timeout=30)
    # Use a custom row factory that returns dicts for easier .get() access
    _connection.row_factory = lambda cursor, row: dict(
        zip([col[0] for col in cursor.description], row)
    )

    # WAL mode: allows concurrent reads while writing, prevents "database is locked"
    _connection.execute("PRAGMA journal_mode = WAL")
    _connection.execute("PRAGMA busy_timeout = 5000")

    # Enable foreign keys
    _connection.execute("PRAGMA foreign_keys = ON")

    # Create tables
    _connection.executescript("""
        -- Users
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT,
            display_name TEXT,
            password_hash TEXT NOT NULL,
            avatar_url TEXT,
            roles TEXT DEFAULT '["user"]',
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

        -- Templates
        CREATE TABLE IF NOT EXISTS templates (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            folder_id TEXT,
            tags TEXT DEFAULT '[]',
            workflow_data TEXT DEFAULT '{}',
            params_schema TEXT DEFAULT '{}',
            icon TEXT,
            color TEXT,
            is_public INTEGER DEFAULT 0,
            version INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_templates_user_id ON templates(user_id);
        CREATE INDEX IF NOT EXISTS idx_templates_created_at ON templates(created_at);

        -- Template folders
        CREATE TABLE IF NOT EXISTS template_folders (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            parent_id TEXT,
            tab TEXT NOT NULL,
            color TEXT,
            order_index INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_template_folders_user_tab
            ON template_folders(user_id, tab);
        CREATE INDEX IF NOT EXISTS idx_template_folders_parent
            ON template_folders(user_id, parent_id);

        -- User profiles
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            bio TEXT,
            website TEXT,
            location TEXT,
            avatar_url TEXT,
            settings TEXT DEFAULT '{}',
            updated_at TEXT
        );

        -- Notifications
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT,
            message TEXT,
            type TEXT,
            is_read INTEGER DEFAULT 0,
            data TEXT DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
        CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

        -- Audit logs
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            actor_id TEXT,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            details TEXT DEFAULT '{}',
            result TEXT,
            ip_address TEXT,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_id ON audit_logs(actor_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

        -- API keys
        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            prefix TEXT,
            key_hash TEXT NOT NULL,
            scopes TEXT DEFAULT '[]',
            last_used_at TEXT,
            created_at TEXT NOT NULL,
            revoked_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
        CREATE INDEX IF NOT EXISTS idx_api_keys_created_at ON api_keys(created_at);
    """)

    # Additive migrations for existing offline databases.
    template_columns = {
        row["name"] for row in _connection.execute("PRAGMA table_info(templates)").fetchall()
    }
    if "folder_id" not in template_columns:
        _connection.execute("ALTER TABLE templates ADD COLUMN folder_id TEXT")
    _connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_templates_folder_id ON templates(folder_id)"
    )

    _connection.commit()
    logger.info(f"Offline SQLite database initialized at {_db_path}")


def get_offline_db() -> sqlite3.Connection:
    """Get offline database connection, initializing if needed."""
    global _connection

    if _connection is None:
        init_offline_db()

    return _connection


def close_offline_db() -> None:
    """Close offline database connection."""
    global _connection, _db_path

    if _connection:
        _connection.close()
        _connection = None
        logger.info("Offline SQLite database connection closed")
    _db_path = None


@contextmanager
def get_offline_cursor():
    """Context manager for offline database cursor with auto-commit.

    Thread-safe: serializes all writes via _db_lock to prevent
    'database is locked' errors from concurrent async tasks.
    """
    with _db_lock:
        db = get_offline_db()
        cursor = db.cursor()
        try:
            yield cursor
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()
