"""
Cloud Breakpoint Manager

Lightweight breakpoint manager for the cloud API (control plane).
Uses the configured breakpoint provider for persistence.
No dependency on flyto-core.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .breakpoint_models import (
    ApprovalMode,
    ApprovalResponse,
    BreakpointRequest,
    BreakpointResult,
    BreakpointStatus,
)
from .breakpoint_store import ProviderBreakpointStore

logger = logging.getLogger(__name__)


class CloudBreakpointManager:
    """
    Cloud-mode breakpoint manager.

    Unlike the flyto-core BreakpointManager:
    - No asyncio.Event (Cloud Run instances are ephemeral)
    - No wait_for_resolution (workers poll via HTTP)
    - All state in Firestore (survives scale-to-zero)
    """

    def __init__(self, store=None, notifier=None):
        self.store = store or ProviderBreakpointStore()
        self.notifier = notifier
        self._results: Dict[str, BreakpointResult] = {}

    async def create_breakpoint(
        self,
        execution_id: str,
        step_id: str,
        title: str = "Approval Required",
        description: str = "",
        workflow_id: Optional[str] = None,
        required_approvers: Optional[List[str]] = None,
        approval_mode: ApprovalMode = ApprovalMode.SINGLE,
        timeout_seconds: Optional[int] = None,
        context_snapshot: Optional[Dict[str, Any]] = None,
        custom_fields: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BreakpointRequest:
        breakpoint_id = f"bp_{uuid4().hex[:12]}"
        request = BreakpointRequest(
            breakpoint_id=breakpoint_id,
            execution_id=execution_id,
            step_id=step_id,
            workflow_id=workflow_id,
            title=title,
            description=description,
            required_approvers=required_approvers or [],
            approval_mode=approval_mode,
            timeout_seconds=timeout_seconds,
            context_snapshot=context_snapshot or {},
            custom_fields=custom_fields or [],
            metadata=metadata or {},
        )
        await self.store.save(request)
        if self.notifier:
            await self.notifier.notify_pending(request)
        logger.info("Created breakpoint %s for %s/%s", breakpoint_id, execution_id, step_id)
        return request

    async def respond(
        self,
        breakpoint_id: str,
        approved: bool,
        user_id: str,
        comment: Optional[str] = None,
        custom_inputs: Optional[Dict[str, Any]] = None,
    ) -> Optional[BreakpointResult]:
        request = await self.store.load(breakpoint_id)
        if not request:
            raise ValueError(f"Breakpoint not found: {breakpoint_id}")
        if request.is_expired:
            return await self._resolve(breakpoint_id, BreakpointStatus.TIMEOUT)
        if request.required_approvers and user_id not in request.required_approvers:
            raise ValueError(f"User {user_id} is not authorized to approve")
        existing_responses = await self.store.get_responses(breakpoint_id)
        if any(response.user_id == user_id for response in existing_responses):
            raise ValueError("User has already responded to this breakpoint")

        response = ApprovalResponse(
            breakpoint_id=breakpoint_id,
            approved=approved,
            user_id=user_id,
            comment=comment,
            custom_inputs=custom_inputs or {},
        )
        await self.store.save_response(response)
        return await self._check_resolution(request, response)

    async def _check_resolution(
        self,
        request: BreakpointRequest,
        latest_response: ApprovalResponse,
    ) -> Optional[BreakpointResult]:
        all_responses = await self.store.get_responses(request.breakpoint_id)
        mode = request.approval_mode

        if mode in (ApprovalMode.SINGLE, ApprovalMode.FIRST):
            status = BreakpointStatus.APPROVED if latest_response.approved else BreakpointStatus.REJECTED
            return await self._resolve(request.breakpoint_id, status, all_responses, latest_response.custom_inputs)

        if mode == ApprovalMode.ALL:
            if not request.required_approvers:
                status = BreakpointStatus.APPROVED if latest_response.approved else BreakpointStatus.REJECTED
                return await self._resolve(request.breakpoint_id, status, all_responses, latest_response.custom_inputs)
            if not latest_response.approved:
                return await self._resolve(request.breakpoint_id, BreakpointStatus.REJECTED, all_responses, {})
            approved_users = {r.user_id for r in all_responses if r.approved}
            if approved_users >= set(request.required_approvers):
                merged = {}
                for r in all_responses:
                    if r.approved:
                        merged.update(r.custom_inputs)
                return await self._resolve(request.breakpoint_id, BreakpointStatus.APPROVED, all_responses, merged)

        if mode == ApprovalMode.MAJORITY:
            approval_count = len({r.user_id for r in all_responses if r.approved})
            rejection_count = len({r.user_id for r in all_responses if not r.approved})
            total = len(request.required_approvers) or 1
            majority = (total // 2) + 1
            if approval_count >= majority:
                merged = {}
                for r in all_responses:
                    if r.approved:
                        merged.update(r.custom_inputs)
                return await self._resolve(request.breakpoint_id, BreakpointStatus.APPROVED, all_responses, merged)
            if rejection_count >= majority:
                return await self._resolve(request.breakpoint_id, BreakpointStatus.REJECTED, all_responses, {})

        return None

    async def _resolve(
        self,
        breakpoint_id: str,
        status: BreakpointStatus,
        responses: Optional[List[ApprovalResponse]] = None,
        final_inputs: Optional[Dict[str, Any]] = None,
    ) -> BreakpointResult:
        if responses is None:
            responses = await self.store.get_responses(breakpoint_id)
        result = BreakpointResult(
            breakpoint_id=breakpoint_id,
            status=status,
            responses=responses,
            final_inputs=final_inputs or {},
        )
        await self.store.update_status(breakpoint_id, status)
        self._results[breakpoint_id] = result
        if self.notifier:
            await self.notifier.notify_resolved(result)
        logger.info("Resolved breakpoint %s → %s", breakpoint_id, status.value)
        return result

    async def cancel(self, breakpoint_id: str) -> BreakpointResult:
        return await self._resolve(breakpoint_id, BreakpointStatus.CANCELLED)

    async def list_pending(
        self,
        execution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        include_unassigned: bool = True,
    ) -> List[BreakpointRequest]:
        pending = await self.store.list_pending(execution_id, user_id, include_unassigned=include_unassigned)
        active = []
        for req in pending:
            if req.is_expired:
                await self._resolve(req.breakpoint_id, BreakpointStatus.TIMEOUT)
            else:
                active.append(req)
        return active

    async def get_status(self, breakpoint_id: str) -> Optional[BreakpointStatus]:
        if breakpoint_id in self._results:
            return self._results[breakpoint_id].status
        # Check durable storage for cross-instance resolution.
        if hasattr(self.store, "get_doc_status"):
            status = await self.store.get_doc_status(breakpoint_id)
            if status is None:
                return None
            if status != BreakpointStatus.PENDING:
                return status
        request = await self.store.load(breakpoint_id)
        if not request:
            return None
        if request.is_expired:
            result = await self._resolve(breakpoint_id, BreakpointStatus.TIMEOUT)
            return result.status
        return BreakpointStatus.PENDING


# Singleton
_cloud_manager: Optional[CloudBreakpointManager] = None


def get_cloud_breakpoint_manager() -> CloudBreakpointManager:
    global _cloud_manager
    if _cloud_manager is None:
        _cloud_manager = CloudBreakpointManager()
    return _cloud_manager


def set_cloud_breakpoint_manager(manager: CloudBreakpointManager) -> None:
    global _cloud_manager
    _cloud_manager = manager
