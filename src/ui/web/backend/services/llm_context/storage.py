"""
Context Storage - Session Persistence & Context Updates

Handles:
- Session persistence (file-based, can upgrade to Redis)
- Context file updates (status, warnings, events)
- Session recovery after restart

Implements the Context Packaging system from CONTEXT_PACKAGING.md
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionStorage:
    """
    Persistent storage for coordination sessions.

    Uses file-based storage by default (easy to inspect, version control).
    Can be upgraded to Redis for production.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize session storage.

        Args:
            storage_dir: Directory for session files.
                        Defaults to ~/.flyto/sessions/
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / ".flyto" / "sessions"

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Session storage initialized at: {self.storage_dir}")

    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Save session to persistent storage.

        Args:
            session_id: Unique session ID
            session_data: Session data to persist

        Returns:
            True if saved successfully
        """
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            session_data["_saved_at"] = datetime.now().isoformat()

            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Session saved: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session from persistent storage.

        Args:
            session_id: Session ID to load

        Returns:
            Session data or None if not found
        """
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            if not session_file.exists():
                logger.debug(f"Session not found: {session_id}")
                return None

            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.debug(f"Session loaded: {session_id}")
            return data

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete session file"""
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                logger.debug(f"Session deleted: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def list_sessions(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all sessions, optionally filtered by state.

        Args:
            state: Filter by state (running, paused, completed, stopped)

        Returns:
            List of session summaries
        """
        sessions = []
        for session_file in self.storage_dir.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if state and data.get("state") != state:
                    continue

                sessions.append({
                    "id": data.get("id", session_file.stem),
                    "task": data.get("task", "")[:100],
                    "state": data.get("state", "unknown"),
                    "turn": data.get("turn", 0),
                    "created_at": data.get("created_at"),
                    "saved_at": data.get("_saved_at"),
                })
            except Exception as e:
                logger.warning(f"Failed to read session file {session_file}: {e}")

        return sorted(sessions, key=lambda x: x.get("saved_at", ""), reverse=True)

    def cleanup_old_sessions(self, max_age_days: int = 7) -> int:
        """
        Clean up sessions older than max_age_days.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of sessions deleted
        """
        deleted = 0
        cutoff = time.time() - (max_age_days * 24 * 60 * 60)

        for session_file in self.storage_dir.glob("*.json"):
            try:
                if session_file.stat().st_mtime < cutoff:
                    session_file.unlink()
                    deleted += 1
            except Exception as e:
                logger.warning(f"Failed to cleanup {session_file}: {e}")

        logger.info(f"Cleaned up {deleted} old sessions")
        return deleted


class ContextUpdater:
    """
    Updates context files based on session results.

    Handles:
    - Updating status.json when tasks complete
    - Appending to warnings.json when new issues found
    - Appending to events.ndjson
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize context updater.

        Args:
            project_root: Project root containing .flyto/ directory
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            self.project_root = Path.cwd()

        self.flyto_dir = self.project_root / ".flyto"
        self.flyto_dir.mkdir(parents=True, exist_ok=True)

    def append_event(
        self,
        event_type: str,
        note: str,
        ref: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Append event to events.ndjson.

        Args:
            event_type: Type (done, decision, warning, error, etc.)
            note: Description of the event
            ref: Optional reference ID (task ID, ADR ID, etc.)
            extra: Optional extra data

        Returns:
            True if successful
        """
        try:
            event = {
                "ts": datetime.now().isoformat(),
                "type": event_type,
                "note": note,
            }
            if ref:
                event["ref"] = ref
            if extra:
                event.update(extra)

            events_file = self.flyto_dir / "events.ndjson"
            with open(events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

            logger.debug(f"Event appended: {event_type} - {note[:50]}")
            return True

        except Exception as e:
            logger.error(f"Failed to append event: {e}")
            return False

    def update_status(
        self,
        done_task: Optional[str] = None,
        add_todo: Optional[Dict[str, Any]] = None,
        update_todo: Optional[Dict[str, Any]] = None,
        set_focus: Optional[str] = None,
    ) -> bool:
        """
        Update status.json.

        Args:
            done_task: Task ID to mark as done
            add_todo: New todo to add {"id", "title", "status", "prio"}
            update_todo: Todo to update {"id", "status"}
            set_focus: New focus description

        Returns:
            True if successful
        """
        try:
            status_file = self.flyto_dir / "30_status.json"

            # Load existing or create new
            if status_file.exists():
                with open(status_file, "r", encoding="utf-8") as f:
                    status = json.load(f)
            else:
                status = {
                    "active_sprint": datetime.now().strftime("%Y-%m-%d"),
                    "focus": "",
                    "todos": [],
                    "done_recently": [],
                }

            # Apply updates
            if set_focus:
                status["focus"] = set_focus

            if done_task:
                # Move from todos to done_recently
                todos = status.get("todos", [])
                for i, todo in enumerate(todos):
                    if todo.get("id") == done_task:
                        status.setdefault("done_recently", []).insert(0, todo.get("title", done_task))
                        todos.pop(i)
                        break
                # Keep only last 10 done items
                status["done_recently"] = status["done_recently"][:10]

            if add_todo:
                status.setdefault("todos", []).append(add_todo)

            if update_todo:
                for todo in status.get("todos", []):
                    if todo.get("id") == update_todo.get("id"):
                        todo.update(update_todo)
                        break

            # Save
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2, ensure_ascii=False)

            logger.debug("Status updated")
            return True

        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            return False

    def add_warning(
        self,
        scope: str,
        rule: str,
        why: str,
        warning_type: str = "gotchas",
    ) -> bool:
        """
        Add warning to warnings.json.

        Args:
            scope: Scope of the warning (e.g., "cloud backend")
            rule: What not to do / what to watch for
            why: Reason for the warning
            warning_type: "do_not_touch" or "gotchas"

        Returns:
            True if successful
        """
        try:
            warnings_file = self.flyto_dir / "40_warnings.json"

            # Load existing or create new
            if warnings_file.exists():
                with open(warnings_file, "r", encoding="utf-8") as f:
                    warnings = json.load(f)
            else:
                warnings = {
                    "do_not_touch": [],
                    "gotchas": [],
                    "known_limitations": [],
                }

            # Add warning
            warning_entry = {"scope": scope, "rule": rule, "why": why}

            if warning_type == "do_not_touch":
                # Check if similar warning exists
                existing = warnings.get("do_not_touch", [])
                if not any(w.get("rule") == rule for w in existing):
                    existing.append(warning_entry)
            else:
                # For gotchas, use symptom/cause/fix format
                gotcha_entry = {
                    "symptom": scope,
                    "cause": rule,
                    "fix": why,
                }
                existing = warnings.get("gotchas", [])
                if not any(w.get("symptom") == scope for w in existing):
                    existing.append(gotcha_entry)

            # Save
            with open(warnings_file, "w", encoding="utf-8") as f:
                json.dump(warnings, f, indent=2, ensure_ascii=False)

            logger.debug(f"Warning added: {rule[:50]}")
            return True

        except Exception as e:
            logger.error(f"Failed to add warning: {e}")
            return False

    def on_session_complete(
        self,
        session_data: Dict[str, Any],
        success: bool = True,
    ) -> None:
        """
        Called when a coordination session completes.
        Updates context files based on session results.

        Args:
            session_data: Complete session data
            success: Whether session completed successfully
        """
        task = session_data.get("task", "Unknown task")
        session_id = session_data.get("id", "unknown")

        # Record event
        event_type = "done" if success else "failed"
        self.append_event(
            event_type=event_type,
            note=f"Session {session_id}: {task[:100]}",
            ref=session_id,
            extra={
                "turns": session_data.get("turn", 0),
                "success": success,
            }
        )

        # If there were failures, record as warnings
        events = session_data.get("events", [])
        for event in events:
            if event.get("type") == "ERROR":
                error = event.get("error", "Unknown error")
                self.add_warning(
                    scope=f"Session {session_id}",
                    rule=error[:200],
                    why="Encountered during coordination",
                    warning_type="gotchas",
                )

        logger.info(f"Session complete handler executed for {session_id}")


# Global instances (singleton pattern)
_session_storage: Optional[SessionStorage] = None
_context_updater: Optional[ContextUpdater] = None


def get_session_storage() -> SessionStorage:
    """Get singleton session storage instance"""
    global _session_storage
    if _session_storage is None:
        _session_storage = SessionStorage()
    return _session_storage


def get_context_updater(project_root: Optional[str] = None) -> ContextUpdater:
    """Get context updater instance"""
    global _context_updater
    if _context_updater is None or project_root:
        _context_updater = ContextUpdater(project_root)
    return _context_updater
