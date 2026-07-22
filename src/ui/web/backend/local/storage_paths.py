"""Persistent local data paths shared by Flyto2 Flow services."""

from __future__ import annotations

import os
from pathlib import Path


def data_root() -> Path:
    configured = os.getenv("FLYTO_DATA_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    database = os.getenv("FLYTO_OFFLINE_DB_PATH", "").strip()
    if database:
        return Path(database).expanduser().resolve().parent
    return (Path.home() / ".flyto").resolve()


def evidence_path() -> Path:
    configured = os.getenv("FLYTO_EVIDENCE_PATH", "").strip()
    return Path(configured).expanduser().resolve() if configured else data_root() / "evidence"


def runs_path() -> Path:
    configured = os.getenv("FLYTO_RUNS_PATH", "").strip()
    return Path(configured).expanduser().resolve() if configured else data_root() / "runs"
