"""
File Log Stream

Local file output implementation for log streaming.
Supports JSON, NDJSON, and plain text formats with rotation.
"""

import asyncio
import gzip
import json
import logging
import os
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from services.observability.log_streaming.interface import LogEvent, LogStreamInterface, StreamConfig

logger = logging.getLogger(__name__)


@dataclass
class FileConfig(StreamConfig):
    """File stream configuration."""
    file_path: str = "/var/log/flyto/audit.log"
    format: str = "ndjson"  # ndjson, json, text, ecs
    rotate_size_mb: int = 100
    rotate_count: int = 5
    compress_rotated: bool = True
    create_dirs: bool = True
    buffer_writes: bool = True
    sync_interval_seconds: float = 1.0


class FileStream(LogStreamInterface):
    """
    Local file log stream.

    Features:
    - Multiple output formats (NDJSON, JSON array, plain text, ECS)
    - Size-based rotation with compression
    - Async file I/O with buffering
    - Automatic directory creation
    """

    def __init__(
        self,
        file_path: str = "/var/log/flyto/audit.log",
        config: Optional[FileConfig] = None,
        **kwargs,
    ):
        """
        Initialize file stream.

        Args:
            file_path: Output file path
            config: Stream configuration
            **kwargs: Additional config options
        """
        if config is None:
            config = FileConfig(file_path=file_path, **kwargs)
        else:
            config.file_path = file_path

        super().__init__(config)
        self.file_config = config
        self._buffer: deque = deque(maxlen=config.batch_size * 2)
        self._file: Optional[aiofiles.threadpool.binary.AsyncBufferedIOBase] = None
        self._lock = asyncio.Lock()
        self._bytes_written = 0
        self._sync_task: Optional[asyncio.Task] = None

    async def _ensure_directory(self) -> bool:
        """
        Ensure output directory exists.

        Returns:
            True if directory exists or was created
        """
        try:
            path = Path(self.file_config.file_path)
            parent = path.parent

            if not parent.exists():
                if self.file_config.create_dirs:
                    parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {parent}")
                else:
                    logger.error(f"Directory does not exist: {parent}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error creating directory: {e}")
            return False

    async def _open_file(self) -> bool:
        """
        Open output file.

        Returns:
            True if file is open
        """
        if self._file is not None:
            return True

        if not await self._ensure_directory():
            return False

        try:
            self._file = await aiofiles.open(
                self.file_config.file_path,
                mode="a",
            )
            self._bytes_written = os.path.getsize(self.file_config.file_path)

            # Start sync task
            if self.file_config.buffer_writes:
                self._sync_task = asyncio.create_task(self._periodic_sync())

            logger.info(f"Opened log file: {self.file_config.file_path}")
            return True

        except Exception as e:
            logger.error(f"Error opening file: {e}")
            return False

    async def _close_file(self) -> None:
        """Close output file."""
        try:
            if self._sync_task:
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass

            if self._file:
                await self._file.close()
                self._file = None

        except Exception as e:
            logger.warning(f"Error closing file: {e}")

    async def _periodic_sync(self) -> None:
        """Periodically sync file to disk."""
        while True:
            try:
                await asyncio.sleep(self.file_config.sync_interval_seconds)
                if self._file:
                    await self._file.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Error syncing file: {e}")

    async def _check_rotation(self) -> None:
        """Check if rotation is needed and perform it."""
        max_bytes = self.file_config.rotate_size_mb * 1024 * 1024

        if self._bytes_written < max_bytes:
            return

        await self._rotate()

    async def _rotate(self) -> None:
        """Rotate log files."""
        async with self._lock:
            await self._close_file()

            try:
                base_path = self.file_config.file_path

                # Shift existing rotated files
                for i in range(self.file_config.rotate_count - 1, 0, -1):
                    old_name = f"{base_path}.{i}"
                    new_name = f"{base_path}.{i + 1}"

                    if self.file_config.compress_rotated:
                        old_name += ".gz"
                        new_name += ".gz"

                    if os.path.exists(old_name):
                        if i + 1 >= self.file_config.rotate_count:
                            os.remove(old_name)
                        else:
                            os.rename(old_name, new_name)

                # Rotate current file
                if os.path.exists(base_path):
                    rotated_name = f"{base_path}.1"

                    if self.file_config.compress_rotated:
                        # Compress to .gz
                        gz_name = f"{rotated_name}.gz"
                        with open(base_path, "rb") as f_in:
                            with gzip.open(gz_name, "wb") as f_out:
                                f_out.writelines(f_in)
                        os.remove(base_path)
                    else:
                        os.rename(base_path, rotated_name)

                logger.info(f"Rotated log file: {base_path}")

            except Exception as e:
                logger.error(f"Error rotating file: {e}")

            # Reopen file
            self._bytes_written = 0
            await self._open_file()

    def _format_event(self, event: LogEvent) -> str:
        """
        Format event based on configured format.

        Args:
            event: Log event

        Returns:
            Formatted string
        """
        fmt = self.file_config.format

        if fmt == "ndjson":
            return json.dumps(event.to_dict(), ensure_ascii=False)

        elif fmt == "json":
            return json.dumps(event.to_dict(), ensure_ascii=False, indent=2)

        elif fmt == "ecs":
            return json.dumps(event.to_ecs(), ensure_ascii=False)

        elif fmt == "text":
            return (
                f"[{event.timestamp}] [{event.level.name}] "
                f"[{event.category.value}] {event.message}"
            )

        else:
            return json.dumps(event.to_dict(), ensure_ascii=False)

    async def push(self, event: LogEvent) -> bool:
        """
        Push a single log event.

        Args:
            event: Log event to push

        Returns:
            True if successfully pushed
        """
        try:
            if not await self._open_file():
                return False

            line = self._format_event(event) + "\n"
            line_bytes = len(line.encode("utf-8"))

            async with self._lock:
                await self._file.write(line)
                self._bytes_written += line_bytes

            await self._check_rotation()
            return True

        except Exception as e:
            logger.error(f"Error writing to file: {e}")
            return False

    async def push_batch(self, events: List[LogEvent]) -> int:
        """
        Push a batch of log events.

        Args:
            events: List of log events

        Returns:
            Number of successfully pushed events
        """
        if not events:
            return 0

        try:
            if not await self._open_file():
                return 0

            lines = [self._format_event(e) + "\n" for e in events]
            content = "".join(lines)
            content_bytes = len(content.encode("utf-8"))

            async with self._lock:
                await self._file.write(content)
                self._bytes_written += content_bytes

            await self._check_rotation()
            return len(events)

        except Exception as e:
            logger.error(f"Error writing batch to file: {e}")
            return 0

    async def flush(self) -> int:
        """
        Flush any buffered events.

        Returns:
            Number of flushed events
        """
        async with self._lock:
            if not self._buffer:
                if self._file:
                    await self._file.flush()
                return 0

            events = list(self._buffer)
            self._buffer.clear()

        count = await self.push_batch(events)

        if self._file:
            await self._file.flush()

        return count

    async def health_check(self) -> Dict[str, Any]:
        """
        Check file stream health.

        Returns:
            Health status dict
        """
        try:
            path = Path(self.file_config.file_path)

            # Check if directory is writable
            parent = path.parent
            if parent.exists():
                writable = os.access(parent, os.W_OK)
            else:
                writable = False

            # Get file info
            file_info = {}
            if path.exists():
                stat = path.stat()
                file_info = {
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                }

            return {
                "healthy": writable,
                "file_path": self.file_config.file_path,
                "writable": writable,
                "file_exists": path.exists(),
                "bytes_written_session": self._bytes_written,
                **file_info,
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "file_path": self.file_config.file_path,
            }

    async def close(self) -> None:
        """Close the stream and cleanup resources."""
        await self.flush()
        await self._close_file()
        logger.info(f"File stream closed: {self.file_config.file_path}")

    async def get_recent_logs(
        self,
        limit: int = 100,
        level_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Read recent logs from file.

        Args:
            limit: Maximum number of logs to return
            level_filter: Optional level filter

        Returns:
            List of log events
        """
        try:
            path = Path(self.file_config.file_path)
            if not path.exists():
                return []

            logs = []

            async with aiofiles.open(path, "r") as f:
                lines = await f.readlines()

                # Read from end
                for line in reversed(lines[-limit * 2:]):
                    try:
                        if self.file_config.format in ("ndjson", "ecs"):
                            event = json.loads(line.strip())

                            if level_filter:
                                event_level = event.get("level", "").lower()
                                if event_level != level_filter.lower():
                                    continue

                            logs.append(event)

                            if len(logs) >= limit:
                                break

                    except json.JSONDecodeError:
                        continue

            return logs

        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return []
