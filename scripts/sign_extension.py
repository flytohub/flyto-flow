#!/usr/bin/env python3
"""Generate Ed25519 extension keys and sign Flyto2 extension manifests."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src/ui/web/backend"
sys.path.insert(0, str(BACKEND))

from services.extensions.manifest import (
    ExtensionKind,
    ExtensionManifest,
    _canonical_payload,
)
from services.extensions.templates import load_template_pack


def _write_new_file(path: Path, value: bytes, *, force: bool, mode: int) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if force else os.O_EXCL)
    descriptor = os.open(path, flags, mode)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(value)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    os.chmod(path, mode)


def generate_key(
    private_key_path: Path,
    public_key_path: Path,
    *,
    force: bool,
) -> str:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    encoded_public_key = base64.b64encode(public_bytes).decode("ascii")
    _write_new_file(private_key_path, private_bytes, force=force, mode=0o600)
    try:
        _write_new_file(
            public_key_path,
            f"{encoded_public_key}\n".encode("ascii"),
            force=force,
            mode=0o644,
        )
    except Exception:
        private_key_path.resolve().unlink(missing_ok=True)
        raise
    return encoded_public_key


def _refresh_artifact_digests(
    manifest_path: Path,
    data: dict[str, Any],
) -> dict[str, Any]:
    root = manifest_path.parent.resolve()
    refreshed = dict(data)
    refreshed.pop("signature", None)
    artifacts = []
    for artifact in refreshed.get("artifacts", []):
        artifact_path = (root / artifact["path"]).resolve()
        if root not in artifact_path.parents or not artifact_path.is_file():
            raise ValueError(f"Extension artifact is missing or unsafe: {artifact['path']}")
        if (root / artifact["path"]).is_symlink():
            raise ValueError(f"Extension artifacts must not be symlinks: {artifact['path']}")
        digest = hashlib.sha256()
        with artifact_path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        updated = dict(artifact)
        updated["sha256"] = digest.hexdigest()
        artifacts.append(updated)
    refreshed["artifacts"] = artifacts
    return refreshed


def sign_manifest(manifest_path: Path, private_key_path: Path, key_id: str) -> str:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    manifest_path = manifest_path.resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Extension manifest must contain a JSON object")
    data = _refresh_artifact_digests(manifest_path, data)
    private_key = serialization.load_pem_private_key(
        private_key_path.resolve().read_bytes(),
        password=None,
    )
    if not isinstance(private_key, Ed25519PrivateKey):
        raise ValueError("The signing key must be an Ed25519 private key")
    signature = base64.b64encode(
        private_key.sign(_canonical_payload(data))
    ).decode("ascii")
    data["signature"] = {
        "algorithm": "ed25519",
        "key_id": key_id,
        "value": signature,
    }
    manifest = ExtensionManifest.model_validate(data)
    if manifest.kind == ExtensionKind.TEMPLATE_PACK:
        load_template_pack(manifest_path.parent / manifest.artifacts[0].path)

    descriptor, temporary_name = tempfile.mkstemp(
        dir=manifest_path.parent,
        prefix=f".{manifest_path.name}.",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, manifest_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return signature


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate-key")
    generate_parser.add_argument("--private-key", type=Path, required=True)
    generate_parser.add_argument("--public-key", type=Path, required=True)
    generate_parser.add_argument("--force", action="store_true")

    sign_parser = subparsers.add_parser("sign")
    sign_parser.add_argument("manifest", type=Path)
    sign_parser.add_argument("--private-key", type=Path, required=True)
    sign_parser.add_argument("--key-id", required=True)

    args = parser.parse_args()
    try:
        if args.command == "generate-key":
            public_key = generate_key(
                args.private_key,
                args.public_key,
                force=args.force,
            )
            print(f"Generated private key: {args.private_key.resolve()}")
            print(f"Generated public key: {args.public_key.resolve()}")
            print(f"Trusted key value: {public_key}")
        else:
            sign_manifest(args.manifest, args.private_key, args.key_id)
            print(f"Signed extension manifest: {args.manifest.resolve()}")
    except Exception as exc:
        print(f"Extension signing failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
