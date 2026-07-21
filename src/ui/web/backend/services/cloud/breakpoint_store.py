"""Provider-neutral durable breakpoint store adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from gateway.providers.data.providers.breakpoint_provider import (
    BreakpointProvider,
    BreakpointRecord,
    BreakpointResponseRecord,
)

from .breakpoint_models import (
    ApprovalMode,
    ApprovalResponse,
    BreakpointRequest,
    BreakpointResult,
    BreakpointStatus,
)


def _request_to_record(request: BreakpointRequest) -> BreakpointRecord:
    return BreakpointRecord(
        breakpoint_id=request.breakpoint_id,
        execution_id=request.execution_id,
        step_id=request.step_id,
        workflow_id=request.workflow_id,
        title=request.title,
        description=request.description,
        required_approvers=request.required_approvers,
        approval_mode=request.approval_mode.value,
        timeout_seconds=request.timeout_seconds,
        created_at=request.created_at,
        expires_at=request.expires_at,
        context_snapshot=request.context_snapshot,
        custom_fields=request.custom_fields,
        metadata=request.metadata,
        status=BreakpointStatus.PENDING.value,
    )


def _record_to_request(record: BreakpointRecord) -> BreakpointRequest:
    return BreakpointRequest(
        breakpoint_id=record.breakpoint_id,
        execution_id=record.execution_id,
        step_id=record.step_id,
        workflow_id=record.workflow_id,
        title=record.title,
        description=record.description,
        required_approvers=record.required_approvers,
        approval_mode=ApprovalMode(record.approval_mode),
        timeout_seconds=record.timeout_seconds,
        created_at=record.created_at or datetime.now(timezone.utc),
        expires_at=record.expires_at,
        context_snapshot=record.context_snapshot,
        custom_fields=record.custom_fields,
        metadata=record.metadata,
    )


def _response_to_record(response: ApprovalResponse) -> BreakpointResponseRecord:
    return BreakpointResponseRecord(
        breakpoint_id=response.breakpoint_id,
        approved=response.approved,
        user_id=response.user_id,
        comment=response.comment,
        custom_inputs=response.custom_inputs,
        responded_at=response.responded_at,
    )


def _record_to_response(record: BreakpointResponseRecord) -> ApprovalResponse:
    return ApprovalResponse(
        breakpoint_id=record.breakpoint_id,
        approved=record.approved,
        user_id=record.user_id,
        comment=record.comment,
        custom_inputs=record.custom_inputs,
        responded_at=record.responded_at or datetime.now(timezone.utc),
    )


class ProviderBreakpointStore:
    """Adapt the breakpoint domain model to the configured data provider."""

    def __init__(self, provider: Optional[BreakpointProvider] = None):
        self._provider = provider

    @property
    def provider(self) -> BreakpointProvider:
        if self._provider is None:
            from gateway.providers.hub import get_data_provider

            data_provider = get_data_provider()
            if data_provider is None:
                raise RuntimeError("Breakpoint persistence is unavailable in local mode")
            self._provider = data_provider.breakpoints
        return self._provider

    async def save(self, request: BreakpointRequest) -> None:
        await self.provider.save(_request_to_record(request))

    async def load(self, breakpoint_id: str) -> Optional[BreakpointRequest]:
        record = await self.provider.get(breakpoint_id)
        return _record_to_request(record) if record else None

    async def list_pending(
        self,
        execution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        include_unassigned: bool = True,
    ) -> list[BreakpointRequest]:
        records = await self.provider.list_pending(execution_id)
        requests = [_record_to_request(record) for record in records]
        if not user_id:
            return requests

        visible: list[BreakpointRequest] = []
        for request in requests:
            if request.required_approvers:
                if user_id not in request.required_approvers:
                    continue
            elif not include_unassigned:
                continue
            visible.append(request)
        return visible

    async def update_status(
        self,
        breakpoint_id: str,
        status: BreakpointStatus,
    ) -> None:
        await self.provider.update_status(
            breakpoint_id,
            status.value,
            datetime.now(timezone.utc),
        )

    async def save_response(self, response: ApprovalResponse) -> None:
        await self.provider.create_response(_response_to_record(response))

    async def replace_response(self, response: ApprovalResponse) -> None:
        await self.provider.replace_response(_response_to_record(response))

    async def get_responses(self, breakpoint_id: str) -> list[ApprovalResponse]:
        records = await self.provider.list_responses(breakpoint_id)
        return [_record_to_response(record) for record in records]

    async def get_doc_status(
        self,
        breakpoint_id: str,
    ) -> Optional[BreakpointStatus]:
        record = await self.provider.get(breakpoint_id)
        return BreakpointStatus(record.status) if record else None

    async def get_resolved_result(
        self,
        breakpoint_id: str,
    ) -> Optional[BreakpointResult]:
        record = await self.provider.get(breakpoint_id)
        if not record or record.status == BreakpointStatus.PENDING.value:
            return None
        return BreakpointResult(
            breakpoint_id=breakpoint_id,
            status=BreakpointStatus(record.status),
            responses=await self.get_responses(breakpoint_id),
            resolved_at=record.resolved_at or datetime.now(timezone.utc),
        )

    async def delete(self, breakpoint_id: str) -> None:
        await self.provider.delete(breakpoint_id)
