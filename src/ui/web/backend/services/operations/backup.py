"""Verified, version-aware backups for the local Flyto2 Flow data plane."""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from config.version import APP_VERSION
from gateway.storage.database import EXECUTION_SCHEMA_VERSION
from gateway.storage.offline_db import OFFLINE_SCHEMA_VERSION


BACKUP_SCHEMA = "flyto.flow-backup.v1"
DATABASE_NAMES = ("offline.db", "executions.db")
MAX_MANIFEST_BYTES = 1024 * 1024
DEFAULT_MAX_BACKUP_BYTES = 10 * 1024 * 1024 * 1024
SUPPORTED_SCHEMA_VERSIONS = {
    "offline.db": {"offline": OFFLINE_SCHEMA_VERSION},
    "executions.db": {"execution": EXECUTION_SCHEMA_VERSION},
}


class BackupFile(BaseModel):
    path: Literal["offline.db", "executions.db"]
    size: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    schema_versions: dict[str, int] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True, extra="forbid")


class BackupManifest(BaseModel):
    schema_name: Literal["flyto.flow-backup.v1"] = Field(alias="schema")
    app_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    minimum_compatible_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    created_at: str
    files: tuple[BackupFile, ...] = Field(min_length=1)

    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _schema_versions(path: Path) -> dict[str, int]:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT namespace, MAX(version) AS version "
            "FROM schema_migrations GROUP BY namespace"
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    finally:
        connection.close()
    return {row["namespace"]: int(row["version"] or 0) for row in rows}


def _copy_sqlite(source: Path, destination: Path) -> None:
    source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    destination_connection = sqlite3.connect(destination)
    try:
        source_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        source_connection.close()


def create_backup(data_dir: Path, destination: Path) -> BackupManifest:
    """Create a consistent archive without copying WAL files directly."""
    data_dir = data_dir.expanduser().resolve()
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Backup already exists: {destination}")

    with tempfile.TemporaryDirectory(prefix="flyto-flow-backup-") as temporary:
        staging = Path(temporary)
        files: list[BackupFile] = []
        for name in DATABASE_NAMES:
            source = data_dir / name
            if not source.is_file():
                continue
            copied = staging / name
            _copy_sqlite(source, copied)
            files.append(
                BackupFile(
                    path=name,
                    size=copied.stat().st_size,
                    sha256=_sha256(copied),
                    schema_versions=_schema_versions(copied),
                )
            )
        if not files:
            raise FileNotFoundError(f"No Flyto2 Flow databases found in {data_dir}")

        manifest = BackupManifest(
            schema=BACKUP_SCHEMA,
            app_version=APP_VERSION,
            minimum_compatible_version=_compatibility_floor(APP_VERSION),
            created_at=datetime.now(timezone.utc).isoformat(),
            files=tuple(files),
        )
        (staging / "manifest.json").write_text(
            manifest.model_dump_json(indent=2, by_alias=True) + "\n",
            encoding="utf-8",
        )
        temporary_file = tempfile.NamedTemporaryFile(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            delete=False,
        )
        temporary_archive = Path(temporary_file.name)
        temporary_file.close()
        try:
            with tarfile.open(temporary_archive, "w:gz") as archive:
                archive.add(staging / "manifest.json", arcname="manifest.json")
                for file in files:
                    archive.add(staging / file.path, arcname=file.path)
            os.link(temporary_archive, destination)
        finally:
            temporary_archive.unlink(missing_ok=True)
    return manifest


def _safe_members(archive: tarfile.TarFile) -> dict[str, tarfile.TarInfo]:
    members = archive.getmembers()
    allowed = {"manifest.json", *DATABASE_NAMES}
    by_name: dict[str, tarfile.TarInfo] = {}
    for member in members:
        if member.name not in allowed or not member.isfile():
            raise ValueError(f"Unsafe or unexpected backup member: {member.name}")
        if member.name in by_name:
            raise ValueError(f"Duplicate backup member: {member.name}")
        by_name[member.name] = member
    if "manifest.json" not in by_name:
        raise ValueError("Backup manifest is missing")
    return by_name


def _semver(version: str) -> tuple[int, int, int]:
    try:
        parts = tuple(int(part) for part in version.split("."))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid backup version: {version!r}") from exc
    if len(parts) != 3 or any(part < 0 for part in parts):
        raise ValueError(f"Invalid backup version: {version!r}")
    return parts


def _compatibility_floor(version: str) -> str:
    major, minor, _patch = _semver(version)
    return f"{major}.{minor if major == 0 else 0}.0"


def _extract_backup(archive_path: Path, staging: Path) -> BackupManifest:
    max_bytes = int(
        os.environ.get("FLYTO_BACKUP_MAX_BYTES", str(DEFAULT_MAX_BACKUP_BYTES))
    )
    if max_bytes < 1:
        raise ValueError("FLYTO_BACKUP_MAX_BYTES must be positive")
    with tarfile.open(archive_path, "r:gz") as archive:
        members = _safe_members(archive)
        manifest_member = members["manifest.json"]
        if manifest_member.size > MAX_MANIFEST_BYTES:
            raise ValueError("Backup manifest is too large")
        manifest_stream = archive.extractfile(manifest_member)
        if manifest_stream is None:
            raise ValueError("Backup manifest cannot be read")
        manifest = BackupManifest.model_validate_json(
            manifest_stream.read(MAX_MANIFEST_BYTES + 1)
        )
        expected_names = {"manifest.json", *(file.path for file in manifest.files)}
        if set(members) != expected_names:
            raise ValueError("Backup members do not match the manifest")
        if len({file.path for file in manifest.files}) != len(manifest.files):
            raise ValueError("Backup manifest contains duplicate files")
        total_size = sum(file.size for file in manifest.files)
        if total_size > max_bytes:
            raise ValueError("Backup exceeds FLYTO_BACKUP_MAX_BYTES")

        (staging / "manifest.json").write_bytes(
            manifest.model_dump_json(indent=2, by_alias=True).encode() + b"\n"
        )
        for expected in manifest.files:
            member = members[expected.path]
            if member.size != expected.size:
                raise ValueError(f"Backup member size mismatch: {expected.path}")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"Backup member cannot be read: {expected.path}")
            with (staging / expected.path).open("xb") as destination:
                shutil.copyfileobj(source, destination, length=1024 * 1024)
    return manifest


def _verify_extracted(staging: Path, manifest: BackupManifest) -> None:
    if manifest.schema_name != BACKUP_SCHEMA:
        raise ValueError(f"Unsupported backup schema: {manifest.schema_name}")
    current = _semver(APP_VERSION)
    backup = _semver(manifest.app_version)
    minimum = _semver(manifest.minimum_compatible_version)
    if current < minimum:
        raise ValueError(
            f"Backup requires Flyto2 Flow {manifest.minimum_compatible_version} or newer"
        )
    if backup > current:
        raise ValueError(
            f"Backup version {manifest.app_version} is newer than {APP_VERSION}"
        )
    if _compatibility_floor(manifest.app_version) != _compatibility_floor(APP_VERSION):
        raise ValueError(
            f"Backup version {manifest.app_version} is incompatible with {APP_VERSION}"
        )
    for expected in manifest.files:
        path = staging / expected.path
        if not path.is_file() or path.stat().st_size != expected.size:
            raise ValueError(f"Backup file size mismatch: {expected.path}")
        if _sha256(path) != expected.sha256:
            raise ValueError(f"Backup digest mismatch: {expected.path}")
        supported = SUPPORTED_SCHEMA_VERSIONS.get(expected.path, {})
        for namespace, version in expected.schema_versions.items():
            if namespace not in supported or version > supported[namespace]:
                raise ValueError(
                    f"Backup schema {expected.path}/{namespace} v{version} "
                    "is newer than this runtime"
                )
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError(f"SQLite integrity check failed: {expected.path}")
        finally:
            connection.close()


def verify_backup(archive_path: Path) -> BackupManifest:
    archive_path = archive_path.expanduser().resolve()
    with tempfile.TemporaryDirectory(prefix="flyto-flow-verify-") as temporary:
        staging = Path(temporary)
        manifest = _extract_backup(archive_path, staging)
        _verify_extracted(staging, manifest)
        return manifest


def restore_backup(
    archive_path: Path,
    data_dir: Path,
    *,
    allow_overwrite: bool = False,
) -> BackupManifest:
    """Restore verified databases. The service must be stopped first."""
    archive_path = archive_path.expanduser().resolve()
    data_dir = data_dir.expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="flyto-flow-restore-") as temporary:
        staging = Path(temporary)
        manifest = _extract_backup(archive_path, staging)
        _verify_extracted(staging, manifest)
        conflicts = [
            file.path for file in manifest.files if (data_dir / file.path).exists()
        ]
        if conflicts and not allow_overwrite:
            raise FileExistsError(
                "Restore target already contains: " + ", ".join(conflicts)
            )

        staged_targets: dict[Path, Path] = {}
        for file in manifest.files:
            source = staging / file.path
            target = data_dir / file.path
            temporary_target = target.with_suffix(target.suffix + ".restore")
            shutil.copy2(source, temporary_target)
            staged_targets[target] = temporary_target

        replaced: list[tuple[Path, Path | None]] = []
        try:
            for target, temporary_target in staged_targets.items():
                previous = target.with_suffix(target.suffix + ".restore-previous")
                if target.exists():
                    previous.unlink(missing_ok=True)
                    target.replace(previous)
                else:
                    previous = None
                replaced.append((target, previous))
                temporary_target.replace(target)
        except Exception:
            for target, previous in reversed(replaced):
                target.unlink(missing_ok=True)
                if previous is not None and previous.exists():
                    previous.replace(target)
            raise
        finally:
            for temporary_target in staged_targets.values():
                temporary_target.unlink(missing_ok=True)
        for _target, previous in replaced:
            if previous is not None:
                previous.unlink(missing_ok=True)
    return manifest
