"""
Workflow Version Repository

Single responsibility: Store workflow versions.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from gateway.storage.database import get_cursor

from services.versioning.version import WorkflowVersion, VersionSummary

logger = logging.getLogger(__name__)


class WorkflowVersionRepository:
    """
    SQLite-based workflow version storage.

    Provides version storage and retrieval.
    """

    _TABLE_NAME = "workflow_versions"
    _initialized = False

    @classmethod
    def _ensure_table(cls) -> None:
        """Ensure workflow_versions table exists."""
        if cls._initialized:
            return

        with get_cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
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
                )
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_wf_versions_workflow
                ON {cls._TABLE_NAME}(workflow_id)
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_wf_versions_hash
                ON {cls._TABLE_NAME}(content_hash)
            """)

        cls._initialized = True

    @classmethod
    def create(cls, version: WorkflowVersion) -> str:
        """
        Create a new version.

        Args:
            version: Version to create

        Returns:
            Version ID
        """
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {cls._TABLE_NAME}
                (id, workflow_id, version_number, version_tag, content_hash,
                 definition, change_summary, created_by, created_at,
                 is_published, deployed_environments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version.id,
                    version.workflow_id,
                    version.version_number,
                    version.version_tag,
                    version.content_hash,
                    json.dumps(version.definition),
                    version.change_summary,
                    version.created_by,
                    version.created_at,
                    1 if version.is_published else 0,
                    json.dumps(version.deployed_environments),
                ),
            )

        return version.id

    @classmethod
    def get(cls, version_id: str) -> Optional[WorkflowVersion]:
        """Get a version by ID."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {cls._TABLE_NAME} WHERE id = ?",
                (version_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return cls._row_to_version(dict(row))

    @classmethod
    def get_by_number(
        cls,
        workflow_id: str,
        version_number: int,
    ) -> Optional[WorkflowVersion]:
        """Get a version by workflow ID and version number."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE workflow_id = ? AND version_number = ?
                """,
                (workflow_id, version_number),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return cls._row_to_version(dict(row))

    @classmethod
    def get_latest(cls, workflow_id: str) -> Optional[WorkflowVersion]:
        """Get the latest version for a workflow."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE workflow_id = ?
                ORDER BY version_number DESC
                LIMIT 1
                """,
                (workflow_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return cls._row_to_version(dict(row))

    @classmethod
    def get_by_hash(cls, content_hash: str) -> Optional[WorkflowVersion]:
        """Get a version by content hash."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {cls._TABLE_NAME} WHERE content_hash = ?",
                (content_hash,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return cls._row_to_version(dict(row))

    @classmethod
    def list_versions(
        cls,
        workflow_id: str,
        limit: int = 100,
    ) -> List[VersionSummary]:
        """
        List versions for a workflow.

        Args:
            workflow_id: Workflow ID
            limit: Maximum versions to return

        Returns:
            List of version summaries
        """
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._TABLE_NAME}
                WHERE workflow_id = ?
                ORDER BY version_number DESC
                LIMIT ?
                """,
                (workflow_id, limit),
            )
            rows = cursor.fetchall()

        versions = [cls._row_to_version(dict(row)) for row in rows]
        return [VersionSummary.from_version(v) for v in versions]

    @classmethod
    def get_next_version_number(cls, workflow_id: str) -> int:
        """Get the next version number for a workflow."""
        cls._ensure_table()

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT MAX(version_number) FROM {cls._TABLE_NAME}
                WHERE workflow_id = ?
                """,
                (workflow_id,),
            )
            row = cursor.fetchone()

        if not row or row[0] is None:
            return 1

        return row[0] + 1

    @classmethod
    def update(cls, version_id: str, **kwargs) -> bool:
        """
        Update a version.

        Args:
            version_id: Version ID
            **kwargs: Fields to update

        Returns:
            True if updated
        """
        cls._ensure_table()

        allowed_fields = {
            "version_tag", "change_summary", "is_published",
            "deployed_environments"
        }

        updates = []
        params = []

        for key, value in kwargs.items():
            if key not in allowed_fields:
                continue

            if key == "is_published":
                value = 1 if value else 0
            elif key == "deployed_environments" and isinstance(value, list):
                value = json.dumps(value)

            updates.append(f"{key} = ?")
            params.append(value)

        if not updates:
            return False

        params.append(version_id)

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {cls._TABLE_NAME}
                SET {", ".join(updates)}
                WHERE id = ?
                """,
                params,
            )
            return cursor.rowcount > 0

    @classmethod
    def publish(cls, version_id: str) -> bool:
        """Mark a version as published."""
        return cls.update(version_id, is_published=True)

    @classmethod
    def add_deployment(cls, version_id: str, environment: str) -> bool:
        """Add an environment to deployed list."""
        version = cls.get(version_id)
        if not version:
            return False

        environments = version.deployed_environments
        if environment not in environments:
            environments.append(environment)

        return cls.update(version_id, deployed_environments=environments)

    @classmethod
    def _row_to_version(cls, row: dict) -> WorkflowVersion:
        """Convert database row to WorkflowVersion."""
        definition = {}
        deployed_environments = []

        if row.get("definition"):
            try:
                definition = json.loads(row["definition"])
            except Exception:
                pass

        if row.get("deployed_environments"):
            try:
                deployed_environments = json.loads(row["deployed_environments"])
            except Exception:
                pass

        return WorkflowVersion(
            id=row["id"],
            workflow_id=row["workflow_id"],
            version_number=row["version_number"],
            version_tag=row.get("version_tag"),
            content_hash=row["content_hash"],
            definition=definition,
            change_summary=row.get("change_summary"),
            created_by=row["created_by"],
            created_at=row.get("created_at"),
            is_published=bool(row.get("is_published", 0)),
            deployed_environments=deployed_environments,
        )
