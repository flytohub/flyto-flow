"""
Audit Archiver

Single responsibility: Archive old audit entries.
"""

import gzip
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from gateway.storage.database import get_cursor

from services.audit.entry import AuditEntry
from services.audit.repository import ImmutableAuditRepository

logger = logging.getLogger(__name__)


@dataclass
class ArchiveResult:
    """Result of an archive operation."""

    id: str
    organization_id: str
    start_sequence: int
    end_sequence: int
    entries_archived: int
    archive_path: str
    checksum: str
    created_at: str
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "start_sequence": self.start_sequence,
            "end_sequence": self.end_sequence,
            "entries_archived": self.entries_archived,
            "archive_path": self.archive_path,
            "checksum": self.checksum,
            "created_at": self.created_at,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class ArchiveInfo:
    """Information about an existing archive."""

    id: str
    organization_id: str
    start_sequence: int
    end_sequence: int
    archive_path: str
    checksum: str
    created_at: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "start_sequence": self.start_sequence,
            "end_sequence": self.end_sequence,
            "archive_path": self.archive_path,
            "checksum": self.checksum,
            "created_at": self.created_at,
        }


class AuditArchiver:
    """
    Archive old audit entries.

    Exports entries to compressed files for long-term storage,
    then optionally removes them from the database.
    """

    _ARCHIVE_TABLE = "audit_archives"

    @classmethod
    def archive(
        cls,
        organization_id: str,
        before_sequence: int,
        destination: str,
        delete_after_archive: bool = False,
    ) -> ArchiveResult:
        """
        Archive entries before a sequence number.

        Args:
            organization_id: Organization ID
            before_sequence: Archive entries before this sequence
            destination: Directory path for archive file
            delete_after_archive: Delete entries after archiving

        Returns:
            Archive result
        """
        archive_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        result = ArchiveResult(
            id=archive_id,
            organization_id=organization_id,
            start_sequence=1,
            end_sequence=before_sequence - 1,
            entries_archived=0,
            archive_path="",
            checksum="",
            created_at=created_at,
        )

        try:
            # Get entries to archive
            entries = ImmutableAuditRepository.get_range(
                organization_id, 1, before_sequence - 1
            )

            if not entries:
                result.entries_archived = 0
                result.error = "No entries to archive"
                result.success = False
                return result

            result.start_sequence = entries[0].sequence_number
            result.end_sequence = entries[-1].sequence_number
            result.entries_archived = len(entries)

            # Create archive directory
            dest_path = Path(destination)
            dest_path.mkdir(parents=True, exist_ok=True)

            # Generate archive filename
            filename = f"audit_{organization_id}_{result.start_sequence}-{result.end_sequence}.json.gz"
            archive_path = dest_path / filename
            result.archive_path = str(archive_path)

            # Write compressed archive
            cls._write_archive(entries, archive_path)

            # Compute checksum
            result.checksum = cls._compute_file_checksum(archive_path)

            # Record archive in database
            cls._record_archive(result)

            # Optionally delete archived entries
            if delete_after_archive:
                cls._delete_archived_entries(
                    organization_id,
                    result.start_sequence,
                    result.end_sequence,
                )

            logger.info(
                f"Archived {result.entries_archived} entries for {organization_id} "
                f"to {archive_path}"
            )

        except Exception as e:
            result.success = False
            result.error = str(e)
            logger.error(f"Archive failed: {e}")

        return result

    @classmethod
    def _write_archive(cls, entries: List[AuditEntry], path: Path) -> None:
        """Write entries to compressed archive."""
        data = {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entries": [e.to_dict() for e in entries],
        }

        with gzip.open(path, "wt", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    @classmethod
    def _compute_file_checksum(cls, path: Path) -> str:
        """Compute SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    @classmethod
    def _record_archive(cls, result: ArchiveResult) -> None:
        """Record archive in database."""
        with get_cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {cls._ARCHIVE_TABLE}
                (id, organization_id, start_sequence, end_sequence,
                 archive_path, checksum, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.id,
                    result.organization_id,
                    result.start_sequence,
                    result.end_sequence,
                    result.archive_path,
                    result.checksum,
                    result.created_at,
                ),
            )

    @classmethod
    def _delete_archived_entries(
        cls,
        organization_id: str,
        start_seq: int,
        end_seq: int,
    ) -> None:
        """Delete archived entries from main table."""
        # Note: This is the ONLY delete operation on audit_log
        # It should only be used after successful archival
        with get_cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM audit_log
                WHERE organization_id = ?
                AND sequence_number >= ? AND sequence_number <= ?
                """,
                (organization_id, start_seq, end_seq),
            )

        logger.info(
            f"Deleted archived entries {start_seq}-{end_seq} for {organization_id}"
        )

    @classmethod
    def restore(cls, archive_path: str) -> int:
        """
        Restore entries from an archive.

        Args:
            archive_path: Path to archive file

        Returns:
            Number of entries restored
        """
        path = Path(archive_path)

        if not path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)

        entries = [AuditEntry.from_dict(e) for e in data.get("entries", [])]

        restored = 0
        for entry in entries:
            try:
                ImmutableAuditRepository.append(entry)
                restored += 1
            except Exception as e:
                logger.warning(f"Failed to restore entry {entry.id}: {e}")

        logger.info(f"Restored {restored} entries from {archive_path}")
        return restored

    @classmethod
    def list_archives(cls, organization_id: str) -> List[ArchiveInfo]:
        """
        List archives for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            List of archive info
        """
        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM {cls._ARCHIVE_TABLE}
                WHERE organization_id = ?
                ORDER BY start_sequence ASC
                """,
                (organization_id,),
            )
            rows = cursor.fetchall()

        return [
            ArchiveInfo(
                id=row["id"],
                organization_id=row["organization_id"],
                start_sequence=row["start_sequence"],
                end_sequence=row["end_sequence"],
                archive_path=row["archive_path"],
                checksum=row["checksum"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    @classmethod
    def verify_archive(cls, archive_path: str, expected_checksum: str) -> bool:
        """
        Verify an archive's integrity.

        Args:
            archive_path: Path to archive file
            expected_checksum: Expected SHA-256 checksum

        Returns:
            True if checksum matches
        """
        path = Path(archive_path)

        if not path.exists():
            return False

        actual_checksum = cls._compute_file_checksum(path)
        return actual_checksum == expected_checksum
