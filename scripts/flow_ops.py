#!/usr/bin/env python3
"""Offline operator CLI for backup, verification, and restore."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src/ui/web/backend"
sys.path.insert(0, str(BACKEND))

from services.operations.backup import create_backup, restore_backup, verify_backup


def main() -> int:
    parser = argparse.ArgumentParser(prog="flow-ops")
    commands = parser.add_subparsers(dest="command", required=True)

    backup = commands.add_parser("backup")
    backup.add_argument("--data-dir", type=Path, required=True)
    backup.add_argument("--output", type=Path, required=True)

    verify = commands.add_parser("verify-backup")
    verify.add_argument("archive", type=Path)

    restore = commands.add_parser("restore")
    restore.add_argument("archive", type=Path)
    restore.add_argument("--data-dir", type=Path, required=True)
    restore.add_argument("--overwrite", action="store_true")

    audit = commands.add_parser("export-audit")
    audit.add_argument("--database", type=Path, required=True)
    audit.add_argument("--format", choices=("jsonl", "csv"), default="jsonl")
    audit.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "backup":
        manifest = create_backup(args.data_dir, args.output)
    elif args.command == "verify-backup":
        manifest = verify_backup(args.archive)
    elif args.command == "restore":
        manifest = restore_backup(
            args.archive,
            args.data_dir,
            allow_overwrite=args.overwrite,
        )
    else:
        import asyncio
        import os

        os.environ["FLYTO_EXECUTION_DB_PATH"] = str(args.database)
        from gateway.providers.audit.local import LocalAuditProvider

        provider = LocalAuditProvider()
        if not asyncio.run(provider.verify_chain()):
            raise RuntimeError("Audit chain verification failed; export refused")
        exported = asyncio.run(provider.export(args.format))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(exported, encoding="utf-8")
        print(f"Exported audit log to {args.output}")
        return 0
    print(manifest.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
