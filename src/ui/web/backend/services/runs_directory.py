"""
Runs Directory Service

Manages ~/.flyto/runs/ directory structure for execution artifacts.
Each execution gets its own directory with manifest, step logs, and results.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.runtime.snapshot import ExecutionSnapshot

logger = logging.getLogger(__name__)


class RunsDirectory:
    """
    Manages execution run directories.

    Directory structure:
        ~/.flyto/runs/{date}-{exec_id[:8]}/
            manifest.json    # Full execution snapshot
            steps.jsonl      # Append-only step log
            result.json      # Final outcome
    """

    DEFAULT_BASE_PATH = Path.home() / ".flyto" / "runs"

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize runs directory manager.

        Args:
            base_path: Base path for runs. Defaults to ~/.flyto/runs/
        """
        self._base_path = base_path or self.DEFAULT_BASE_PATH
        self._run_dirs: Dict[str, Path] = {}
        self._lock = asyncio.Lock()

    @property
    def base_path(self) -> Path:
        """Get the base path for runs."""
        return self._base_path

    def _get_run_dir_name(self, exec_id: str) -> str:
        """
        Generate run directory name.

        Format: {YYYYMMDD}-{exec_id[:8]}
        """
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        short_id = exec_id[:8]
        return f"{date_str}-{short_id}"

    async def create_run_directory(self, exec_id: str) -> Path:
        """
        Create a new run directory for an execution.

        Args:
            exec_id: Execution identifier

        Returns:
            Path to the created run directory
        """
        async with self._lock:
            if exec_id in self._run_dirs:
                return self._run_dirs[exec_id]

            dir_name = self._get_run_dir_name(exec_id)
            run_dir = self._base_path / dir_name

            # Handle collision with counter
            counter = 0
            original_dir = run_dir
            while run_dir.exists():
                counter += 1
                run_dir = Path(f"{original_dir}-{counter}")

            # Create directory
            run_dir.mkdir(parents=True, exist_ok=True)

            self._run_dirs[exec_id] = run_dir
            logger.info(f"Created run directory: {run_dir}")

            return run_dir

    def get_run_directory(self, exec_id: str) -> Optional[Path]:
        """
        Get existing run directory for an execution.

        Args:
            exec_id: Execution identifier

        Returns:
            Path to run directory or None if not found
        """
        return self._run_dirs.get(exec_id)

    async def write_manifest(
        self,
        exec_id: str,
        snapshot: "ExecutionSnapshot",
    ) -> Path:
        """
        Write execution manifest to run directory.

        Args:
            exec_id: Execution identifier
            snapshot: Execution snapshot to write

        Returns:
            Path to manifest file
        """
        run_dir = self._run_dirs.get(exec_id)
        if not run_dir:
            run_dir = await self.create_run_directory(exec_id)

        manifest_path = run_dir / "manifest.json"

        # Write manifest
        manifest_data = snapshot.to_dict()
        await self._write_json(manifest_path, manifest_data)

        logger.debug(f"Wrote manifest: {manifest_path}")
        return manifest_path

    async def append_step_log(
        self,
        exec_id: str,
        entry: Dict[str, Any],
    ) -> None:
        """
        Append entry to step log (JSONL format).

        Args:
            exec_id: Execution identifier
            entry: Step log entry to append
        """
        run_dir = self._run_dirs.get(exec_id)
        if not run_dir:
            logger.warning(f"Run directory not found for {exec_id}")
            return

        steps_path = run_dir / "steps.jsonl"

        # Add timestamp if not present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Append to JSONL file
        line = json.dumps(entry, default=str) + "\n"

        await self._append_file(steps_path, line)

    async def write_result(
        self,
        exec_id: str,
        result: Dict[str, Any],
    ) -> Path:
        """
        Write final execution result.

        Args:
            exec_id: Execution identifier
            result: Execution result with outcome classification

        Returns:
            Path to result file
        """
        run_dir = self._run_dirs.get(exec_id)
        if not run_dir:
            run_dir = await self.create_run_directory(exec_id)

        result_path = run_dir / "result.json"

        # Add timestamp
        if "completed_at" not in result:
            result["completed_at"] = datetime.now(timezone.utc).isoformat()

        await self._write_json(result_path, result)

        logger.info(f"Wrote result: {result_path}")
        return result_path

    async def read_manifest(self, exec_id: str) -> Optional[Dict[str, Any]]:
        """
        Read manifest from run directory.

        Args:
            exec_id: Execution identifier

        Returns:
            Manifest data or None if not found
        """
        run_dir = self._run_dirs.get(exec_id)
        if not run_dir:
            return None

        manifest_path = run_dir / "manifest.json"
        if not manifest_path.exists():
            return None

        return await self._read_json(manifest_path)

    async def read_step_logs(self, exec_id: str) -> list:
        """
        Read all step log entries.

        Args:
            exec_id: Execution identifier

        Returns:
            List of step log entries
        """
        run_dir = self._run_dirs.get(exec_id)
        if not run_dir:
            return []

        steps_path = run_dir / "steps.jsonl"
        if not steps_path.exists():
            return []

        entries = []
        try:
            content = await self._read_file(steps_path)
            for line in content.splitlines():
                if line.strip():
                    entries.append(json.loads(line))
        except Exception as e:
            logger.warning(f"Failed to read step logs: {e}")

        return entries

    async def cleanup_old_runs(self, max_age_days: int = 30) -> int:
        """
        Remove run directories older than specified days.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of directories removed
        """
        import shutil
        from datetime import timedelta

        if not self._base_path.exists():
            return 0

        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        removed = 0

        for run_dir in self._base_path.iterdir():
            if not run_dir.is_dir():
                continue

            try:
                # Parse date from directory name (YYYYMMDD-...)
                date_str = run_dir.name[:8]
                dir_date = datetime.strptime(date_str, "%Y%m%d").replace(
                    tzinfo=timezone.utc
                )

                if dir_date < cutoff:
                    shutil.rmtree(run_dir)
                    removed += 1
                    logger.info(f"Removed old run directory: {run_dir}")

            except (ValueError, OSError) as e:
                logger.debug(f"Skipping directory {run_dir}: {e}")

        return removed

    # =========================================================================
    # Private file I/O methods (async-safe)
    # =========================================================================

    async def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        """Write JSON data to file."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: path.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8",
            ),
        )

    async def _read_json(self, path: Path) -> Dict[str, Any]:
        """Read JSON data from file."""
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            None,
            lambda: path.read_text(encoding="utf-8"),
        )
        return json.loads(content)

    async def _append_file(self, path: Path, content: str) -> None:
        """Append content to file."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: path.open("a", encoding="utf-8").write(content),
        )

    async def _read_file(self, path: Path) -> str:
        """Read file content."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: path.read_text(encoding="utf-8"),
        )


# Module-level singleton
_runs_directory: Optional[RunsDirectory] = None


def get_runs_directory() -> RunsDirectory:
    """Get the singleton runs directory instance."""
    global _runs_directory
    if _runs_directory is None:
        _runs_directory = RunsDirectory()
        logger.info(f"Created RunsDirectory at {_runs_directory.base_path}")
    return _runs_directory
