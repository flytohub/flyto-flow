"""SQLite storage for CE's single local workspace."""

import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path


logger = logging.getLogger(__name__)
DEFAULT_OFFLINE_DB_PATH = Path.home() / ".flyto" / "offline.db"
OFFLINE_DB_PATH_ENV = "FLYTO_OFFLINE_DB_PATH"
OFFLINE_SCHEMA_VERSION = 3

_connection: sqlite3.Connection | None = None
_db_path: Path | None = None
_db_lock = threading.Lock()


def _migrate_connection_profiles(connection: sqlite3.Connection) -> None:
    from gateway.storage.migrations import execute_script

    execute_script(
        connection,
        """
        CREATE TABLE IF NOT EXISTS connection_profiles (
            id TEXT NOT NULL,
            scope_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            schema_version INTEGER NOT NULL,
            revision INTEGER NOT NULL,
            scope TEXT NOT NULL,
            config TEXT NOT NULL,
            secret_refs TEXT NOT NULL,
            policy TEXT NOT NULL,
            disabled INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (id, scope_id)
        );
        CREATE INDEX IF NOT EXISTS idx_connection_profiles_scope
            ON connection_profiles(scope_id, name);
        """,
    )


def _migrate_legacy_workspace_columns(connection: sqlite3.Connection) -> None:
    _migrate_workspace_column(connection, "templates")
    _migrate_workspace_column(connection, "workflows")
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_templates_workspace ON templates(workspace_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_workflows_workspace ON workflows(workspace_id)"
    )


def _offline_migrations():
    from gateway.storage.migrations import Migration

    return (
        Migration(
            1,
            "workspace-scoped-records",
            "baseline:workspace_id-required:v1",
            lambda _connection: None,
        ),
        Migration(
            2,
            "connection-profiles",
            "connection_profiles:workspace-scoped:revisioned:v1",
            _migrate_connection_profiles,
        ),
        Migration(
            3,
            "legacy-workspace-columns",
            "templates,workflows:workspace-backfill,indexes:v1",
            _migrate_legacy_workspace_columns,
        ),
    )


def get_default_offline_db_path() -> Path:
    """Resolve the configured offline database path for the current process."""
    configured = os.environ.get(OFFLINE_DB_PATH_ENV, "").strip()
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_OFFLINE_DB_PATH


def get_offline_db_path() -> Path:
    """Return the active database path, or the path that will be used on init."""
    return _db_path or get_default_offline_db_path()


def init_offline_db(db_path: Path | None = None) -> None:
    """Open the local database and create only Flow workflow tables."""
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
    _connection.row_factory = lambda cursor, row: dict(
        zip([column[0] for column in cursor.description], row)
    )
    _connection.execute("PRAGMA journal_mode = WAL")
    _connection.execute("PRAGMA busy_timeout = 5000")
    _connection.execute("PRAGMA foreign_keys = ON")
    _connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS templates (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            tags TEXT DEFAULT '[]',
            workflow_data TEXT DEFAULT '{}',
            params_schema TEXT DEFAULT '{}',
            icon TEXT,
            color TEXT,
            version INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            trigger_type TEXT DEFAULT 'manual',
            trigger_config TEXT DEFAULT '{}',
            nodes TEXT DEFAULT '[]',
            edges TEXT DEFAULT '[]',
            tags TEXT DEFAULT '[]',
            total_executions INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            error_workflow_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_executed_at TEXT
        );
        """
    )
    from gateway.storage.migrations import apply_migrations

    apply_migrations(_connection, "offline", _offline_migrations())
    _connection.commit()
    logger.info("Local CE database initialized at %s", _db_path)


def _migrate_workspace_column(connection: sqlite3.Connection, table: str) -> None:
    """Migrate pre-Flow local databases without losing existing records."""
    columns = {
        row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if "workspace_id" not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN workspace_id TEXT")
    if "user_id" in columns:
        connection.execute(
            f"UPDATE {table} SET workspace_id = COALESCE(workspace_id, user_id, 'local-workspace')"
        )
    else:
        connection.execute(
            f"UPDATE {table} SET workspace_id = COALESCE(workspace_id, 'local-workspace')"
        )


def get_offline_db() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        init_offline_db()
    assert _connection is not None
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
    """Yield a serialized cursor and commit or roll back atomically."""
    with _db_lock:
        database = get_offline_db()
        cursor = database.cursor()
        try:
            yield cursor
            database.commit()
        except Exception:
            database.rollback()
            raise
        finally:
            cursor.close()


@contextmanager
def offline_transaction(*, immediate: bool = False):
    """Yield a serialized local-data transaction."""
    with _db_lock:
        database = get_offline_db()
        database.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        try:
            yield database
            database.commit()
        except Exception:
            database.rollback()
            raise
