"""
Snapshot Service

Creates immutable snapshots of execution context for reproducibility.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.runtime.snapshot.models import (
    ExecutionSnapshot,
    ModuleVersionInfo,
    SecretRef,
    WorkflowSnapshot,
)
from services.runtime.snapshot.environment import get_environment_snapshot, collect_dependencies

logger = logging.getLogger(__name__)


class SnapshotService:
    """Service for creating execution snapshots."""

    # Keys that indicate sensitive data
    SENSITIVE_KEYS = frozenset({
        "password",
        "token",
        "secret",
        "api_key",
        "apikey",
        "auth",
        "credential",
        "private_key",
        "access_key",
        "secret_key",
    })

    @classmethod
    def create_execution_snapshot(
        cls,
        exec_id: str,
        workflow_id: str,
        workflow_name: str,
        workflow_data: Dict[str, Any],
        input_params: Dict[str, Any],
        trigger: Optional[Dict[str, Any]] = None,
    ) -> ExecutionSnapshot:
        """
        Create a complete execution snapshot.

        Args:
            exec_id: Unique execution identifier
            workflow_id: Workflow identifier
            workflow_name: Workflow display name
            workflow_data: Parsed workflow definition
            input_params: Runtime input parameters
            trigger: Trigger information (manual, scheduled, etc.)

        Returns:
            ExecutionSnapshot with all context captured
        """
        now = datetime.now(timezone.utc).isoformat()

        # Create workflow snapshot
        workflow_json = json.dumps(workflow_data, sort_keys=True, default=str)
        workflow_hash = hashlib.sha256(workflow_json.encode()).hexdigest()[:16]

        workflow_snapshot = WorkflowSnapshot(
            id=workflow_id,
            name=workflow_name,
            version=workflow_data.get("version", "1.0.0"),
            content_hash=workflow_hash,
            definition=workflow_data,
        )

        # Collect module versions
        modules = cls.collect_module_versions(workflow_data)

        # Get environment snapshot
        env = get_environment_snapshot()

        # Collect dependencies
        dependencies_lock = collect_dependencies()

        # Extract secret references (no values)
        secrets_refs = cls.extract_secret_refs(input_params)

        # Redact sensitive data from input params
        safe_input_params = cls.redact_sensitive_data(input_params)

        return ExecutionSnapshot(
            exec_id=exec_id,
            workflow=workflow_snapshot,
            modules=modules,
            input_params=safe_input_params,
            env=env,
            dependencies_lock=dependencies_lock,
            secrets_refs=secrets_refs,
            artifacts=[],
            trigger=trigger or {"type": "manual"},
            created_at=now,
        )

    @classmethod
    def collect_module_versions(
        cls, workflow_data: Dict[str, Any]
    ) -> List[ModuleVersionInfo]:
        """
        Extract module information from workflow definition.

        Args:
            workflow_data: Parsed workflow YAML

        Returns:
            List of module version info
        """
        modules = []
        seen_modules = set()

        steps = workflow_data.get("steps", [])
        for step in steps:
            module_id = step.get("module") or step.get("module_id")
            if not module_id or module_id in seen_modules:
                continue

            seen_modules.add(module_id)

            # Create a hash of the step configuration
            step_json = json.dumps(step, sort_keys=True, default=str)
            content_hash = hashlib.sha256(step_json.encode()).hexdigest()[:16]

            modules.append(
                ModuleVersionInfo(
                    module_id=module_id,
                    version="1.0.0",  # Default version
                    content_hash=content_hash,
                )
            )

        return modules

    @classmethod
    def extract_secret_refs(cls, params: Dict[str, Any]) -> List[SecretRef]:
        """
        Extract references to secrets without capturing values.

        Args:
            params: Input parameters that may contain secrets

        Returns:
            List of secret references
        """
        refs = []

        def scan_dict(d: Dict[str, Any], path: str = "") -> None:
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                key_lower = key.lower()

                # Check if key indicates a secret
                if any(s in key_lower for s in cls.SENSITIVE_KEYS):
                    refs.append(
                        SecretRef(
                            name=current_path,
                            scope="input_params",
                            version=None,
                        )
                    )

                # Recurse into nested dicts
                if isinstance(value, dict):
                    scan_dict(value, current_path)

        scan_dict(params)
        return refs

    @classmethod
    def redact_sensitive_data(cls, data: Any) -> Any:
        """
        Redact sensitive values from data.

        Args:
            data: Data that may contain sensitive values

        Returns:
            Data with sensitive values replaced by [REDACTED]
        """
        if data is None:
            return None

        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(s in key_lower for s in cls.SENSITIVE_KEYS):
                    result[key] = "[REDACTED]"
                else:
                    result[key] = cls.redact_sensitive_data(value)
            return result

        if isinstance(data, list):
            return [cls.redact_sensitive_data(item) for item in data]

        return data
