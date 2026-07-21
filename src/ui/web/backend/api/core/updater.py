"""
Core Package Update & Install Endpoints

Handles:
- Update flyto-core from PyPI
- Upload and install .whl file
- Install base package (first-time setup)
"""
import sys
import re
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel

from gateway.auth import get_admin_user
from gateway.config import get_gateway_config
from gateway.providers.base import UserInfo
from api.core.health import get_installed_version
from api.core.plugins import reload_core_modules

logger = logging.getLogger(__name__)

router = APIRouter()


# Allowed filename pattern for .whl files
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+\.whl$')


class UpdateResult(BaseModel):
    """Update operation result"""
    ok: bool
    message: str
    from_version: Optional[str]
    to_version: Optional[str]


def _validate_safe_filename(filename: str) -> None:
    """
    Validate filename to prevent path traversal attacks.

    Args:
        filename: The uploaded filename

    Raises:
        HTTPException 400 if filename is unsafe
    """
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename: path traversal not allowed"
        )

    if not SAFE_FILENAME_PATTERN.match(filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename: only alphanumeric, underscore, hyphen, and dot allowed"
        )


def _check_offline_mode() -> None:
    """Block network package installs when the gateway is fully offline."""
    if get_gateway_config().is_offline:
        raise HTTPException(
            status_code=403,
            detail="Online package updates are disabled in offline mode. Upload a local .whl package instead.",
        )


@router.post("/update", response_model=UpdateResult)
async def update_core_online(
    admin: UserInfo = Depends(get_admin_user),
):
    """
    Update flyto-core from PyPI (requires internet).
    Runs: pip install --upgrade flyto-core

    REQUIRES ADMIN - Only administrators can update packages.
    """
    _check_offline_mode()  # Block in offline mode
    logger.info(f"Package update from PyPI by admin: {admin.email}")

    old_version = get_installed_version()

    try:
        logger.info("Updating flyto-core from PyPI...")

        # Run pip upgrade
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "flyto-core"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            logger.error(f"pip upgrade failed: {result.stderr}")
            return UpdateResult(
                ok=False,
                message=f"Update failed: {result.stderr[:200]}",
                from_version=old_version,
                to_version=None
            )

        new_version = get_installed_version()

        # Reload modules after update
        await reload_core_modules()

        if old_version == new_version:
            return UpdateResult(
                ok=True,
                message=f"Already on latest version: {new_version}",
                from_version=old_version,
                to_version=new_version
            )

        logger.info(f"Updated flyto-core: {old_version} -> {new_version}")
        return UpdateResult(
            ok=True,
            message=f"Updated successfully: {old_version} -> {new_version}",
            from_version=old_version,
            to_version=new_version
        )

    except subprocess.TimeoutExpired:
        return UpdateResult(
            ok=False,
            message="Update timed out. Please try again.",
            from_version=old_version,
            to_version=None
        )
    except Exception as e:
        logger.error(f"Update error: {e}")
        return UpdateResult(
            ok=False,
            message=f"Update error: {str(e)}",
            from_version=old_version,
            to_version=None
        )


@router.post("/upload", response_model=UpdateResult)
async def upload_core_package(
    file: UploadFile = File(...),
    admin: UserInfo = Depends(get_admin_user),
):
    """
    Upload and install flyto-core .whl file.
    Accepts: .whl file upload

    REQUIRES ADMIN - Only administrators can install packages.
    ALWAYS ALLOWED - This is a local operation, works in offline mode.
    """
    logger.info(f"Package upload by admin: {admin.email}")

    # Validate filename for path traversal attacks (SECURITY)
    _validate_safe_filename(file.filename)

    # Validate file extension
    if not file.filename.endswith('.whl'):
        raise HTTPException(
            status_code=400,
            detail="Only .whl files are accepted"
        )

    # Validate filename contains flyto-core or flyto_core
    if 'flyto' not in file.filename.lower():
        raise HTTPException(
            status_code=400,
            detail="File must be a flyto-core package"
        )

    old_version = get_installed_version()

    try:
        # Save uploaded file to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / file.filename

            # Write uploaded file
            content = await file.read()
            with open(temp_path, 'wb') as f:
                f.write(content)

            logger.info(f"Installing uploaded package: {file.filename}")

            # Install with pip
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--force-reinstall", str(temp_path)],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.error(f"pip install failed: {result.stderr}")
                return UpdateResult(
                    ok=False,
                    message=f"Installation failed: {result.stderr[:200]}",
                    from_version=old_version,
                    to_version=None
                )

        new_version = get_installed_version()

        # Reload modules after update
        await reload_core_modules()

        logger.info(f"Installed flyto-core from upload: {old_version} -> {new_version}")
        return UpdateResult(
            ok=True,
            message=f"Installed successfully: {new_version}",
            from_version=old_version,
            to_version=new_version
        )

    except subprocess.TimeoutExpired:
        return UpdateResult(
            ok=False,
            message="Installation timed out. Please try again.",
            from_version=old_version,
            to_version=None
        )
    except Exception as e:
        logger.error(f"Upload install error: {e}")
        return UpdateResult(
            ok=False,
            message=f"Installation error: {str(e)}",
            from_version=old_version,
            to_version=None
        )


@router.post("/install-base")
async def install_base_package(
    admin: UserInfo = Depends(get_admin_user),
):
    """
    Install base flyto-core package from PyPI.
    Used for first-time setup.

    REQUIRES ADMIN - Only administrators can install packages.
    """
    _check_offline_mode()  # Block in offline mode
    logger.info(f"Base package install by admin: {admin.email}")

    installed = get_installed_version()
    if installed:
        return {
            "ok": True,
            "message": f"flyto-core already installed: v{installed}",
            "version": installed
        }

    try:
        logger.info("Installing flyto-core base package...")

        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "flyto-core"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            return {
                "ok": False,
                "message": f"Installation failed: {result.stderr[:200]}",
                "version": None
            }

        version = get_installed_version()
        await reload_core_modules()

        return {
            "ok": True,
            "message": f"Installed flyto-core v{version}",
            "version": version
        }

    except Exception as e:
        return {
            "ok": False,
            "message": str(e),
            "version": None
        }
