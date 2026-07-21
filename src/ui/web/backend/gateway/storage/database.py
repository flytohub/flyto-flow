"""
SQLite Database Setup

Local storage for execution records.
"""

import logging
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default database path — use /tmp on Cloud Run (home dir is read-only)
import os
if os.environ.get("DEPLOYMENT_MODE") in ("cloud", "worker"):
    DEFAULT_DB_PATH = Path("/tmp") / "flyto" / "executions.db"
else:
    DEFAULT_DB_PATH = Path.home() / ".flyto" / "executions.db"

# Global connection + lock for thread-safe access from async tasks
_connection: Optional[sqlite3.Connection] = None
_db_path: Optional[Path] = None
_db_lock = threading.Lock()


def init_db(db_path: Path = None) -> None:
    """
    Initialize SQLite database and create tables.

    Args:
        db_path: Path to database file. Defaults to ~/.flyto/executions.db
    """
    global _connection, _db_path

    _db_path = db_path or DEFAULT_DB_PATH
    _db_path.parent.mkdir(parents=True, exist_ok=True)

    _connection = sqlite3.connect(str(_db_path), check_same_thread=False, timeout=30)
    # Use a custom row factory that returns dicts for easier .get() access
    _connection.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))

    # WAL mode: allows concurrent reads while writing, prevents "database is locked"
    _connection.execute("PRAGMA journal_mode = WAL")
    _connection.execute("PRAGMA busy_timeout = 5000")

    # Enable foreign keys
    _connection.execute("PRAGMA foreign_keys = ON")

    # Create tables
    _connection.executescript("""
        -- Execution records
        CREATE TABLE IF NOT EXISTS executions (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            workflow_name TEXT,
            workflow_version TEXT DEFAULT '1.0.0',
            user_id TEXT,

            -- Status
            status TEXT DEFAULT 'pending',  -- pending, running, success, failure, cancelled

            -- Timing
            started_at TEXT NOT NULL,
            finished_at TEXT,
            duration_ms INTEGER,

            -- Data (JSON stored as TEXT)
            input_params TEXT DEFAULT '{}',
            result_data TEXT,

            -- Error info
            error_message TEXT,
            error_step_id TEXT,

            -- Snapshot data (JSON stored as TEXT)
            workflow_snapshot TEXT,    -- Full workflow definition
            modules_snapshot TEXT,     -- Module versions
            env_snapshot TEXT,         -- Environment info

            -- Outcome classification
            outcome TEXT,              -- success, failure, partial_success, cancelled
            outcome_reason TEXT,
            error_category TEXT,
            error_fingerprint TEXT,

            -- Metadata
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Step execution logs
        CREATE TABLE IF NOT EXISTS execution_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            step_id TEXT NOT NULL,
            step_index INTEGER,
            module_id TEXT,

            -- Status
            status TEXT DEFAULT 'pending',  -- pending, running, success, failure, skipped

            -- Timing
            started_at TEXT,
            finished_at TEXT,
            duration_ms INTEGER,

            -- Data (JSON stored as TEXT)
            input_params TEXT,
            output_data TEXT,
            error_message TEXT,

            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_executions_workflow_id ON executions(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_executions_user_id ON executions(user_id);
        CREATE INDEX IF NOT EXISTS idx_executions_started_at ON executions(started_at);
        CREATE INDEX IF NOT EXISTS idx_execution_steps_execution_id ON execution_steps(execution_id);

        -- Job queue for worker-based execution (Phase 1)
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            execution_id TEXT NOT NULL UNIQUE,
            workflow_id TEXT NOT NULL,
            user_id TEXT,

            -- Priority (higher = more urgent)
            priority INTEGER DEFAULT 0,

            -- Status: pending, running, completed, failed, cancelled
            status TEXT DEFAULT 'pending',

            -- Retry management
            attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 3,

            -- Timeout in milliseconds (0 = no limit)
            timeout_ms INTEGER DEFAULT 0,

            -- Lease management for worker coordination
            locked_by TEXT,              -- Worker ID holding the lock
            lease_until TEXT,            -- Lease expiration timestamp
            heartbeat_at TEXT,           -- Last heartbeat from worker

            -- Visibility timeout (ms) - delay before retry after failure
            visibility_timeout_ms INTEGER DEFAULT 30000,

            -- Error info
            error_message TEXT,

            -- Timestamps
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            started_at TEXT,
            finished_at TEXT,

            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        -- Job queue indexes
        CREATE INDEX IF NOT EXISTS idx_jobs_status_priority ON jobs(status, priority DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_execution_id ON jobs(execution_id);
        CREATE INDEX IF NOT EXISTS idx_jobs_lease_until ON jobs(lease_until);
        CREATE INDEX IF NOT EXISTS idx_jobs_locked_by ON jobs(locked_by);

        -- ============================================================
        -- Messaging Integrations (LINE, Telegram, Slack, Discord, etc.)
        -- ============================================================

        -- Integration configurations
        CREATE TABLE IF NOT EXISTS messaging_integrations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT,

            -- Provider info
            provider TEXT NOT NULL,           -- line, telegram, slack, discord, whatsapp
            name TEXT NOT NULL,               -- User-friendly name
            description TEXT,

            -- Status
            status TEXT DEFAULT 'active',     -- active, disabled, error

            -- Configuration (encrypted JSON)
            config_encrypted TEXT NOT NULL,   -- Encrypted JSON (tokens, secrets)
            key_version INTEGER DEFAULT 1,    -- Encryption key version

            -- Webhook info
            webhook_id TEXT UNIQUE,           -- Unique webhook path identifier
            webhook_secret TEXT,              -- For additional signature verification

            -- Workflow binding
            default_workflow_id TEXT,         -- Default workflow to execute
            workflow_mapping TEXT,            -- JSON: {"message": "wf_id", "postback": "wf_id"}

            -- Provider-specific identifiers
            external_channel_id TEXT,         -- LINE channel ID, TG bot ID, etc.
            external_bot_name TEXT,           -- Bot display name from provider

            -- Timestamps
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            last_webhook_at TEXT,

            -- Stats
            message_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_msg_integrations_user ON messaging_integrations(user_id);
        CREATE INDEX IF NOT EXISTS idx_msg_integrations_provider ON messaging_integrations(provider);
        CREATE INDEX IF NOT EXISTS idx_msg_integrations_webhook ON messaging_integrations(webhook_id);
        CREATE INDEX IF NOT EXISTS idx_msg_integrations_status ON messaging_integrations(status);

        -- Incoming message queue (inbox)
        CREATE TABLE IF NOT EXISTS messaging_inbox (
            id TEXT PRIMARY KEY,
            integration_id TEXT NOT NULL,
            user_id TEXT NOT NULL,

            -- Provider info
            provider TEXT NOT NULL,

            -- Sender info
            sender_id TEXT NOT NULL,          -- Platform-specific sender ID
            sender_name TEXT,
            sender_avatar_url TEXT,
            channel_id TEXT,                  -- Group/channel ID if applicable
            channel_type TEXT DEFAULT 'user', -- user, group, channel

            -- Message content (normalized)
            message_type TEXT NOT NULL,       -- text, image, audio, video, file, location, sticker, postback
            content TEXT,                     -- Text content or JSON for rich content
            raw_payload TEXT,                 -- Original provider payload (JSON)

            -- Reply context
            reply_token TEXT,                 -- Provider reply token if applicable
            reply_token_expires_at TEXT,
            thread_id TEXT,                   -- Thread/conversation ID
            reply_to_message_id TEXT,         -- If replying to a message

            -- Processing status
            status TEXT DEFAULT 'pending',    -- pending, processing, completed, failed, expired
            processed_by TEXT,                -- Device ID that claimed this message
            processing_started_at TEXT,
            completed_at TEXT,

            -- Workflow execution
            execution_id TEXT,
            workflow_id TEXT,

            -- Error info
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,

            -- Timestamps
            received_at TEXT DEFAULT CURRENT_TIMESTAMP,
            provider_timestamp INTEGER,       -- Original timestamp from provider

            FOREIGN KEY (integration_id) REFERENCES messaging_integrations(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_msg_inbox_status ON messaging_inbox(status);
        CREATE INDEX IF NOT EXISTS idx_msg_inbox_integration ON messaging_inbox(integration_id);
        CREATE INDEX IF NOT EXISTS idx_msg_inbox_user ON messaging_inbox(user_id);
        CREATE INDEX IF NOT EXISTS idx_msg_inbox_received ON messaging_inbox(received_at);
        CREATE INDEX IF NOT EXISTS idx_msg_inbox_sender ON messaging_inbox(sender_id);

        -- Outgoing message queue (outbox)
        CREATE TABLE IF NOT EXISTS messaging_outbox (
            id TEXT PRIMARY KEY,
            integration_id TEXT NOT NULL,
            inbox_message_id TEXT,            -- Reference to original message (for replies)

            -- Target
            recipient_id TEXT NOT NULL,
            channel_id TEXT,

            -- Content
            message_type TEXT NOT NULL,       -- text, image, template, flex, etc.
            content TEXT NOT NULL,            -- JSON message payload

            -- Status
            status TEXT DEFAULT 'pending',    -- pending, sending, sent, failed
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,

            -- Results
            sent_at TEXT,
            provider_message_id TEXT,         -- Message ID returned by provider
            error_message TEXT,

            -- Timestamps
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (integration_id) REFERENCES messaging_integrations(id) ON DELETE CASCADE,
            FOREIGN KEY (inbox_message_id) REFERENCES messaging_inbox(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_msg_outbox_status ON messaging_outbox(status);
        CREATE INDEX IF NOT EXISTS idx_msg_outbox_integration ON messaging_outbox(integration_id);

        -- Conversation state (for multi-turn interactions)
        CREATE TABLE IF NOT EXISTS messaging_conversations (
            id TEXT PRIMARY KEY,              -- integration_id + sender_id
            integration_id TEXT NOT NULL,
            sender_id TEXT NOT NULL,

            -- Current state
            current_flow TEXT DEFAULT 'idle', -- Current workflow/flow name
            current_step TEXT,                -- Current step in flow
            context TEXT DEFAULT '{}',        -- JSON context data

            -- Timestamps
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            last_message_at TEXT,

            FOREIGN KEY (integration_id) REFERENCES messaging_integrations(id) ON DELETE CASCADE,
            UNIQUE(integration_id, sender_id)
        );

        CREATE INDEX IF NOT EXISTS idx_msg_conversations_integration ON messaging_conversations(integration_id);
    """)

    _connection.commit()

    # Migrate existing tables: add new columns if they don't exist
    _migrate_tables(_connection)

    logger.info(f"SQLite database initialized at {_db_path}")


def _migrate_tables(conn: sqlite3.Connection) -> None:
    """
    Add new columns to existing tables if they don't exist.

    This handles schema evolution for existing installations.
    """
    cursor = conn.cursor()

    # Get existing columns in executions table
    cursor.execute("PRAGMA table_info(executions)")
    existing_columns = {row["name"] for row in cursor.fetchall()}

    # New columns added in Phase 0
    new_columns = [
        ("workflow_snapshot", "TEXT"),
        ("modules_snapshot", "TEXT"),
        ("env_snapshot", "TEXT"),
        ("outcome", "TEXT"),
        ("outcome_reason", "TEXT"),
        ("error_category", "TEXT"),
        ("error_fingerprint", "TEXT"),
    ]

    # Whitelist validation: only allow known column names/types
    _ALLOWED_COL_NAMES = {name for name, _ in new_columns}
    _ALLOWED_COL_TYPES = {"TEXT", "INTEGER", "REAL", "BLOB"}

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            if col_name not in _ALLOWED_COL_NAMES or col_type not in _ALLOWED_COL_TYPES:
                logger.error(f"Rejected invalid column: {col_name} {col_type}")
                continue
            try:
                # Safe: col_name and col_type validated against whitelist above
                cursor.execute(f"ALTER TABLE executions ADD COLUMN {col_name} {col_type}")
                logger.info(f"Added column {col_name} to executions table")
            except Exception as e:
                logger.debug(f"Column {col_name} may already exist: {e}")

    conn.commit()
    cursor.close()


def get_db() -> sqlite3.Connection:
    """Get database connection, initializing if needed."""
    global _connection

    if _connection is None:
        init_db()

    return _connection


def close_db() -> None:
    """Close database connection."""
    global _connection

    if _connection:
        _connection.close()
        _connection = None
        logger.info("SQLite database connection closed")


@contextmanager
def get_cursor():
    """Context manager for database cursor with auto-commit.

    Thread-safe: serializes all writes via _db_lock to prevent
    'database is locked' errors from concurrent async tasks.
    """
    with _db_lock:
        db = get_db()
        cursor = db.cursor()
        try:
            yield cursor
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()


# Compatibility alias for get_db
def get_db_connection():
    """Alias for get_db() for backward compatibility."""
    return get_db()


class DatabaseManager:
    """
    Compatibility class providing static database methods.

    Note: Prefer using get_cursor() context manager for new code.
    """

    @staticmethod
    def execute(sql: str, params: tuple = None):
        """Execute SQL and return cursor."""
        with _db_lock:
            conn = get_db()
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            return cursor

    @staticmethod
    def fetchone(sql: str, params: tuple = None):
        """Execute SQL and fetch one row."""
        conn = get_db()
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchone()

    @staticmethod
    def fetchall(sql: str, params: tuple = None):
        """Execute SQL and fetch all rows."""
        conn = get_db()
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchall()
