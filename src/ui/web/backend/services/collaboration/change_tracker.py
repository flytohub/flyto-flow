"""
Change Tracker

Tracks and audits changes made during collaboration sessions.

Features:
- Change history
- Diff generation
- Attribution tracking
- Rollback support
"""

import difflib
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Types of changes."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RENAME = "rename"
    MOVE = "move"
    REORDER = "reorder"


@dataclass
class Change:
    """A single tracked change."""
    change_id: str
    change_type: ChangeType
    path: List[str]
    old_value: Any = None
    new_value: Any = None
    user_id: str = ""
    user_name: str = ""
    timestamp: str = ""
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default timestamp and generate change ID if missing."""
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.change_id:
            self.change_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique change ID."""
        content = f"{self.user_id}:{self.timestamp}:{self.change_type}:{self.path}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize change to dictionary."""
        return {
            "change_id": self.change_id,
            "change_type": self.change_type.value,
            "path": self.path,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Change":
        """Deserialize change from dictionary."""
        return cls(
            change_id=data.get("change_id", ""),
            change_type=ChangeType(data["change_type"]),
            path=data["path"],
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            user_id=data.get("user_id", ""),
            user_name=data.get("user_name", ""),
            timestamp=data.get("timestamp", ""),
            session_id=data.get("session_id"),
            metadata=data.get("metadata", {}),
        )

    def get_summary(self) -> str:
        """Get human-readable summary of change."""
        path_str = " > ".join(str(p) for p in self.path)

        summaries = {
            ChangeType.CREATE: f"Created {path_str}",
            ChangeType.UPDATE: f"Updated {path_str}",
            ChangeType.DELETE: f"Deleted {path_str}",
            ChangeType.RENAME: f"Renamed {path_str}",
            ChangeType.MOVE: f"Moved {path_str}",
            ChangeType.REORDER: f"Reordered {path_str}",
        }

        return summaries.get(self.change_type, f"Changed {path_str}")


@dataclass
class ChangeGroup:
    """A group of related changes (e.g., batch operation)."""
    group_id: str
    description: str
    changes: List[Change] = field(default_factory=list)
    user_id: str = ""
    user_name: str = ""
    timestamp: str = ""
    is_atomic: bool = True  # All or nothing for rollback

    def __post_init__(self):
        """Set default timestamp and generate group ID if missing."""
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.group_id:
            self.group_id = hashlib.sha256(
                f"{self.user_id}:{self.timestamp}".encode()
            ).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize change group to dictionary."""
        return {
            "group_id": self.group_id,
            "description": self.description,
            "changes": [c.to_dict() for c in self.changes],
            "change_count": len(self.changes),
            "user_id": self.user_id,
            "user_name": self.user_name,
            "timestamp": self.timestamp,
            "is_atomic": self.is_atomic,
        }


class ChangeTracker:
    """
    Tracks changes to documents for audit and rollback.

    Usage:
        tracker = ChangeTracker(document_id="workflow_123")

        # Record change
        change = tracker.record_change(
            change_type=ChangeType.UPDATE,
            path=["steps", 0, "name"],
            old_value="Old Name",
            new_value="New Name",
            user_id="user_1",
            user_name="John Doe",
        )

        # Get history
        history = tracker.get_history(limit=50)

        # Get changes by user
        user_changes = tracker.get_changes_by_user("user_1")

        # Generate diff
        diff = tracker.generate_diff(old_state, new_state)
    """

    def __init__(
        self,
        document_id: str,
        max_history: int = 1000,
    ):
        """
        Initialize change tracker.

        Args:
            document_id: Document to track
            max_history: Maximum changes to keep in memory
        """
        self.document_id = document_id
        self.max_history = max_history
        self._changes: List[Change] = []
        self._groups: List[ChangeGroup] = []
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._current_group: Optional[ChangeGroup] = None

    def record_change(
        self,
        change_type: ChangeType,
        path: List[str],
        old_value: Any = None,
        new_value: Any = None,
        user_id: str = "",
        user_name: str = "",
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Change:
        """
        Record a change.

        Args:
            change_type: Type of change
            path: Path to changed element
            old_value: Previous value
            new_value: New value
            user_id: User making change
            user_name: User display name
            session_id: Collaboration session ID
            metadata: Additional metadata

        Returns:
            Recorded Change
        """
        change = Change(
            change_id="",
            change_type=change_type,
            path=path,
            old_value=old_value,
            new_value=new_value,
            user_id=user_id,
            user_name=user_name,
            session_id=session_id,
            metadata=metadata or {},
        )

        # Add to current group or main list
        if self._current_group:
            self._current_group.changes.append(change)
        else:
            self._changes.append(change)

        # Trim history if needed
        if len(self._changes) > self.max_history:
            self._changes = self._changes[-self.max_history:]

        logger.debug(f"Recorded change: {change.get_summary()} by {user_name}")
        return change

    def start_group(
        self,
        description: str,
        user_id: str = "",
        user_name: str = "",
        is_atomic: bool = True,
    ) -> ChangeGroup:
        """
        Start a change group for batch operations.

        Args:
            description: Group description
            user_id: User ID
            user_name: User name
            is_atomic: Whether changes are atomic

        Returns:
            New ChangeGroup
        """
        if self._current_group:
            self.end_group()

        self._current_group = ChangeGroup(
            group_id="",
            description=description,
            user_id=user_id,
            user_name=user_name,
            is_atomic=is_atomic,
        )

        return self._current_group

    def end_group(self) -> Optional[ChangeGroup]:
        """
        End current change group.

        Returns:
            Completed ChangeGroup or None
        """
        if not self._current_group:
            return None

        group = self._current_group
        self._current_group = None

        if group.changes:
            self._groups.append(group)
            # Also add individual changes to main list
            self._changes.extend(group.changes)

        return group

    def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None,
        change_type: Optional[ChangeType] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> List[Change]:
        """
        Get change history with filters.

        Args:
            limit: Maximum changes to return
            offset: Offset for pagination
            user_id: Filter by user
            change_type: Filter by change type
            since: Filter changes after this timestamp
            until: Filter changes before this timestamp

        Returns:
            List of changes
        """
        changes = self._changes.copy()

        # Apply filters
        if user_id:
            changes = [c for c in changes if c.user_id == user_id]
        if change_type:
            changes = [c for c in changes if c.change_type == change_type]
        if since:
            changes = [c for c in changes if c.timestamp >= since]
        if until:
            changes = [c for c in changes if c.timestamp <= until]

        # Sort by timestamp descending (most recent first)
        changes.sort(key=lambda c: c.timestamp, reverse=True)

        # Apply pagination
        return changes[offset:offset + limit]

    def get_changes_by_user(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[Change]:
        """Get changes made by a specific user."""
        return self.get_history(limit=limit, user_id=user_id)

    def get_changes_for_path(
        self,
        path: List[str],
        limit: int = 50,
    ) -> List[Change]:
        """Get changes affecting a specific path."""
        path_prefix = path

        changes = [
            c for c in self._changes
            if c.path[:len(path_prefix)] == path_prefix
        ]

        changes.sort(key=lambda c: c.timestamp, reverse=True)
        return changes[:limit]

    def get_groups(self, limit: int = 20) -> List[ChangeGroup]:
        """Get change groups."""
        return sorted(
            self._groups,
            key=lambda g: g.timestamp,
            reverse=True,
        )[:limit]

    def save_snapshot(
        self,
        snapshot_id: str,
        state: Dict[str, Any],
        description: str = "",
    ) -> None:
        """
        Save a document snapshot.

        Args:
            snapshot_id: Unique snapshot ID
            state: Document state
            description: Snapshot description
        """
        self._snapshots[snapshot_id] = {
            "snapshot_id": snapshot_id,
            "state": state,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Get a saved snapshot."""
        return self._snapshots.get(snapshot_id)

    def generate_diff(
        self,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        path: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate diff between two states.

        Args:
            old_state: Previous state
            new_state: New state
            path: Current path (for recursion)

        Returns:
            List of diff entries
        """
        path = path or []
        diffs = []

        # Handle different types
        if type(old_state) is not type(new_state):
            diffs.append({
                "type": "replace",
                "path": path,
                "old_value": old_state,
                "new_value": new_state,
            })
            return diffs

        if isinstance(old_state, dict):
            all_keys = set(old_state.keys()) | set(new_state.keys())

            for key in all_keys:
                key_path = path + [key]

                if key not in old_state:
                    diffs.append({
                        "type": "add",
                        "path": key_path,
                        "new_value": new_state[key],
                    })
                elif key not in new_state:
                    diffs.append({
                        "type": "remove",
                        "path": key_path,
                        "old_value": old_state[key],
                    })
                elif old_state[key] != new_state[key]:
                    # Recurse for nested objects
                    if isinstance(old_state[key], (dict, list)):
                        diffs.extend(self.generate_diff(
                            old_state[key],
                            new_state[key],
                            key_path,
                        ))
                    else:
                        diffs.append({
                            "type": "change",
                            "path": key_path,
                            "old_value": old_state[key],
                            "new_value": new_state[key],
                        })

        elif isinstance(old_state, list):
            # Use sequence matcher for list diffs
            old_json = [json.dumps(item, sort_keys=True) for item in old_state]
            new_json = [json.dumps(item, sort_keys=True) for item in new_state]

            matcher = difflib.SequenceMatcher(None, old_json, new_json)

            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == "replace":
                    for idx in range(i1, i2):
                        diffs.append({
                            "type": "change",
                            "path": path + [idx],
                            "old_value": old_state[idx],
                            "new_value": new_state[j1 + (idx - i1)] if j1 + (idx - i1) < len(new_state) else None,
                        })
                elif tag == "delete":
                    for idx in range(i1, i2):
                        diffs.append({
                            "type": "remove",
                            "path": path + [idx],
                            "old_value": old_state[idx],
                        })
                elif tag == "insert":
                    for idx in range(j1, j2):
                        diffs.append({
                            "type": "add",
                            "path": path + [idx],
                            "new_value": new_state[idx],
                        })

        elif old_state != new_state:
            diffs.append({
                "type": "change",
                "path": path,
                "old_value": old_state,
                "new_value": new_state,
            })

        return diffs

    def generate_text_diff(
        self,
        old_text: str,
        new_text: str,
        context_lines: int = 3,
    ) -> str:
        """
        Generate unified diff for text content.

        Args:
            old_text: Previous text
            new_text: New text
            context_lines: Context lines around changes

        Returns:
            Unified diff string
        """
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="before",
            tofile="after",
            n=context_lines,
        )

        return "".join(diff)

    def get_attribution(
        self,
        path: List[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Get attribution for who last modified a path.

        Args:
            path: Path to check

        Returns:
            Attribution info or None
        """
        changes = self.get_changes_for_path(path, limit=1)
        if changes:
            change = changes[0]
            return {
                "user_id": change.user_id,
                "user_name": change.user_name,
                "timestamp": change.timestamp,
                "change_type": change.change_type.value,
            }
        return None

    def get_contributors(self) -> List[Dict[str, Any]]:
        """Get list of all contributors with change counts."""
        contributors: Dict[str, Dict[str, Any]] = {}

        for change in self._changes:
            if change.user_id not in contributors:
                contributors[change.user_id] = {
                    "user_id": change.user_id,
                    "user_name": change.user_name,
                    "change_count": 0,
                    "first_change": change.timestamp,
                    "last_change": change.timestamp,
                }

            contributors[change.user_id]["change_count"] += 1
            if change.timestamp > contributors[change.user_id]["last_change"]:
                contributors[change.user_id]["last_change"] = change.timestamp

        return sorted(
            contributors.values(),
            key=lambda c: c["change_count"],
            reverse=True,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tracker to dictionary."""
        return {
            "document_id": self.document_id,
            "changes": [c.to_dict() for c in self._changes],
            "groups": [g.to_dict() for g in self._groups],
            "snapshots": self._snapshots,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChangeTracker":
        """Deserialize tracker from dictionary."""
        tracker = cls(document_id=data["document_id"])
        tracker._changes = [Change.from_dict(c) for c in data.get("changes", [])]
        tracker._snapshots = data.get("snapshots", {})
        return tracker


# Global instances per document
_trackers: Dict[str, ChangeTracker] = {}


def get_change_tracker(document_id: str) -> ChangeTracker:
    """Get or create change tracker for document."""
    if document_id not in _trackers:
        _trackers[document_id] = ChangeTracker(document_id)
    return _trackers[document_id]
