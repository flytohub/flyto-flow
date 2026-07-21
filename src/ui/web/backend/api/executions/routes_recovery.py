"""
Execution Recovery Routes

Resume from checkpoint and failure recovery endpoints.
Uses CheckpointService (wired via engine checkpoint_callback) for checkpoint data.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from api.executions.auth import get_optional_user
from api.executions.models import (
    CheckpointInfo,
    ResumeOptionsResponse,
    ResumeFromCheckpointRequest,
    ResumeFromCheckpointResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{execution_id}/resume-options", response_model=ResumeOptionsResponse)
async def get_resume_options(
    execution_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get available resume options for a failed execution.

    Returns list of checkpoints and recommended resume point.
    """
    from services.runtime.execution_manager import get_execution_manager
    from services.checkpoint_service import get_checkpoint_service

    manager = get_execution_manager()
    checkpoint_service = get_checkpoint_service()

    # Verify execution exists
    status = manager.get_status(execution_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    # Check ownership
    user_id = current_user.get("id") if current_user else None
    exec_user_id = status.get("user_id")

    if user_id and exec_user_id and user_id != exec_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot view resume options for execution owned by another user"
        )

    checkpoints = await checkpoint_service.get_checkpoints(execution_id)

    if not checkpoints:
        return ResumeOptionsResponse(
            ok=True,
            execution_id=execution_id,
            can_resume=False,
            checkpoints=[]
        )

    # Find error checkpoint and recommended resume point
    failure_node = None
    failure_message = None
    recommended_checkpoint = None

    for cp in reversed(checkpoints):
        if cp['status'] == 'failed' and not failure_node:
            failure_node = cp['step_id']
            failure_message = cp.get('data', {}).get('error')
        if cp['status'] == 'success' and not recommended_checkpoint:
            recommended_checkpoint = cp['id']

    return ResumeOptionsResponse(
        ok=True,
        execution_id=execution_id,
        can_resume=len(checkpoints) > 0,
        checkpoints=[
            CheckpointInfo(
                id=cp["id"],
                type="node_complete" if cp["status"] == "success" else "error",
                node_id=cp["step_id"],
                node_index=cp["step_index"],
                timestamp=cp.get("created_at", ""),
                has_error=cp["status"] == "failed"
            )
            for cp in checkpoints
        ],
        recommended_checkpoint=recommended_checkpoint,
        failure_node=failure_node,
        failure_message=failure_message
    )


@router.post("/{execution_id}/resume-from-checkpoint", response_model=ResumeFromCheckpointResponse)
async def resume_from_checkpoint(
    execution_id: str,
    request: ResumeFromCheckpointRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Resume execution from a saved checkpoint.

    Starts a new execution from the step after the checkpoint,
    injecting the checkpoint's context as initial_context.
    Optionally allows modifying variables before resume.
    """
    from services.runtime.execution_manager import get_execution_manager
    from services.checkpoint_service import get_checkpoint_service

    manager = get_execution_manager()
    checkpoint_service = get_checkpoint_service()

    # Verify execution exists
    status = manager.get_status(execution_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    # Check ownership
    user_id = current_user.get("id") if current_user else None
    exec_user_id = status.get("user_id")

    if user_id and exec_user_id and user_id != exec_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot resume execution owned by another user"
        )

    # Get the target checkpoint
    if request.checkpoint_id:
        checkpoint = await checkpoint_service.get_checkpoint(
            execution_id, step_id=request.checkpoint_id.split("_")[-1]
        )
        # Try exact match if step_id extraction failed
        if not checkpoint:
            all_checkpoints = await checkpoint_service.get_checkpoints(execution_id)
            for cp in all_checkpoints:
                if cp['id'] == request.checkpoint_id:
                    checkpoint = cp
                    break
    else:
        # Use latest successful checkpoint
        checkpoint = await checkpoint_service.get_latest_successful_checkpoint(execution_id)

    if not checkpoint:
        return ResumeFromCheckpointResponse(
            ok=False,
            message="No checkpoint available for resume"
        )

    # Extract resume data from checkpoint
    checkpoint_data = checkpoint.get('data', {})
    context = checkpoint_data.get('context', {})
    workflow_yaml = checkpoint_data.get('workflow_yaml', '')
    resume_step_index = checkpoint['step_index'] + 1  # Start from next step

    if not workflow_yaml:
        # Try to load workflow_yaml from replay services
        try:
            from api.replay.services import get_replay_manager
            replay_manager = get_replay_manager()
            workflow_yaml = await replay_manager.load_workflow_yaml(execution_id)
        except Exception as e:
            logger.warning(f"Failed to load workflow_yaml from replay manager: {e}")

    if not workflow_yaml:
        return ResumeFromCheckpointResponse(
            ok=False,
            message="Cannot resume: workflow definition not found in checkpoint or execution records"
        )

    # Apply modified variables if provided
    if request.modified_variables:
        context.update(request.modified_variables)

    try:
        # Start new execution from checkpoint
        new_execution_id = await manager.start(
            workflow_yaml=workflow_yaml,
            variables=checkpoint_data.get('params', {}),
            user_id=user_id,
            start_step=resume_step_index,
            initial_context=context,
            workflow_name=f"Resume from {checkpoint['step_id']}",
        )

        return ResumeFromCheckpointResponse(
            ok=True,
            new_execution_id=new_execution_id,
            message=f"Resumed execution from step {checkpoint['step_id']} (index {resume_step_index})"
        )

    except Exception as e:
        logger.error(f"Failed to resume execution: {e}")
        return ResumeFromCheckpointResponse(
            ok=False,
            message=f"Failed to resume: {str(e)}"
        )
