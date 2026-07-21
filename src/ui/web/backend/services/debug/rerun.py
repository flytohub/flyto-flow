"""
Debug Rerun

Replay and rerun operations for execution debugging.
"""

import logging
from typing import Any, Dict, Optional

from services.debug.models import RerunMode, RerunResult

logger = logging.getLogger(__name__)


async def replay_execution(
    execution_id: str,
    override_inputs: Optional[Dict[str, Any]] = None,
) -> RerunResult:
    """
    Replay an entire execution with same (or overridden) inputs.

    Args:
        execution_id: Original execution to replay
        override_inputs: Optional input overrides

    Returns:
        RerunResult with new execution ID
    """
    from gateway.storage.execution_repo import ExecutionRepository
    from services.runtime.execution_manager import get_execution_manager
    import yaml

    # Get original execution
    execution = ExecutionRepository.get_execution(execution_id)

    if not execution:
        return RerunResult(
            success=False,
            error=f"Execution {execution_id} not found",
        )

    if not execution.workflow_snapshot:
        return RerunResult(
            success=False,
            error="No workflow snapshot available for replay",
        )

    # Merge inputs
    inputs = execution.input_params or {}
    if override_inputs:
        inputs = {**inputs, **override_inputs}

    # Convert workflow snapshot to YAML
    workflow_yaml = yaml.dump(execution.workflow_snapshot)

    # Start new execution
    try:
        manager = get_execution_manager()
        new_exec_id = await manager.start(
            workflow_yaml=workflow_yaml,
            variables=inputs,
            workflow_id=execution.workflow_id,
            user_id=execution.user_id,
            workflow_name=execution.workflow_name,
        )

        return RerunResult(
            success=True,
            new_execution_id=new_exec_id,
            original_execution_id=execution_id,
            mode=RerunMode.REPLAY,
        )

    except Exception as e:
        logger.error(f"Failed to replay execution: {e}")
        return RerunResult(
            success=False,
            original_execution_id=execution_id,
            error=str(e),
        )


async def rerun_from_node(
    execution_id: str,
    node_id: str,
    mode: RerunMode = RerunMode.REHYDRATE,
    override_inputs: Optional[Dict[str, Any]] = None,
) -> RerunResult:
    """
    Rerun execution starting from a specific node.

    REHYDRATE mode: Inject outputs from previous steps, run from node_id
    RECOMPUTE mode: Rerun all dependencies of node_id

    Args:
        execution_id: Original execution
        node_id: Node to start from
        mode: Rerun mode
        override_inputs: Optional input overrides

    Returns:
        RerunResult with new execution ID
    """
    from gateway.storage.execution_repo import ExecutionRepository
    from services.runtime.execution_manager import get_execution_manager
    import yaml

    # Get original execution with steps
    execution = ExecutionRepository.get_execution(
        execution_id,
        include_steps=True,
    )

    if not execution:
        return RerunResult(
            success=False,
            error=f"Execution {execution_id} not found",
        )

    if not execution.workflow_snapshot:
        return RerunResult(
            success=False,
            error="No workflow snapshot available",
        )

    if not execution.steps:
        return RerunResult(
            success=False,
            error="No step history available",
        )

    # Find the target node
    target_step = None
    target_index = None
    for step in execution.steps:
        if step.step_id == node_id:
            target_step = step
            target_index = step.step_index
            break

    if not target_step:
        return RerunResult(
            success=False,
            error=f"Node {node_id} not found in execution",
        )

    # Build injected outputs for REHYDRATE mode
    injected_outputs = {}
    if mode == RerunMode.REHYDRATE:
        for step in execution.steps:
            if step.step_index is not None and target_index is not None:
                if step.step_index < target_index:
                    if step.output_data and step.status == "success":
                        injected_outputs[step.step_id] = step.output_data

    # Prepare inputs
    inputs = execution.input_params or {}
    if override_inputs:
        inputs = {**inputs, **override_inputs}

    # Add rerun metadata
    inputs["_rerun_from"] = execution_id
    inputs["_rerun_node"] = node_id
    inputs["_rerun_mode"] = mode.value

    if mode == RerunMode.REHYDRATE:
        inputs["_injected_outputs"] = injected_outputs
        inputs["_start_step"] = target_index

    # Convert workflow snapshot to YAML
    workflow_yaml = yaml.dump(execution.workflow_snapshot)

    # Start new execution
    try:
        manager = get_execution_manager()

        # For REHYDRATE, start from specific step
        start_step = target_index if mode == RerunMode.REHYDRATE else None

        new_exec_id = await manager.start(
            workflow_yaml=workflow_yaml,
            variables=inputs,
            workflow_id=execution.workflow_id,
            start_step=start_step,
            user_id=execution.user_id,
            workflow_name=execution.workflow_name,
        )

        return RerunResult(
            success=True,
            new_execution_id=new_exec_id,
            original_execution_id=execution_id,
            mode=mode,
            injected_outputs=injected_outputs,
        )

    except Exception as e:
        logger.error(f"Failed to rerun from node: {e}")
        return RerunResult(
            success=False,
            original_execution_id=execution_id,
            error=str(e),
        )
