"""
Utility endpoints for the Local Runner.

browse-path: Opens native OS file/folder dialog.
"""
import asyncio
import platform
import logging

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utils", tags=["Utils"])


@router.get("/browse-path")
async def browse_path(mode: str = Query(default="directory", pattern="^(file|directory)$")):
    """Open a native OS file/folder picker dialog and return the selected path."""
    try:
        path = await _open_native_dialog(mode)
        if path:
            return {"ok": True, "path": path}
        return {"ok": False, "error": "No path selected"}
    except Exception as e:
        logger.warning(f"browse-path failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)},
        )


async def _open_native_dialog(mode: str) -> str:
    system = platform.system()
    if system == "Darwin":
        return await _macos_dialog(mode)
    # Fallback: tkinter (Linux / Windows) — run in thread to avoid blocking
    try:
        return await asyncio.to_thread(_tkinter_dialog, mode)
    except Exception:
        return ""


async def _macos_dialog(mode: str) -> str:
    if mode == "file":
        script = 'POSIX path of (choose file)'
    else:
        script = 'POSIX path of (choose folder)'
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=5,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
        if proc.returncode == 0:
            return stdout.decode().strip()
    except Exception:
        pass
    return ""


def _tkinter_dialog(mode: str) -> str:
    """Open a tkinter file/folder dialog and return the selected path."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if mode == "file":
        path = filedialog.askopenfilename()
    else:
        path = filedialog.askdirectory()
    root.destroy()
    return path or ""
