"""
Context Compiler - LLM Context Packaging

Compiles context packages for LLM sessions based on task type.
Implements the Context Packaging system from CONTEXT_PACKAGING.md

Usage:
    compiler = ContextCompiler(project_root="/path/to/project")
    context = compiler.compile(TaskType.BUGFIX)
    # context is ready to inject into LLM prompt
"""

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Types of tasks that determine context composition"""
    BUGFIX = "bugfix"
    NEW_FEATURE = "new_feature"
    REFACTOR = "refactor"
    DESIGN = "design"
    CODE_REVIEW = "code_review"
    GENERAL = "general"


@dataclass
class ContextPackage:
    """Compiled context package ready for LLM injection"""
    task_type: TaskType
    dna: str = ""
    contracts: Dict[str, Any] = field(default_factory=dict)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    status: Dict[str, Any] = field(default_factory=dict)
    warnings: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    total_tokens_estimate: int = 0
    compiled_at: str = ""

    def to_prompt(self) -> str:
        """Convert to prompt-ready markdown format"""
        sections = []

        if self.dna:
            sections.append(f"## Project DNA\n\n{self.dna}")

        if self.contracts:
            sections.append(f"## Contracts (MUST NOT violate)\n\n```json\n{json.dumps(self.contracts, indent=2, ensure_ascii=False)}\n```")

        if self.decisions:
            decisions_text = "\n".join([
                f"- **{d.get('id', 'ADR')}**: {d.get('decision', '')} ({d.get('reason', '')})"
                for d in self.decisions
            ])
            sections.append(f"## Key Decisions\n\n{decisions_text}")

        if self.status:
            sections.append(f"## Current Status\n\n```json\n{json.dumps(self.status, indent=2, ensure_ascii=False)}\n```")

        if self.warnings:
            sections.append(f"## Warnings (avoid these)\n\n```json\n{json.dumps(self.warnings, indent=2, ensure_ascii=False)}\n```")

        if self.events:
            events_text = "\n".join([
                f"- [{e.get('ts', '')}] {e.get('type', '')}: {e.get('note', '')}"
                for e in self.events[-20:]  # Last 20 events
            ])
            sections.append(f"## Recent Events\n\n{events_text}")

        return "\n\n---\n\n".join(sections)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_type": self.task_type.value,
            "dna": self.dna,
            "contracts": self.contracts,
            "decisions": self.decisions,
            "status": self.status,
            "warnings": self.warnings,
            "events": self.events,
            "total_tokens_estimate": self.total_tokens_estimate,
            "compiled_at": self.compiled_at,
        }


# Context composition rules per task type
TASK_CONTEXT_RULES = {
    TaskType.BUGFIX: ["dna", "contracts", "warnings", "status"],
    TaskType.NEW_FEATURE: ["dna", "contracts", "decisions", "status"],
    TaskType.REFACTOR: ["dna", "contracts", "decisions", "warnings"],
    TaskType.DESIGN: ["dna", "contracts", "decisions"],
    TaskType.CODE_REVIEW: ["dna", "contracts", "warnings"],
    TaskType.GENERAL: ["dna", "contracts", "status"],
}


class ContextCompiler:
    """
    Compiles context packages for LLM sessions.

    Reads from .flyto/ directory and assembles context based on task type.
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize compiler with project root.

        Args:
            project_root: Path to project root containing .flyto/ directory.
                         If None, uses current working directory.
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            self.project_root = Path.cwd()

        self.flyto_dir = self.project_root / ".flyto"

    def compile(
        self,
        task_type: TaskType = TaskType.GENERAL,
        include_events: bool = True,
        max_events: int = 20,
    ) -> ContextPackage:
        """
        Compile context package for given task type.

        Args:
            task_type: Type of task (determines what context to include)
            include_events: Whether to include recent events
            max_events: Maximum number of events to include

        Returns:
            ContextPackage ready for LLM injection
        """
        from datetime import datetime

        package = ContextPackage(task_type=task_type)
        package.compiled_at = datetime.now().isoformat()

        # Get rules for this task type
        rules = TASK_CONTEXT_RULES.get(task_type, TASK_CONTEXT_RULES[TaskType.GENERAL])

        # Load each required component
        if "dna" in rules:
            package.dna = self._load_dna()

        if "contracts" in rules:
            package.contracts = self._load_json("10_contracts.json")

        if "decisions" in rules:
            decisions_data = self._load_json("20_decisions.json")
            package.decisions = decisions_data.get("decisions", [])

        if "status" in rules:
            package.status = self._load_json("30_status.json")

        if "warnings" in rules:
            package.warnings = self._load_json("40_warnings.json")

        if "events" in rules and include_events:
            package.events = self._load_events(max_events)

        # Estimate tokens (rough: 4 chars = 1 token)
        prompt_text = package.to_prompt()
        package.total_tokens_estimate = len(prompt_text) // 4

        logger.info(
            f"Compiled context for {task_type.value}: "
            f"~{package.total_tokens_estimate} tokens"
        )

        return package

    def _load_dna(self) -> str:
        """Load DNA markdown file"""
        dna_path = self.flyto_dir / "00_dna.md"
        if dna_path.exists():
            return dna_path.read_text(encoding="utf-8")
        logger.warning(f"DNA file not found: {dna_path}")
        return ""

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON context file"""
        file_path = self.flyto_dir / filename
        if file_path.exists():
            try:
                return json.loads(file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {filename}: {e}")
                return {}
        logger.warning(f"Context file not found: {file_path}")
        return {}

    def _load_events(self, max_events: int = 20) -> List[Dict[str, Any]]:
        """Load recent events from NDJSON file"""
        events_path = self.flyto_dir / "events.ndjson"
        if not events_path.exists():
            return []

        events = []
        try:
            lines = events_path.read_text(encoding="utf-8").strip().split("\n")
            # Get last N lines
            for line in lines[-max_events:]:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error loading events: {e}")

        return events

    def get_available_context(self) -> Dict[str, bool]:
        """Check which context files exist"""
        return {
            "dna": (self.flyto_dir / "00_dna.md").exists(),
            "contracts": (self.flyto_dir / "10_contracts.json").exists(),
            "decisions": (self.flyto_dir / "20_decisions.json").exists(),
            "status": (self.flyto_dir / "30_status.json").exists(),
            "warnings": (self.flyto_dir / "40_warnings.json").exists(),
            "events": (self.flyto_dir / "events.ndjson").exists(),
        }


def compile_context_for_task(
    task_description: str,
    project_root: Optional[str] = None,
) -> ContextPackage:
    """
    Convenience function to compile context based on task description.

    Automatically detects task type from description.

    Args:
        task_description: Natural language task description
        project_root: Project root path

    Returns:
        Compiled ContextPackage
    """
    # Simple keyword-based task type detection
    task_lower = task_description.lower()

    if any(kw in task_lower for kw in ["fix", "bug", "error", "issue", "broken"]):
        task_type = TaskType.BUGFIX
    elif any(kw in task_lower for kw in ["add", "new", "feature", "implement", "create"]):
        task_type = TaskType.NEW_FEATURE
    elif any(kw in task_lower for kw in ["refactor", "clean", "improve", "optimize"]):
        task_type = TaskType.REFACTOR
    elif any(kw in task_lower for kw in ["design", "plan", "architect"]):
        task_type = TaskType.DESIGN
    elif any(kw in task_lower for kw in ["review", "check", "audit"]):
        task_type = TaskType.CODE_REVIEW
    else:
        task_type = TaskType.GENERAL

    compiler = ContextCompiler(project_root)
    return compiler.compile(task_type)
