"""Deterministic SQLite schema migrations with an auditable ledger."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable


MigrationAction = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    fingerprint: str
    apply: MigrationAction

    @property
    def checksum(self) -> str:
        payload = f"{self.version}:{self.name}:{self.fingerprint}".encode()
        return hashlib.sha256(payload).hexdigest()


def ensure_column(
    connection: sqlite3.Connection,
    table: str,
    name: str,
    declaration: str,
) -> None:
    columns = {
        row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if name not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")


def execute_script(connection: sqlite3.Connection, script: str) -> None:
    """Execute complete SQLite statements without implicit transaction commits."""
    statement = ""
    for line in script.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            connection.execute(statement)
            statement = ""
    if statement.strip():
        raise RuntimeError("Incomplete SQLite migration statement")


def apply_migrations(
    connection: sqlite3.Connection,
    namespace: str,
    migrations: Iterable[Migration],
) -> int:
    """Apply pending migrations atomically and reject changed history."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            namespace TEXT NOT NULL,
            version INTEGER NOT NULL,
            name TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            PRIMARY KEY (namespace, version)
        )
        """
    )
    applied = {
        row["version"]: row
        for row in connection.execute(
            "SELECT version, name, checksum FROM schema_migrations WHERE namespace = ?",
            (namespace,),
        ).fetchall()
    }
    ordered = sorted(migrations, key=lambda migration: migration.version)
    if len({migration.version for migration in ordered}) != len(ordered):
        raise RuntimeError(f"Duplicate migration version in namespace {namespace}")
    expected_versions = list(range(1, len(ordered) + 1))
    actual_versions = [migration.version for migration in ordered]
    if actual_versions != expected_versions:
        raise RuntimeError(
            f"Migration versions must be contiguous in namespace {namespace}: "
            f"expected {expected_versions}, found {actual_versions}"
        )
    if any(
        not migration.name.strip() or not migration.fingerprint.strip()
        for migration in ordered
    ):
        raise RuntimeError(f"Empty migration metadata in namespace {namespace}")
    unknown_applied = sorted(set(applied) - set(actual_versions))
    if unknown_applied:
        raise RuntimeError(
            f"Database contains unsupported {namespace} migration versions: "
            + ", ".join(str(version) for version in unknown_applied)
        )

    if connection.in_transaction:
        connection.commit()
    for migration in ordered:
        previous = applied.get(migration.version)
        if previous:
            if previous["name"] != migration.name or previous["checksum"] != migration.checksum:
                raise RuntimeError(
                    f"Migration history changed: {namespace}/{migration.version}"
                )
            continue
        connection.execute("BEGIN IMMEDIATE")
        try:
            migration.apply(connection)
            connection.execute(
                """
                INSERT INTO schema_migrations
                    (namespace, version, name, checksum, applied_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    namespace,
                    migration.version,
                    migration.name,
                    migration.checksum,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return ordered[-1].version if ordered else 0


def current_schema_version(connection: sqlite3.Connection, namespace: str) -> int:
    try:
        row = connection.execute(
            "SELECT MAX(version) AS version FROM schema_migrations WHERE namespace = ?",
            (namespace,),
        ).fetchone()
    except sqlite3.OperationalError:
        return 0
    return int(row["version"] or 0)
