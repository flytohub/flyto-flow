"""
Credential Resolver — Create temporary tokens for secretRef parameters.

Extracted from ExecutionManager to keep service.py focused on orchestration.
"""

import logging
from typing import Any, Dict, List, Optional

from services.credentials.models import extract_secret_refs
from services.credentials.service import CredentialService

logger = logging.getLogger(__name__)


async def create_credential_tokens(
    execution_id: str,
    workflow_data: Dict[str, Any],
    workflow_id: str,
    workspace_id: Optional[str],
) -> Dict[str, str]:
    """
    Create temporary tokens for all secretRef parameters in workflow.

    Scans workflow steps for secretRef parameters and creates tokens
    that can be used to resolve credentials during execution.

    Args:
        execution_id: Execution ID
        workflow_data: Parsed workflow data
        workflow_id: Workflow ID (used as scope_id for workflow-scoped credentials)
        workspace_id: Workspace ID for audit

    Returns:
        Dict mapping credential name to token
    """
    tokens = {}

    if not workflow_data or not workflow_data.get('steps'):
        return tokens

    # Collect all secretRef parameters from all steps
    all_refs: List[Dict[str, Any]] = []
    for step in workflow_data.get('steps', []):
        params = step.get('params', {}) or step.get('config', {})
        refs = extract_secret_refs(params, scope_id=workflow_id)
        all_refs.extend(refs)

    if not all_refs:
        return tokens

    # Create tokens for unique credentials
    seen: set = set()
    unique_refs: List[Dict[str, Any]] = []
    for ref in all_refs:
        key = f"{ref['scope']}:{ref['scope_id']}:{ref['name']}"
        if key not in seen:
            seen.add(key)
            unique_refs.append(ref)

    # Create tokens
    tokens = CredentialService.create_tokens_for_execution(
        execution_id=execution_id,
        credential_refs=unique_refs,
        workspace_id=workspace_id or "system",
    )

    return tokens
