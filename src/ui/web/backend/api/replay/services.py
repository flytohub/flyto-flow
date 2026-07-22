"""
Replay Services

Evidence-based replay manager and helper functions.
"""
import json
import logging
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from local.storage_paths import evidence_path, runs_path

logger = logging.getLogger(__name__)


def get_evidence_path() -> Path:
    """Get the local evidence directory."""
    return evidence_path()


def get_runs_path() -> Path:
    """Get the local run-artifact directory."""
    return runs_path()


class EvidenceReplayManager:
    """
    Replay manager that reads from evidence.jsonl files.

    Provides:
    - Step state loading from evidence
    - Execution comparison with diff detection
    - Replay history tracking
    - Context modification support
    """

    def __init__(self, evidence_path: Path):
        """Initialize with evidence directory path and load replay history."""
        self.evidence_path = evidence_path
        self._history: List[Dict[str, Any]] = []
        self._history_file = evidence_path / ".replay_history.json"
        self._load_history()

    def _load_history(self):
        """Load replay history from file"""
        try:
            if self._history_file.exists():
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load replay history: {e}")
            self._history = []

    def _save_history(self):
        """Save replay history to file"""
        try:
            self.evidence_path.mkdir(parents=True, exist_ok=True)
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history[-200:], f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save replay history: {e}")

    def _load_evidence(self, execution_id: str) -> List[Dict[str, Any]]:
        """Load evidence JSONL for an execution"""
        evidence_file = self.evidence_path / execution_id / "evidence.jsonl"

        if not evidence_file.exists():
            return []

        steps = []
        with open(evidence_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    steps.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return steps

    def _find_step(self, steps: List[Dict], step_id: str) -> Optional[Dict]:
        """Find a specific step in evidence (returns first occurrence)"""
        for step in steps:
            if step.get('step_id') == step_id:
                return step
        return None

    def _find_all_occurrences(self, steps: List[Dict], step_id: str) -> List[Dict]:
        """Find all occurrences of a step (for loops)"""
        return [s for s in steps if s.get('step_id') == step_id]

    async def validate_replay(
        self,
        execution_id: str,
        step_id: str,
        config: Any = None
    ) -> Dict[str, Any]:
        """Validate that replay is possible"""
        steps = self._load_evidence(execution_id)

        if not steps:
            return {
                "can_replay": False,
                "reason": "Execution evidence not found",
                "execution_id": execution_id
            }

        # Find the step
        target_step = self._find_step(steps, step_id)
        if not target_step:
            return {
                "can_replay": False,
                "reason": f"Step '{step_id}' not found in execution",
                "available_steps": [s.get('step_id') for s in steps]
            }

        # Check if step has context
        if not target_step.get('context_before'):
            return {
                "can_replay": False,
                "reason": "Step has no context_before (required for replay)",
                "step_id": step_id
            }

        # Get step index and calculate remaining steps
        step_index = target_step.get('step_index', 0)
        unique_steps = {}
        for s in steps:
            sid = s.get('step_id')
            if sid not in unique_steps:
                unique_steps[sid] = s

        remaining = [s for s in unique_steps.values() if s.get('step_index', 0) >= step_index]

        return {
            "can_replay": True,
            "execution_id": execution_id,
            "step_id": step_id,
            "step_index": step_index,
            "module_id": target_step.get('module_id'),
            "total_steps": len(unique_steps),
            "remaining_steps": len(remaining),
            "context_available": True,
            "context_keys": list(target_step.get('context_before', {}).keys())
        }

    async def load_execution_state(
        self,
        execution_id: str,
        step_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load execution state at a specific step"""
        steps = self._load_evidence(execution_id)

        if not steps:
            return None

        # Get all occurrences of this step
        occurrences = self._find_all_occurrences(steps, step_id)

        if not occurrences:
            return None

        # Return the last occurrence (most recent in case of loops)
        step = occurrences[-1]

        return {
            "step_id": step.get('step_id'),
            "step_index": step.get('step_index'),
            "module_id": step.get('module_id'),
            "params": step.get('params', {}),
            "context_before": self._sanitize_context(step.get('context_before', {})),
            "context_after": self._sanitize_context(step.get('context_after', {})),
            "result": step.get('result'),
            "status": step.get('status'),
            "error": step.get('error_message'),
            "duration_ms": step.get('duration_ms'),
            "timestamp": step.get('timestamp'),
            "occurrence_count": len(occurrences)
        }

    async def load_execution_steps(
        self,
        execution_id: str
    ) -> List[Dict[str, Any]]:
        """Load all steps from an execution"""
        steps = self._load_evidence(execution_id)

        if not steps:
            return []

        # Deduplicate but track occurrences
        unique_steps = {}
        step_counts = {}

        for step in steps:
            step_id = step.get('step_id')
            step_counts[step_id] = step_counts.get(step_id, 0) + 1

            if step_id not in unique_steps:
                unique_steps[step_id] = {
                    **step,
                    "loop_count": 1
                }
            else:
                unique_steps[step_id]["loop_count"] = step_counts[step_id]

        # Sort by step_index
        sorted_steps = sorted(unique_steps.values(), key=lambda s: s.get('step_index', 0))

        return [
            {
                "step_id": s.get('step_id'),
                "step_index": s.get('step_index'),
                "module_id": s.get('module_id'),
                "params": s.get('params', {}),
                "status": s.get('status'),
                "duration_ms": s.get('duration_ms'),
                "has_context": bool(s.get('context_before')),
                "loop_count": s.get('loop_count', 1),
                "error": s.get('error_message'),
                "result_preview": self._get_preview(s.get('result'))
            }
            for s in sorted_steps
        ]

    async def compare_replay(
        self,
        original_execution_id: str,
        replay_execution_id: str
    ) -> Dict[str, Any]:
        """Compare original execution with replay"""
        original_steps = self._load_evidence(original_execution_id)
        replay_steps = self._load_evidence(replay_execution_id)

        if not original_steps:
            return {"error": "Original execution not found"}

        if not replay_steps:
            return {"error": "Replay execution not found"}

        # Build step maps (use first occurrence for comparison)
        original_map = {}
        for s in original_steps:
            sid = s.get('step_id')
            if sid not in original_map:
                original_map[sid] = s

        replay_map = {}
        for s in replay_steps:
            sid = s.get('step_id')
            if sid not in replay_map:
                replay_map[sid] = s

        # Find differences
        differences = []
        all_step_ids = set(original_map.keys()) | set(replay_map.keys())

        for step_id in all_step_ids:
            orig = original_map.get(step_id)
            repl = replay_map.get(step_id)

            if not orig:
                differences.append({
                    "step_id": step_id,
                    "type": "added",
                    "message": "Step added in replay",
                    "replay_result": repl.get('result')
                })
            elif not repl:
                differences.append({
                    "step_id": step_id,
                    "type": "removed",
                    "message": "Step not executed in replay",
                    "original_result": orig.get('result')
                })
            else:
                # Compare results
                orig_result = orig.get('result', {})
                repl_result = repl.get('result', {})

                orig_status = orig.get('status')
                repl_status = repl.get('status')

                if orig_status != repl_status:
                    differences.append({
                        "step_id": step_id,
                        "type": "status_changed",
                        "original_status": orig_status,
                        "replay_status": repl_status,
                        "original_error": orig.get('error_message'),
                        "replay_error": repl.get('error_message')
                    })
                elif self._results_differ(orig_result, repl_result):
                    differences.append({
                        "step_id": step_id,
                        "type": "result_changed",
                        "original_result": self._get_preview(orig_result),
                        "replay_result": self._get_preview(repl_result),
                        "field_diffs": self._get_field_diffs(orig_result, repl_result)
                    })

        # Build summary
        return {
            "original_id": original_execution_id,
            "replay_id": replay_execution_id,
            "differences": differences,
            "difference_count": len(differences),
            "has_differences": len(differences) > 0,
            "original": {
                "step_count": len(original_map),
                "steps": [
                    {
                        "id": s.get('step_id'),
                        "name": s.get('step_id'),
                        "module_id": s.get('module_id'),
                        "status": s.get('status'),
                        "output": s.get('result')
                    }
                    for s in sorted(original_map.values(), key=lambda x: x.get('step_index', 0))
                ]
            },
            "replay": {
                "step_count": len(replay_map),
                "steps": [
                    {
                        "id": s.get('step_id'),
                        "name": s.get('step_id'),
                        "module_id": s.get('module_id'),
                        "status": s.get('status'),
                        "output": s.get('result')
                    }
                    for s in sorted(replay_map.values(), key=lambda x: x.get('step_index', 0))
                ]
            }
        }

    def get_replay_history(
        self,
        execution_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get replay history"""
        if execution_id:
            return [
                h for h in self._history
                if h.get('original_execution_id') == execution_id
            ]
        return self._history

    def add_to_history(
        self,
        original_execution_id: str,
        replay_execution_id: str,
        from_step: Optional[str] = None,
        replay_type: str = "full"
    ):
        """Add a replay to history"""
        entry = {
            "id": replay_execution_id,
            "original_execution_id": original_execution_id,
            "replay_execution_id": replay_execution_id,
            "type": replay_type,
            "from_step": from_step,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._history.append(entry)
        self._save_history()

    def _sanitize_context(self, context: Dict) -> Dict:
        """Remove non-serializable objects from context"""
        sanitized = {}
        for key, value in context.items():
            if isinstance(value, str) and value.startswith('<') and value.endswith('>'):
                # Skip object representations like <BrowserDriver object at 0x...>
                sanitized[key] = "[object]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_context(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_context(v) if isinstance(v, dict) else v
                    for v in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    def _get_preview(self, value: Any, max_length: int = 200) -> Any:
        """Get a preview of a value"""
        if value is None:
            return None
        if isinstance(value, str):
            return value[:max_length] + "..." if len(value) > max_length else value
        if isinstance(value, dict):
            preview = {}
            for k, v in list(value.items())[:10]:
                preview[k] = self._get_preview(v, max_length // 2)
            return preview
        if isinstance(value, list):
            return [self._get_preview(v, max_length // 2) for v in value[:5]]
        return value

    def _results_differ(self, a: Any, b: Any) -> bool:
        """Check if two results are different"""
        if type(a) is not type(b):
            return True
        if isinstance(a, dict) and isinstance(b, dict):
            all_keys = set(a.keys()) | set(b.keys())
            for key in all_keys:
                if key not in a or key not in b:
                    return True
                if self._results_differ(a[key], b[key]):
                    return True
            return False
        if isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                return True
            for i in range(len(a)):
                if self._results_differ(a[i], b[i]):
                    return True
            return False
        return a != b

    def _get_field_diffs(self, a: Dict, b: Dict) -> List[Dict]:
        """Get field-level differences between two dicts"""
        diffs = []
        all_keys = set(a.keys()) | set(b.keys())

        for key in all_keys:
            if key not in a:
                diffs.append({"field": key, "type": "added", "value": b[key]})
            elif key not in b:
                diffs.append({"field": key, "type": "removed", "value": a[key]})
            elif a[key] != b[key]:
                diffs.append({
                    "field": key,
                    "type": "changed",
                    "original": a[key],
                    "replay": b[key]
                })

        return diffs

    async def load_workflow_yaml(self, execution_id: str) -> Optional[str]:
        """
        Load the original workflow YAML from an execution.

        Tries multiple sources:
        1. Runs directory manifest.json
        2. SQLite execution record
        """
        # Try runs directory first
        runs_path = get_runs_path()
        manifest_file = runs_path / execution_id / "manifest.json"

        if manifest_file.exists():
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)

                workflow_snapshot = manifest.get('workflow', {})
                if workflow_snapshot:
                    # Reconstruct YAML from snapshot
                    workflow_data = workflow_snapshot.get('workflow_data', {})
                    if workflow_data:
                        return yaml.dump(workflow_data, default_flow_style=False, allow_unicode=True)
            except Exception as e:
                logger.warning(f"Failed to load workflow from manifest: {e}")

        # Try SQLite
        try:
            from gateway.storage import ExecutionRepository
            execution = ExecutionRepository.get_execution(execution_id)
            if execution and execution.workflow_snapshot:
                workflow_data = execution.workflow_snapshot.get('workflow_data', {})
                if workflow_data:
                    return yaml.dump(workflow_data, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.warning(f"Failed to load workflow from SQLite: {e}")

        # Try to reconstruct from evidence (minimal workflow)
        steps = self._load_evidence(execution_id)
        if steps:
            try:
                # Build a minimal workflow from evidence
                workflow_data = self._reconstruct_workflow(steps)
                if workflow_data:
                    return yaml.dump(workflow_data, default_flow_style=False, allow_unicode=True)
            except Exception as e:
                logger.warning(f"Failed to reconstruct workflow from evidence: {e}")

        return None

    def _reconstruct_workflow(self, steps: List[Dict]) -> Optional[Dict]:
        """
        Reconstruct a minimal workflow from evidence steps.

        This is a fallback when original workflow is not available.
        """
        if not steps:
            return None

        # Deduplicate steps by step_id (keep first occurrence)
        seen_steps = {}
        for step in steps:
            step_id = step.get('step_id')
            if step_id and step_id not in seen_steps:
                seen_steps[step_id] = step

        # Build workflow structure
        workflow_steps = []
        for step_id, step_data in sorted(seen_steps.items(), key=lambda x: x[1].get('step_index', 0)):
            workflow_step = {
                'id': step_id,
                'module': step_data.get('module_id'),
                'params': step_data.get('params', {}),
            }
            workflow_steps.append(workflow_step)

        return {
            'name': 'Reconstructed Workflow',
            'version': '1.0',
            'steps': workflow_steps,
        }

    def get_step_index(self, execution_id: str, step_id: str) -> Optional[int]:
        """Get the step index for a given step_id"""
        steps = self._load_evidence(execution_id)

        for step in steps:
            if step.get('step_id') == step_id:
                return step.get('step_index', 0)

        return None


# Singleton instance
_replay_manager: Optional[EvidenceReplayManager] = None


def get_replay_manager() -> EvidenceReplayManager:
    """Get or create replay manager instance"""
    global _replay_manager
    if _replay_manager is None:
        _replay_manager = EvidenceReplayManager(get_evidence_path())
    return _replay_manager
