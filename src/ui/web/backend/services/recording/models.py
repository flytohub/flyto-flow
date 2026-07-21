"""
Recording Service Models

Dataclasses and enums for browser recording.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ActionType(str, Enum):
    """Types of recorded actions."""
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    HOVER = "hover"
    PRESS = "press"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    ASSERT = "assert"
    SCROLL = "scroll"
    DRAG = "drag"
    UPLOAD = "upload"


class SelectorStrategy(str, Enum):
    """Selector generation strategies."""
    AUTO = "auto"
    DATA_TESTID = "data-testid"
    DATA_CY = "data-cy"
    ID = "id"
    TEXT = "text"
    ROLE = "role"
    CSS = "css"
    XPATH = "xpath"


RECORDED_ACTION_MODULES: Dict[ActionType, str] = {
    ActionType.NAVIGATE: "browser.goto",
    ActionType.CLICK: "browser.click",
    ActionType.FILL: "browser.type",
    ActionType.SELECT: "browser.select",
    ActionType.CHECK: "browser.click",
    ActionType.UNCHECK: "browser.click",
    ActionType.HOVER: "browser.hover",
    ActionType.PRESS: "browser.press",
    ActionType.WAIT: "browser.wait",
    ActionType.SCREENSHOT: "browser.screenshot",
    ActionType.ASSERT: "browser.extract",
    ActionType.SCROLL: "browser.scroll",
    ActionType.DRAG: "browser.drag",
    ActionType.UPLOAD: "browser.upload",
}


def _coerce_action_type(value: ActionType | str) -> ActionType:
    return ActionType(value) if isinstance(value, str) else value


def _coerce_milliseconds(value: Any, default: int) -> int:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_replayable_navigation_url(value: Optional[str]) -> bool:
    return bool(value and value.startswith(("http://", "https://")))


def _non_replayable_warning(action: "RecordedAction", action_index: int) -> Dict[str, Any]:
    action_type = _coerce_action_type(action.type)
    warning = {
        "code": "non_replayable_action",
        "action_index": action_index,
        "action_type": action_type.value,
        "message": f"Recorded {action_type.value} action was skipped because it cannot be replayed safely.",
    }
    if action_type == ActionType.NAVIGATE:
        warning["code"] = "non_replayable_navigation"
        warning["message"] = "Recorded navigation was skipped because only http and https URLs are replayable."
        warning["value"] = action.value
    elif action.selector:
        warning["selector"] = action.selector
    return warning


@dataclass
class RecordedAction:
    """A single recorded action."""
    type: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    timestamp: str = ""
    screenshot: Optional[str] = None
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default timestamp if not provided."""
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the recorded action to a dictionary."""
        return {
            "type": self.type.value if isinstance(self.type, ActionType) else self.type,
            "selector": self.selector,
            "value": self.value,
            "timestamp": self.timestamp,
            "screenshot": self.screenshot,
            "alternatives": self.alternatives,
            "options": self.options,
        }

    def to_workflow_step(self, index: int = 0) -> Dict[str, Any]:
        """Convert to workflow step format."""
        step = {
            "id": f"step_{index + 1}",
            "label": self._generate_step_name(),
            "module": self._get_module_id(),
            "params": self._get_params(),
        }
        return step

    def is_replayable(self) -> bool:
        """Return whether the action can be emitted as a flyto-core workflow step."""
        action_type = _coerce_action_type(self.type)
        if action_type == ActionType.NAVIGATE:
            return _is_replayable_navigation_url(self.value)
        return True

    def _generate_step_name(self) -> str:
        """Generate human-readable step name."""
        type_names = {
            ActionType.NAVIGATE: "Navigate to",
            ActionType.CLICK: "Click",
            ActionType.FILL: "Fill",
            ActionType.SELECT: "Select",
            ActionType.CHECK: "Check",
            ActionType.UNCHECK: "Uncheck",
            ActionType.HOVER: "Hover over",
            ActionType.PRESS: "Press key",
            ActionType.WAIT: "Wait for",
            ActionType.SCREENSHOT: "Take screenshot",
            ActionType.ASSERT: "Assert",
            ActionType.SCROLL: "Scroll",
            ActionType.DRAG: "Drag",
            ActionType.UPLOAD: "Upload file",
        }
        action_type = ActionType(self.type) if isinstance(self.type, str) else self.type
        base_name = type_names.get(action_type, str(action_type))

        if self.value:
            return f"{base_name} '{self.value[:30]}'"
        elif self.selector:
            return f"{base_name} element"
        return base_name

    def _get_module_id(self) -> str:
        """Get corresponding module ID."""
        action_type = _coerce_action_type(self.type)
        return RECORDED_ACTION_MODULES.get(action_type, f"browser.{self.type}")

    def _get_params(self) -> Dict[str, Any]:
        """Get module parameters."""
        params = {}
        action_type = _coerce_action_type(self.type)
        skip_option_keys: set[str] = set()

        if action_type == ActionType.NAVIGATE:
            params["url"] = self.value
        elif action_type in [ActionType.CLICK, ActionType.CHECK, ActionType.UNCHECK]:
            params["click_method"] = "selector"
            params["selector"] = self.selector
        elif action_type == ActionType.HOVER:
            params["selector"] = self.selector
        elif action_type == ActionType.FILL:
            params["type_method"] = "selector"
            params["selector"] = self.selector
            params["text"] = self.value
        elif action_type == ActionType.SELECT:
            params["select_method"] = self.options.get("select_method", "value")
            params["selector"] = self.selector
            params["target"] = self.value
        elif action_type == ActionType.PRESS:
            params["key"] = self.value
        elif action_type == ActionType.WAIT:
            if self.selector:
                params["selector"] = self.selector
                params["timeout_ms"] = _coerce_milliseconds(
                    self.options.get("timeout_ms", self.options.get("timeout")),
                    5000,
                )
            else:
                params["duration_ms"] = _coerce_milliseconds(
                    self.value or self.options.get("duration_ms") or self.options.get("timeout_ms"),
                    1000,
                )
            skip_option_keys.add("timeout")
        elif action_type == ActionType.SCREENSHOT:
            params["path"] = self.value or "screenshot.png"
        elif action_type == ActionType.ASSERT:
            params["selector"] = self.selector
            params["condition"] = self.value
        elif action_type == ActionType.SCROLL:
            if self.selector:
                params["selector"] = self.selector
            elif self.value in {"up", "down", "left", "right"}:
                params["direction"] = self.value
        elif action_type == ActionType.DRAG:
            params["source"] = self.selector
            params["target"] = self.options.get("target") or self.value
            skip_option_keys.add("target")
        elif action_type == ActionType.UPLOAD:
            params["selector"] = self.selector
            params["file_path"] = self.options.get("file_path") or self.value
            skip_option_keys.add("file_path")

        for key, value in self.options.items():
            if key not in skip_option_keys:
                params.setdefault(key, value)
        return params


@dataclass
class RecordingSession:
    """A recording session."""
    session_id: str
    url: str
    started_at: str = ""
    ended_at: Optional[str] = None
    actions: List[RecordedAction] = field(default_factory=list)
    status: str = "active"
    options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default started_at timestamp if not provided."""
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the recording session to a dictionary."""
        return {
            "session_id": self.session_id,
            "url": self.url,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "action_count": len(self.actions),
            "status": self.status,
            "options": self.options,
        }

    def to_workflow(self) -> Dict[str, Any]:
        """Convert recording to workflow format."""
        steps = [
            {"id": "launch", "label": "Launch Browser", "module": "browser.launch", "params": {"headless": False}},
        ]
        warnings: List[Dict[str, Any]] = []
        action_index = 0
        for recorded_index, action in enumerate(self.actions):
            if not action.is_replayable():
                warnings.append(_non_replayable_warning(action, recorded_index))
                continue
            steps.append(action.to_workflow_step(action_index))
            action_index += 1
        steps.append(
            {"id": "close", "label": "Close Browser", "module": "browser.close", "params": {}},
        )
        recording_summary = {
            "recorded_action_count": len(self.actions),
            "replayable_action_count": action_index,
            "skipped_action_count": len(warnings),
            "step_count": len(steps),
        }
        return {
            "name": "Recorded Workflow",
            "description": f"Recorded from {self.url} on {self.started_at}",
            "version": "1.0.0",
            "steps": steps,
            "recording_summary": recording_summary,
            "warnings": warnings,
        }
