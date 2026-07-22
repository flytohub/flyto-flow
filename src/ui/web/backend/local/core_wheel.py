"""Offline-only flyto-core wheel installation and activation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from email.parser import BytesParser
from pathlib import Path, PurePosixPath


MAX_WHEEL_BYTES = 256 * 1024 * 1024
MAX_EXTRACTED_BYTES = 768 * 1024 * 1024
MAX_ARCHIVE_FILES = 30_000
_SAFE_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+!-]*$")


class CoreWheelError(ValueError):
    """The supplied wheel cannot be safely installed as flyto-core."""


@dataclass(frozen=True)
class InstalledCore:
    version: str
    sha256: str
    path: Path


def get_core_update_dir() -> Path:
    configured = os.getenv("FLYTO_CORE_UPDATE_DIR")
    root = Path(configured) if configured else Path.home() / ".flyto" / "core"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _active_record_path() -> Path:
    return get_core_update_dir() / "active.json"


def read_active_core() -> InstalledCore | None:
    record_path = _active_record_path()
    if not record_path.is_file():
        return None
    try:
        payload = json.loads(record_path.read_text(encoding="utf-8"))
        version = str(payload["version"])
        sha256 = str(payload["sha256"])
        path = get_core_update_dir() / version
        if _SAFE_VERSION.fullmatch(version) and (path / "core" / "__init__.py").is_file():
            return InstalledCore(version=version, sha256=sha256, path=path)
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return None


def activate_installed_core() -> InstalledCore | None:
    """Put the persisted offline wheel ahead of the image-bundled baseline."""
    installed = read_active_core()
    if installed and str(installed.path) not in sys.path:
        sys.path.insert(0, str(installed.path))
    return installed


def _wheel_metadata(archive: zipfile.ZipFile) -> tuple[str, str]:
    metadata_names = [
        name for name in archive.namelist()
        if name.endswith(".dist-info/METADATA") and "/" in name
    ]
    if len(metadata_names) != 1:
        raise CoreWheelError("Wheel must contain exactly one dist-info/METADATA file")
    metadata = BytesParser().parsebytes(archive.read(metadata_names[0]))
    name = (metadata.get("Name") or "").strip().lower().replace("_", "-")
    version = (metadata.get("Version") or "").strip()
    if name != "flyto-core":
        raise CoreWheelError("Wheel package name must be flyto-core")
    if not _SAFE_VERSION.fullmatch(version):
        raise CoreWheelError("Wheel contains an invalid version")
    return name, version


def _validate_member(member: zipfile.ZipInfo) -> PurePosixPath:
    path = PurePosixPath(member.filename)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise CoreWheelError("Wheel contains an unsafe path")
    unix_mode = member.external_attr >> 16
    if unix_mode and stat.S_ISLNK(unix_mode):
        raise CoreWheelError("Wheel symbolic links are not allowed")
    return path


def _preflight_import(version_dir: Path) -> None:
    code = "import sys; sys.path.insert(0, sys.argv[1]); import core"
    result = subprocess.run(
        [sys.executable, "-c", code, str(version_dir)],
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, "PIP_NO_INDEX": "1"},
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-500:]
        raise CoreWheelError(f"flyto-core import check failed: {detail}")


def install_core_wheel(wheel_path: Path, expected_sha256: str | None = None) -> InstalledCore:
    """Validate and install a local wheel without invoking pip or the network."""
    if wheel_path.stat().st_size > MAX_WHEEL_BYTES:
        raise CoreWheelError("Wheel exceeds the 256 MiB limit")

    digest = hashlib.sha256(wheel_path.read_bytes()).hexdigest()
    if expected_sha256 and digest.lower() != expected_sha256.strip().lower():
        raise CoreWheelError("Wheel SHA-256 does not match the supplied digest")

    update_dir = get_core_update_dir()
    with zipfile.ZipFile(wheel_path) as archive:
        if len(archive.infolist()) > MAX_ARCHIVE_FILES:
            raise CoreWheelError("Wheel contains too many files")
        _, version = _wheel_metadata(archive)
        target = update_dir / version
        if target.exists():
            raise CoreWheelError(f"flyto-core {version} is already installed")

        core_members = []
        extracted_bytes = 0
        for member in archive.infolist():
            member_path = _validate_member(member)
            if member_path.parts[0] != "core":
                continue
            extracted_bytes += member.file_size
            if extracted_bytes > MAX_EXTRACTED_BYTES:
                raise CoreWheelError("Wheel expands beyond the 768 MiB limit")
            core_members.append((member, member_path))

        if not any(path == PurePosixPath("core/__init__.py") for _, path in core_members):
            raise CoreWheelError("Wheel does not contain core/__init__.py")

        with tempfile.TemporaryDirectory(prefix=".core-wheel-", dir=update_dir) as temp_dir:
            staging = Path(temp_dir) / version
            for member, member_path in core_members:
                destination = staging.joinpath(*member_path.parts)
                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, destination.open("wb") as output:
                    while chunk := source.read(1024 * 1024):
                        output.write(chunk)
            _preflight_import(staging)
            os.replace(staging, target)

    record = InstalledCore(version=version, sha256=digest, path=target)
    record_path = _active_record_path()
    temporary_record = record_path.with_suffix(".tmp")
    temporary_record.write_text(
        json.dumps({"version": version, "sha256": digest}, sort_keys=True),
        encoding="utf-8",
    )
    os.replace(temporary_record, record_path)
    activate_installed_core()
    return record
