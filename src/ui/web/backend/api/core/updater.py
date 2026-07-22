"""Offline flyto-core wheel import endpoint for CE."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from pydantic import BaseModel

from local.core_wheel import (
    MAX_WHEEL_BYTES,
    CoreWheelError,
    get_core_update_dir,
    install_core_wheel,
)


router = APIRouter()


class UpdateResult(BaseModel):
    ok: bool
    message: str
    from_version: str | None
    to_version: str
    sha256: str
    modules_loaded: int
    restart_recommended: bool = True


@router.post("/upload", response_model=UpdateResult)
async def upload_core_package(
    file: UploadFile = File(...),
    expected_sha256: str | None = Header(default=None, alias="X-Flyto-Core-SHA256"),
):
    """Import a flyto-core wheel supplied by the operator; never use a registry."""
    filename = file.filename or ""
    if not filename.lower().endswith(".whl") or "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="A safe .whl filename is required")
    if expected_sha256 and (
        len(expected_sha256) != 64
        or any(character not in "0123456789abcdefABCDEF" for character in expected_sha256)
    ):
        raise HTTPException(status_code=400, detail="X-Flyto-Core-SHA256 must be 64 hex characters")

    from api.core.health import get_installed_version

    previous = get_installed_version()
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="core-upload-", suffix=".whl", dir=get_core_update_dir(), delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            total = 0
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_WHEEL_BYTES:
                    raise CoreWheelError("Wheel exceeds the 256 MiB limit")
                temporary.write(chunk)

        installed = install_core_wheel(temporary_path, expected_sha256)
        from local.core_reload import reload_modules

        modules_loaded, _ = await reload_modules(installed.path)
        return UpdateResult(
            ok=True,
            message=f"Imported flyto-core {installed.version} from local wheel",
            from_version=previous,
            to_version=installed.version,
            sha256=installed.sha256,
            modules_loaded=modules_loaded,
        )
    except (CoreWheelError, OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()
        if temporary_path:
            temporary_path.unlink(missing_ok=True)
