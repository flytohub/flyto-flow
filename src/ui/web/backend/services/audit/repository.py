"""
Immutable Audit Repository

Single responsibility: Append-only audit storage.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from gateway.storage.database import get_cursor

from services.audit.entry import ActorType, AuditAction, AuditEntry, AuditQuery

logger = logging.getLogger(__name__)


class ImmutableAuditRepository:
    """
    Append-only SQLite audit storage.

    Key characteristics:
    - INSERT only, no UPDATE or DELETE
    - Sequential numbering per organization
    - Hash chain for integrity
    """

    _TABLE_NAME = "audit_log"
    _ARCHIVE_TABLE = "audit_archives"
    _initialized = False

    @classmethod
    def _ensure_table(cls) -> None:
        """Ensure audit tables exist."""
        if cls._initialized:
            return

        with get_cursor() as cursor:
            # Main audit log table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                    id TEXT PRIMARY KEY,
                    sequence_number INTEGER NOT NULL,
                    organization_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    actor_type TEXT NOT NULL,
                    actor_ip TEXT,
                    actor_user_agent TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    old_value_hash TEXT,
                    new_value_hash TEXT,
                    change_summary TEXT,
                    timestamp TEXT NOT NULL,
                    prev_entry_hash TEXT NOT NULL,
                    entry_hash TEXT NOT NULL,
                    trace_id TEXT,
                    metadata TEXT,
                    UNIQUE(organization_id, sequence_number)
                )
            """)

            # Indexes
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_audit_org_seq
                ON {cls._TABLE_NAME}(organization_id, sequence_number)
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON {cls._TABLE_NAME}(timestamp)
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_audit_actor
                ON {cls._TABLE_NAME}(actor_id)
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_audit_resource
                ON {cls._TABLE_NAME}(resource_type, resource_id)
            """)

            # Archive reference table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls._ARCHIVE_TABLE} (
                    id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    start_sequence INTEGER NOT NULL,
                    end_sequence INTEGER NOT NULL,
                    archive_path TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

        cls._initialized = True

    @classmethod
    def append(cls, entry: AuditEntry) -> str:
        """
        Append an entry to the audit log.

        This is the ONLY write operation allowed.

        Args:
            entry: Entry to append

        Returns:
            Entry ID
        """
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {cls._TABLE_NAME}
                (id, sequence_number, organization_id, actor_id, actor_type,
                 actor_ip, actor_user_agent, action, resource_type, resource_id,
                 old_value_hash, new_value_hash, change_summary, timestamp,
                 prev_entry_hash, entry_hash, trace_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.id,
                    entry.sequence_number,
                    entry.organization_id,
                    entry.actor_id,
                    entry.actor_type.value if isinstance(entry.actor_type, ActorType) else entry.actor_type,
                    entry.actor_ip,
                    entry.actor_user_agent,
                    entry.action.value if isinstance(entry.action, AuditAction) else entry.action,
                    entry.resource_type,
                    entry.resource_id,
                    entry.old_value_hash,
                    entry.new_value_hash,
                    entry.change_summary,
                    entry.timestamp,
                    entry.prev_entry_hash,
                    entry.entry_hash,
                    entry.trace_id,
                    json.dumps(entry.metadata) if entry.metadata else None,
                ),
            )

        logger.debug(f"Appended audit entry: {entry.id}")
        return entry.id

    @classmethod
    def get(cls, entry_id: str) -> Optional[AuditEntry]:
        """Get an entry by ID."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {cls._TABLE_NAME} WHERE id = ?",
                (entry_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return cls._row_to_entry(dict(row))

    @classmethod
    def get_by_sequence(
        cls,
        organization_id: str,
        sequence_number: int,
    ) -> Optional[AuditEntry]:
        """Get an entry by organization and sequence number."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE organization_id = ? AND sequence_number = ?
                """,
                (organization_id, sequence_number),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return cls._row_to_entry(dict(row))

    @classmethod
    def get_last_entry(cls, organization_id: str) -> Optional[AuditEntry]:
        """Get the last entry for an organization."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE organization_id = ?
                ORDER BY sequence_number DESC
                LIMIT 1
                """,
                (organization_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return cls._row_to_entry(dict(row))

    @classmethod
    def get_next_sequence(cls, organization_id: str) -> int:
        """Get the next sequence number for an organization."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT MAX(sequence_number) FROM {cls._TABLE_NAME}
                WHERE organization_id = ?
                """,
                (organization_id,),
            )
            row = cursor.fetchone()

        if not row or row[0] is None:
            return 1

        return row[0] + 1

    @classmethod
    def query(cls, query: AuditQuery) -> List[AuditEntry]:
        """
        Query audit entries.

        Args:
            query: Query parameters

        Returns:
            List of matching entries
        """
        cls._ensure_table()

        conditions = ["organization_id = ?"]
        params: List[Any] = [query.organization_id]

        if query.actor_id:
            conditions.append("actor_id = ?")
            params.append(query.actor_id)

        if query.action:
            action_value = query.action.value if isinstance(query.action, AuditAction) else query.action
            conditions.append("action = ?")
            params.append(action_value)

        if query.resource_type:
            conditions.append("resource_type = ?")
            params.append(query.resource_type)

        if query.resource_id:
            conditions.append("resource_id = ?")
            params.append(query.resource_id)

        if query.start_time:
            conditions.append("timestamp >= ?")
            params.append(query.start_time)

        if query.end_time:
            conditions.append("timestamp <= ?")
            params.append(query.end_time)

        where_clause = " AND ".join(conditions)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE {where_clause}
                ORDER BY sequence_number DESC
                LIMIT ? OFFSET ?
                """,
                (*params, query.limit, query.offset),
            )
            rows = cursor.fetchall()

        return [cls._row_to_entry(dict(row)) for row in rows]

    @classmethod
    def get_range(
        cls,
        organization_id: str,
        start_seq: int,
        end_seq: int,
    ) -> List[AuditEntry]:
        """
        Get entries in a sequence range.

        Args:
            organization_id: Organization ID
            start_seq: Start sequence (inclusive)
            end_seq: End sequence (inclusive)

        Returns:
            List of entries in order
        """
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE organization_id = ?
                AND sequence_number >= ? AND sequence_number <= ?
                ORDER BY sequence_number ASC
                """,
                (organization_id, start_seq, end_seq),
            )
            rows = cursor.fetchall()

        return [cls._row_to_entry(dict(row)) for row in rows]

    @classmethod
    def count(cls, organization_id: str) -> int:
        """Count entries for an organization."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM {cls._TABLE_NAME}
                WHERE organization_id = ?
                """,
                (organization_id,),
            )
            row = cursor.fetchone()

        return row[0] if row else 0

    @classmethod
    def _row_to_entry(cls, row: dict) -> AuditEntry:
        """Convert database row to AuditEntry."""
        metadata = {}
        if row.get("metadata"):
            try:
                metadata = json.loads(row["metadata"])
            except Exception:
                pass

        return AuditEntry(
            id=row["id"],
            sequence_number=row["sequence_number"],
            organization_id=row["organization_id"],
            actor_id=row["actor_id"],
            actor_type=ActorType(row["actor_type"]),
            actor_ip=row.get("actor_ip"),
            actor_user_agent=row.get("actor_user_agent"),
            action=AuditAction(row["action"]),
            resource_type=row["resource_type"],
            resource_id=row["resource_id"],
            old_value_hash=row.get("old_value_hash"),
            new_value_hash=row.get("new_value_hash"),
            change_summary=row.get("change_summary"),
            timestamp=row.get("timestamp"),
            prev_entry_hash=row.get("prev_entry_hash", ""),
            entry_hash=row.get("entry_hash", ""),
            trace_id=row.get("trace_id"),
            metadata=metadata,
        )
