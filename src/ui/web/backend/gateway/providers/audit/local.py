"""Tamper-evident local audit provider with export support."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from gateway.storage.database import DatabaseManager, transaction


_REDACTED_KEYS = {
    "apikey",
    "authorization",
    "clientsecret",
    "credential",
    "password",
    "privatekey",
    "secret",
    "token",
}


def _is_redacted_key(value: str) -> bool:
    normalized = value.lower().replace("_", "").replace("-", "")
    return normalized in _REDACTED_KEYS or normalized.endswith(
        ("password", "secret", "token")
    )


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if _is_redacted_key(key) else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


class LocalAuditProvider:
    """Append-only hash chain stored in the local execution database."""

    @property
    def name(self) -> str:
        return "local-hash-chain"

    @classmethod
    def _ensure_table(cls) -> None:
        DatabaseManager.execute(
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
            )
            """
        )
        DatabaseManager.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_actor_time "
            "ON audit_events(actor_id, occurred_at DESC)"
        )

    async def log(
        self,
        action: str,
        actor_id: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        result: str = "success",
        details: dict | None = None,
        **_kwargs: Any,
    ) -> None:
        self._ensure_table()
        with transaction(immediate=True) as connection:
            previous = connection.execute(
                "SELECT sequence, event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            sequence = int(previous["sequence"]) + 1 if previous else 1
            previous_hash = previous["event_hash"] if previous else "0" * 64
            occurred_at = datetime.now(timezone.utc).isoformat()
            safe_details = json.dumps(
                _redact(details or {}),
                sort_keys=True,
                separators=(",", ":"),
            )
            canonical = json.dumps(
                {
                    "sequence": sequence,
                    "occurred_at": occurred_at,
                    "action": action,
                    "actor_id": actor_id,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "result": result,
                    "details": safe_details,
                    "previous_hash": previous_hash,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            event_hash = hashlib.sha256(canonical.encode()).hexdigest()
            connection.execute(
                """
                INSERT INTO audit_events (
                    id, sequence, occurred_at, action, actor_id, resource_type,
                    resource_id, result, details, previous_hash, event_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    sequence,
                    occurred_at,
                    action,
                    actor_id,
                    resource_type,
                    resource_id,
                    result,
                    safe_details,
                    previous_hash,
                    event_hash,
                ),
            )

    async def get_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        return await self.query({}, limit=limit)

    async def get_by_actor(self, actor_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return await self.query({"actor_id": actor_id}, limit=limit)

    async def query(
        self,
        filters: dict,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        self._ensure_table()
        clauses: list[str] = []
        params: list[Any] = []
        for key in ("actor_id", "action", "result", "resource_type", "resource_id"):
            value = filters.get(key)
            if value is not None:
                clauses.append(f"{key} = ?")
                params.append(value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend((max(1, min(limit, 10000)), max(0, offset)))
        rows = DatabaseManager.fetchall(
            f"SELECT * FROM audit_events {where} ORDER BY sequence DESC LIMIT ? OFFSET ?",
            tuple(params),
        )
        return [self._decode(row) for row in rows]

    async def verify_chain(self) -> bool:
        self._ensure_table()
        rows = DatabaseManager.fetchall("SELECT * FROM audit_events ORDER BY sequence")
        previous_hash = "0" * 64
        for expected_sequence, row in enumerate(rows, 1):
            if row["sequence"] != expected_sequence or row["previous_hash"] != previous_hash:
                return False
            canonical = json.dumps(
                {
                    "sequence": row["sequence"],
                    "occurred_at": row["occurred_at"],
                    "action": row["action"],
                    "actor_id": row["actor_id"],
                    "resource_type": row["resource_type"],
                    "resource_id": row["resource_id"],
                    "result": row["result"],
                    "details": row["details"],
                    "previous_hash": row["previous_hash"],
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            if hashlib.sha256(canonical.encode()).hexdigest() != row["event_hash"]:
                return False
            previous_hash = row["event_hash"]
        return True

    async def export(self, format_name: str = "jsonl") -> str:
        self._ensure_table()
        rows = [
            self._decode(row)
            for row in DatabaseManager.fetchall(
                "SELECT * FROM audit_events ORDER BY sequence"
            )
        ]
        if format_name == "jsonl":
            return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
        if format_name != "csv":
            raise ValueError("Audit export format must be jsonl or csv")
        output = io.StringIO()
        fieldnames = list(rows[0]) if rows else [
            "id",
            "sequence",
            "occurred_at",
            "action",
            "actor_id",
            "resource_type",
            "resource_id",
            "result",
            "details",
            "previous_hash",
            "event_hash",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    @staticmethod
    def _decode(row: dict[str, Any]) -> dict[str, Any]:
        decoded = dict(row)
        decoded["details"] = json.loads(decoded["details"])
        return decoded
