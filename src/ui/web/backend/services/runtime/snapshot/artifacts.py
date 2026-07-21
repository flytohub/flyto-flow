"""
Artifact Collector

Collects and stores execution artifacts (files, screenshots, outputs).
"""

import hashlib
import logging
import mimetypes
import os
import shutil
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from services.runtime.snapshot.models import ArtifactInfo

logger = logging.getLogger(__name__)

# Default artifact storage path
ARTIFACT_STORAGE_PATH = os.environ.get(
    "FLYTO_ARTIFACT_PATH",
    os.path.expanduser("~/.flyto/artifacts")
)


class ArtifactCollector:
    """
    Collects and stores execution artifacts.

    Artifacts are stored in a hierarchical directory structure:
    ~/.flyto/artifacts/{exec_id}/{node_id}/{artifact_name}
    """

    def __init__(self, exec_id: str, storage_path: Optional[str] = None):
        """
        Initialize artifact collector.

        Args:
            exec_id: Execution identifier
            storage_path: Custom storage path (defaults to ARTIFACT_STORAGE_PATH)
        """
        self.exec_id = exec_id
        self.storage_path = Path(storage_path or ARTIFACT_STORAGE_PATH)
        self.exec_dir = self.storage_path / exec_id
        self.artifacts: List[ArtifactInfo] = []

        # Ensure directory exists
        self.exec_dir.mkdir(parents=True, exist_ok=True)

    def add(
        self,
        name: str,
        data: Union[bytes, str, Path],
        mime_type: Optional[str] = None,
        node_id: Optional[str] = None,
        step_index: Optional[int] = None,
    ) -> ArtifactInfo:
        """
        Add an artifact to the collection.

        Args:
            name: Artifact name
            data: Artifact data (bytes, string, or path to file)
            mime_type: MIME type (auto-detected if not provided)
            node_id: Associated node identifier
            step_index: Step index in workflow

        Returns:
            ArtifactInfo describing the stored artifact
        """
        artifact_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()

        # Determine storage location
        if node_id:
            artifact_dir = self.exec_dir / node_id
        else:
            artifact_dir = self.exec_dir
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        safe_name = self._sanitize_filename(name)
        artifact_path = artifact_dir / safe_name

        # Handle different data types
        if isinstance(data, Path):
            # Copy file
            if data.exists():
                shutil.copy2(data, artifact_path)
                content = data.read_bytes()
            else:
                raise FileNotFoundError(f"Artifact source not found: {data}")
        elif isinstance(data, str):
            content = data.encode("utf-8")
            artifact_path.write_bytes(content)
        else:
            content = data
            artifact_path.write_bytes(content)

        # Calculate checksum
        checksum = hashlib.sha256(content).hexdigest()

        # Determine MIME type
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(str(artifact_path))
            if not mime_type:
                mime_type = "application/octet-stream"

        info = ArtifactInfo(
            id=artifact_id,
            name=name,
            mime_type=mime_type,
            size=len(content),
            path=str(artifact_path.relative_to(self.storage_path)),
            checksum=checksum,
            created_at=now,
            node_id=node_id,
            step_index=step_index,
        )

        self.artifacts.append(info)
        logger.debug(f"Stored artifact: {name} ({len(content)} bytes)")

        return info

    def add_screenshot(
        self,
        data: bytes,
        node_id: str,
        step_index: Optional[int] = None,
        suffix: str = "",
    ) -> ArtifactInfo:
        """
        Add a screenshot artifact.

        Args:
            data: Screenshot PNG data
            node_id: Node that generated the screenshot
            step_index: Step index in workflow
            suffix: Optional suffix for the filename (e.g., "error", "after")

        Returns:
            ArtifactInfo describing the stored screenshot
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        name = f"screenshot_{timestamp}"
        if suffix:
            name += f"_{suffix}"
        name += ".png"

        return self.add(
            name=name,
            data=data,
            mime_type="image/png",
            node_id=node_id,
            step_index=step_index,
        )

    def add_output(
        self,
        key: str,
        value: Any,
        node_id: str,
        step_index: Optional[int] = None,
    ) -> Optional[ArtifactInfo]:
        """
        Add an output value as an artifact if it's a file or binary data.

        Args:
            key: Output key name
            value: Output value
            node_id: Node that produced the output
            step_index: Step index in workflow

        Returns:
            ArtifactInfo if artifact was stored, None otherwise
        """
        if isinstance(value, bytes):
            return self.add(
                name=f"{key}.bin",
                data=value,
                node_id=node_id,
                step_index=step_index,
            )
        elif isinstance(value, Path) and value.exists():
            return self.add(
                name=value.name,
                data=value,
                node_id=node_id,
                step_index=step_index,
            )
        return None

    def get_manifest(self) -> List[Dict[str, Any]]:
        """
        Get manifest of all collected artifacts.

        Returns:
            List of artifact info dictionaries
        """
        return [asdict(a) for a in self.artifacts]

    def get_artifact(self, artifact_id: str) -> Optional[ArtifactInfo]:
        """
        Get artifact by ID.

        Args:
            artifact_id: Artifact identifier

        Returns:
            ArtifactInfo if found, None otherwise
        """
        for artifact in self.artifacts:
            if artifact.id == artifact_id:
                return artifact
        return None

    def get_artifact_data(self, artifact_id: str) -> Optional[bytes]:
        """
        Read artifact data by ID.

        Args:
            artifact_id: Artifact identifier

        Returns:
            Artifact bytes if found, None otherwise
        """
        info = self.get_artifact(artifact_id)
        if info:
            full_path = self.storage_path / info.path
            if full_path.exists():
                return full_path.read_bytes()
        return None

    def cleanup(self) -> None:
        """Remove all artifacts for this execution."""
        if self.exec_dir.exists():
            shutil.rmtree(self.exec_dir)
            logger.info(f"Cleaned up artifacts for execution: {self.exec_id}")

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        Sanitize filename for safe storage.

        Args:
            name: Original filename

        Returns:
            Sanitized filename
        """
        # Replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            name = name.replace(char, "_")
        # Limit length
        if len(name) > 200:
            name = name[:200]
        return name

    @classmethod
    def load_from_execution(
        cls, exec_id: str, storage_path: Optional[str] = None
    ) -> "ArtifactCollector":
        """
        Load artifacts from a previous execution.

        Args:
            exec_id: Execution identifier
            storage_path: Custom storage path

        Returns:
            ArtifactCollector with loaded artifacts
        """
        collector = cls(exec_id, storage_path)

        # Scan for existing artifacts
        if collector.exec_dir.exists():
            for artifact_path in collector.exec_dir.rglob("*"):
                if artifact_path.is_file():
                    relative_path = artifact_path.relative_to(collector.storage_path)
                    parts = relative_path.parts

                    # Determine node_id from path structure
                    node_id = None
                    if len(parts) > 2:
                        node_id = parts[1]

                    content = artifact_path.read_bytes()
                    mime_type, _ = mimetypes.guess_type(str(artifact_path))

                    info = ArtifactInfo(
                        id=str(uuid.uuid4())[:8],
                        name=artifact_path.name,
                        mime_type=mime_type or "application/octet-stream",
                        size=len(content),
                        path=str(relative_path),
                        checksum=hashlib.sha256(content).hexdigest(),
                        created_at=datetime.fromtimestamp(
                            artifact_path.stat().st_mtime, tz=timezone.utc
                        ).isoformat(),
                        node_id=node_id,
                    )
                    collector.artifacts.append(info)

        return collector
