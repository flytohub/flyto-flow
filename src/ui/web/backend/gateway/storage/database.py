"""SQLite storage for local CE executions, steps, and the worker queue."""

import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path


logger = logging.getLogger(__name__)
DEFAULT_DB_PATH = Path.home() / ".flyto" / "executions.db"
EXECUTION_SCHEMA_VERSION = 3

_connection: sqlite3.Connection | None = None
_db_path: Path | None = None
_db_lock = threading.Lock()


def get_db_path() -> Path:
    configured = os.environ.get("FLYTO_EXECUTION_DB_PATH", "").strip()
    return _db_path or (Path(configured).expanduser() if configured else DEFAULT_DB_PATH)


def _migrate_job_idempotency(connection: sqlite3.Connection) -> None:
    from gateway.storage.migrations import ensure_column

    ensure_column(connection, "jobs", "idempotency_key", "TEXT")
    ensure_column(connection, "jobs", "metadata", "TEXT NOT NULL DEFAULT '{}'")
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_active_idempotency
        ON jobs(idempotency_key)
        WHERE idempotency_key IS NOT NULL AND status IN ('pending', 'running')
        """
    )


def _migrate_operational_tables(connection: sqlite3.Connection) -> None:
    from gateway.storage.migrations import ensure_column, execute_script

    execute_script(
        connection,
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id TEXT PRIMARY KEY,
            sequence INTEGER NOT NULL UNIQUE,
            occurred_at TEXT NOT NULL,
            action TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            result TEXT NOT NULL,
            details TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            event_hash TEXT NOT NULL UNIQUE
        );
        CREATE INDEX IF NOT EXISTS idx_audit_actor_time
            ON audit_events(actor_id, occurred_at DESC);

        CREATE TABLE IF NOT EXISTS credentials (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            scope TEXT NOT NULL,
            scope_id TEXT NOT NULL,
            credential_type TEXT DEFAULT 'generic',
            encrypted_value TEXT NOT NULL,
            key_version INTEGER DEFAULT 1,
            description TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_accessed_at TEXT,
            access_count INTEGER DEFAULT 0
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_credentials_name
            ON credentials(scope, scope_id, name);

        CREATE TABLE IF NOT EXISTS credential_access_log (
            id TEXT PRIMARY KEY,
            credential_name TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            success INTEGER DEFAULT 1,
            reason TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_credential_audit_time
            ON credential_access_log(timestamp);

        CREATE TABLE IF NOT EXISTS credential_tokens (
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
            FOREIGN KEY (credential_id) REFERENCES credentials(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_tokens_execution_id
            ON credential_tokens(execution_id);
        CREATE INDEX IF NOT EXISTS idx_tokens_expires_at
            ON credential_tokens(expires_at);

        CREATE TABLE IF NOT EXISTS variables (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            value TEXT,
            value_type TEXT DEFAULT 'string',
            scope TEXT DEFAULT 'workflow',
            scope_id TEXT NOT NULL,
            environment TEXT DEFAULT 'all',
            is_secret INTEGER DEFAULT 0,
            encrypted_value TEXT,
            description TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_variables_scope
            ON variables(scope, scope_id, environment);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_variables_unique_name
            ON variables(scope, scope_id, environment, name);

        CREATE TABLE IF NOT EXISTS metrics (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            value REAL NOT NULL,
            labels TEXT,
            timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_metrics_name_ts ON metrics(name, timestamp);
        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);

        CREATE TABLE IF NOT EXISTS spans (
            id TEXT PRIMARY KEY,
            trace_id TEXT NOT NULL,
            span_id TEXT NOT NULL,
            parent_span_id TEXT,
            operation_name TEXT NOT NULL,
            service_name TEXT DEFAULT 'flyto',
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_ms INTEGER,
            status TEXT NOT NULL,
            status_message TEXT,
            attributes TEXT,
            events TEXT,
            workspace_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);
        CREATE INDEX IF NOT EXISTS idx_spans_start_time ON spans(start_time);
        CREATE INDEX IF NOT EXISTS idx_spans_operation ON spans(operation_name);
        CREATE INDEX IF NOT EXISTS idx_spans_workspace_id ON spans(workspace_id);

        CREATE TABLE IF NOT EXISTS alert_rules (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            condition TEXT NOT NULL,
            severity TEXT NOT NULL,
            duration_seconds INTEGER DEFAULT 0,
            labels TEXT,
            annotations TEXT,
            enabled INTEGER DEFAULT 1,
            workspace_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_alert_rules_workspace_id
            ON alert_rules(workspace_id);

        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            rule_id TEXT NOT NULL,
            status TEXT NOT NULL,
            severity TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            silenced_until TEXT,
            labels TEXT,
            annotations TEXT,
            evaluated_value REAL,
            threshold_value REAL,
            workspace_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_alerts_rule_id ON alerts(rule_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
        CREATE INDEX IF NOT EXISTS idx_alerts_workspace_id ON alerts(workspace_id);

        CREATE TABLE IF NOT EXISTS workflow_versions (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            version_tag TEXT,
            content_hash TEXT NOT NULL,
            definition TEXT NOT NULL,
            change_summary TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_published INTEGER DEFAULT 0,
            deployed_environments TEXT,
            UNIQUE(workflow_id, version_number)
        );
        CREATE INDEX IF NOT EXISTS idx_wf_versions_workflow
            ON workflow_versions(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_wf_versions_hash
            ON workflow_versions(content_hash);
        """,
    )
    ensure_column(connection, "credentials", "credential_type", "TEXT DEFAULT 'generic'")
    ensure_column(connection, "spans", "workspace_id", "TEXT")
    ensure_column(connection, "alert_rules", "workspace_id", "TEXT")
    ensure_column(connection, "alerts", "workspace_id", "TEXT")


def _migrate_legacy_execution_columns(connection: sqlite3.Connection) -> None:
    _migrate_workspace_column(connection, "executions")
    _migrate_workspace_column(connection, "jobs")
    _migrate_executions(connection)
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_executions_workspace ON executions(workspace_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_jobs_workspace ON jobs(workspace_id)"
    )


def _execution_migrations():
    from gateway.storage.migrations import Migration

    return (
        Migration(
            1,
            "job-idempotency-and-metadata",
            "jobs:+idempotency_key:text,+metadata:text-not-null-default-object,"
            "+idx_jobs_active_idempotency:v1",
            _migrate_job_idempotency,
        ),
        Migration(
            2,
            "operational-tables",
            "audit,credentials,tokens,variables,metrics,traces,alerts,versions:v1",
            _migrate_operational_tables,
        ),
        Migration(
            3,
            "legacy-execution-columns",
            "executions,jobs:workspace-and-snapshot-backfill,indexes:v1",
            _migrate_legacy_execution_columns,
        ),
    )


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
            idempotency_key TEXT,
            metadata TEXT NOT NULL DEFAULT '{}',
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
    from gateway.storage.migrations import apply_migrations

    apply_migrations(_connection, "execution", _execution_migrations())
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


@contextmanager
def transaction(*, immediate: bool = False):
    """Serialize a database transaction and optionally acquire the write lease."""
    with _db_lock:
        connection = get_db()
        connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise


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
