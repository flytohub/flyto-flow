"""SQLite storage for local CE executions, steps, and the worker queue."""

import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path


logger = logging.getLogger(__name__)
DEFAULT_DB_PATH = Path.home() / ".flyto" / "executions.db"

_connection: sqlite3.Connection | None = None
_db_path: Path | None = None
_db_lock = threading.Lock()


def init_db(db_path: Path | None = None) -> None:
    global _connection, _db_path

    configured = os.environ.get("FLYTO_EXECUTION_DB_PATH", "").strip()
    requested = db_path or (Path(configured) if configured else DEFAULT_DB_PATH)
    requested = requested.expanduser().resolve()
    if _connection is not None:
        if _db_path == requested:
            return
        _connection.close()

    _db_path = requested
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
        CREATE TABLE IF NOT EXISTS executions (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            workflow_name TEXT,
            workflow_version TEXT DEFAULT '1.0.0',
            workspace_id TEXT,
            status TEXT DEFAULT 'pending',
            started_at TEXT NOT NULL,
            finished_at TEXT,
            duration_ms INTEGER,
            input_params TEXT DEFAULT '{}',
            result_data TEXT,
            error_message TEXT,
            error_step_id TEXT,
            workflow_snapshot TEXT,
            modules_snapshot TEXT,
            env_snapshot TEXT,
            outcome TEXT,
            outcome_reason TEXT,
            error_category TEXT,
            error_fingerprint TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_executions_workflow_id ON executions(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_executions_started_at ON executions(started_at);

        CREATE TABLE IF NOT EXISTS execution_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            step_id TEXT NOT NULL,
            step_index INTEGER,
            module_id TEXT,
            status TEXT DEFAULT 'pending',
            started_at TEXT,
            finished_at TEXT,
            duration_ms INTEGER,
            input_params TEXT,
            output_data TEXT,
            error_message TEXT,
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_execution_steps_execution_id
            ON execution_steps(execution_id);

        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            execution_id TEXT NOT NULL UNIQUE,
            workflow_id TEXT NOT NULL,
            workspace_id TEXT,
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 3,
            timeout_ms INTEGER DEFAULT 0,
            locked_by TEXT,
            lease_until TEXT,
            heartbeat_at TEXT,
            visibility_timeout_ms INTEGER DEFAULT 30000,
            error_message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            started_at TEXT,
            finished_at TEXT,
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_jobs_status_priority ON jobs(status, priority DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_execution_id ON jobs(execution_id);
        CREATE INDEX IF NOT EXISTS idx_jobs_lease_until ON jobs(lease_until);
        CREATE INDEX IF NOT EXISTS idx_jobs_locked_by ON jobs(locked_by);
        """
    )
    _migrate_workspace_column(_connection, "executions")
    _migrate_workspace_column(_connection, "jobs")
    _migrate_executions(_connection)
    _connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_executions_workspace ON executions(workspace_id)"
    )
    _connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_jobs_workspace ON jobs(workspace_id)"
    )
    _connection.commit()


def _migrate_executions(connection: sqlite3.Connection) -> None:
    existing = {
        row["name"] for row in connection.execute("PRAGMA table_info(executions)").fetchall()
    }
    columns = (
        ("workflow_snapshot", "TEXT"),
        ("modules_snapshot", "TEXT"),
        ("env_snapshot", "TEXT"),
        ("outcome", "TEXT"),
        ("outcome_reason", "TEXT"),
        ("error_category", "TEXT"),
        ("error_fingerprint", "TEXT"),
    )
    for name, column_type in columns:
        if name not in existing:
            connection.execute(f"ALTER TABLE executions ADD COLUMN {name} {column_type}")


def _migrate_workspace_column(connection: sqlite3.Connection, table: str) -> None:
    """Keep local data created before the accountless workspace schema."""
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


def get_db() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        init_db()
    assert _connection is not None
    return _connection


def close_db() -> None:
    global _connection
    if _connection:
        _connection.close()
        _connection = None


@contextmanager
def get_cursor():
    with _db_lock:
        connection = get_db()
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


def get_db_connection() -> sqlite3.Connection:
    return get_db()


class DatabaseManager:
    """Compatibility wrapper for local repositories sharing this database."""

    @staticmethod
    def execute(sql: str, params: tuple | None = None):
        with _db_lock:
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(sql, params or ())
            connection.commit()
            return cursor

    @staticmethod
    def fetchone(sql: str, params: tuple | None = None):
        cursor = get_db().cursor()
        cursor.execute(sql, params or ())
        return cursor.fetchone()

    @staticmethod
    def fetchall(sql: str, params: tuple | None = None):
        cursor = get_db().cursor()
        cursor.execute(sql, params or ())
        return cursor.fetchall()
