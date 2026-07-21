"""
Lineage Services

Business logic and helper functions for lineage API.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from api.lineage.models import LineageNode

logger = logging.getLogger(__name__)


def get_evidence_path() -> Path:
    """Get evidence base path, configurable via environment"""
    custom_path = os.getenv("FLYTO_EVIDENCE_PATH")
    if custom_path:
        return Path(custom_path)

    # Find project root by looking for flyto-cloud directory name
    current = Path(__file__).resolve()
    for _ in range(10):
        current = current.parent
        if current.name == "flyto-cloud":
            evidence_dir = current / "evidence"
            if evidence_dir.exists():
                return evidence_dir
            break

    return Path("./evidence")


def load_execution_evidence(execution_id: str) -> List[Dict[str, Any]]:
    """Load all evidence for an execution"""
    evidence_path = get_evidence_path()
    jsonl_path = evidence_path / execution_id / "evidence.jsonl"

    if not jsonl_path.exists():
        return []

    steps = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                steps.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return steps


def load_tracking_data(execution_id: str) -> Dict[str, Any]:
    """Load tracking data from evidence if available"""
    evidence_path = get_evidence_path()
    tracking_path = evidence_path / execution_id / "tracking.json"

    if tracking_path.exists():
        with open(tracking_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_value_preview(value: Any, max_length: int = 50) -> str:
    """Get a preview of a value for display"""
    if value is None:
        return "null"
    if isinstance(value, str):
        if len(value) > max_length:
            return value[:max_length] + "..."
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        return f"{{...}} ({len(value)} keys)"
    if isinstance(value, list):
        return f"[...] ({len(value)} items)"
    return str(type(value).__name__)


def get_data_type(value: Any) -> str:
    """Get the data type of a value"""
    if value is None:
        return "null"
    if isinstance(value, str):
        return "string"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "unknown"


def classify_module(module_id: str) -> Dict[str, Any]:
    """Classify a module into lane and category"""
    module_lower = module_id.lower() if module_id else ""

    # Determine category
    if "browser" in module_lower or "page" in module_lower or "dom" in module_lower:
        category = "browser"
    elif "data" in module_lower or "json" in module_lower or "csv" in module_lower or "file" in module_lower:
        category = "data"
    elif "loop" in module_lower or "if" in module_lower or "condition" in module_lower or "retry" in module_lower:
        category = "flow"
    elif "ai" in module_lower or "llm" in module_lower or "gpt" in module_lower or "claude" in module_lower:
        category = "ai"
    elif "http" in module_lower or "api" in module_lower or "request" in module_lower:
        category = "http"
    else:
        category = "other"

    # Determine lane (Source / Transform / Sink)
    source_keywords = ["load", "read", "fetch", "get", "launch", "open", "start", "input", "source"]
    sink_keywords = ["save", "write", "export", "close", "end", "output", "sink", "send", "post"]

    lane = "transform"  # default
    for kw in source_keywords:
        if kw in module_lower:
            lane = "source"
            break
    for kw in sink_keywords:
        if kw in module_lower:
            lane = "sink"
            break

    # Control flow detection - only flow.* modules are control flow
    is_control_flow = module_lower.startswith("flow.")

    return {
        "category": category,
        "lane": lane,
        "is_control_flow": is_control_flow
    }


def detect_state_nodes(steps: List[Dict[str, Any]]) -> List[LineageNode]:
    """Detect state nodes like browser sessions"""
    state_nodes = []
    browser_session_active = False

    for step in steps:
        module_id = step.get('module_id', '').lower()

        # Browser session detection
        if 'browser.launch' in module_id or 'browser.open' in module_id:
            browser_session_active = True
            state_nodes.append(LineageNode(
                id=f"state_browser_{step.get('step_id', 'unknown')}",
                type="state",
                label="Browser Session",
                step_id=step.get('step_id'),
                module_id=module_id,
                category="browser",
                lane="source"
            ))
        elif 'browser.close' in module_id and browser_session_active:
            browser_session_active = False

    return state_nodes


def group_related_steps(steps: List[Dict[str, Any]]) -> List[LineageNode]:
    """Group related steps (e.g., loop iterations, browser sequences)"""
    groups = []
    current_group = None
    group_steps = []

    for i, step in enumerate(steps):
        module_id = step.get('module_id', '').lower()

        # Detect loop start
        if 'loop' in module_id and 'start' in module_id:
            if current_group:
                # Close previous group
                groups.append(LineageNode(
                    id=f"group_{current_group['id']}",
                    type="group",
                    label=f"{current_group['label']} ({len(group_steps)} steps)",
                    step_id=current_group['id'],
                    module_id=current_group['module_id'],
                    category="flow",
                    lane="transform",
                    is_control_flow=True,
                    loop_count=current_group.get('loop_count', 1),
                    group_children=[s.get('step_id') for s in group_steps]
                ))
            current_group = {
                'id': step.get('step_id'),
                'label': 'Loop',
                'module_id': module_id,
                'loop_count': step.get('loop_count', 1)
            }
            group_steps = []

        elif 'loop' in module_id and 'end' in module_id:
            if current_group:
                groups.append(LineageNode(
                    id=f"group_{current_group['id']}",
                    type="group",
                    label=f"{current_group['label']} ({len(group_steps)} steps)",
                    step_id=current_group['id'],
                    module_id=current_group['module_id'],
                    category="flow",
                    lane="transform",
                    is_control_flow=True,
                    loop_count=current_group.get('loop_count', 1),
                    group_children=[s.get('step_id') for s in group_steps]
                ))
                current_group = None
                group_steps = []

        elif current_group:
            group_steps.append(step)

    return groups
