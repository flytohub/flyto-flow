"""
Offline Workflow Provider

SQLite-based workflow CRUD and execution management for offline/desktop mode.
Workflow data stored in offline_db; executions delegated to ExecutionRepository.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from gateway.providers.data.base import WorkflowProvider
from gateway.providers.data.models import (
    WorkflowDTO,
    WorkflowCreateDTO,
    WorkflowUpdateDTO,
    WorkflowNode,
    WorkflowEdge,
    ExecutionDTO,
    ExecutionStatus,
    PaginatedResponse,
    DataSource,
    TriggerType,
)
from gateway.storage.offline_db import get_offline_cursor
from gateway.storage.execution_repo import ExecutionRepository

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def _utc_iso() -> str:
    """Get current UTC timestamp as ISO string."""
    return _utc_now().isoformat()


def _parse_dt(val: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string, return None on failure."""
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


def _ensure_workflows_table() -> None:
    """Create workflows table if it does not exist yet."""
    with get_offline_cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                trigger_type TEXT DEFAULT 'manual',
                trigger_config TEXT DEFAULT '{}',
                nodes TEXT DEFAULT '[]',
                edges TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                total_executions INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                error_workflow_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_executed_at TEXT
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflows_user_id ON workflows(user_id)"
        )


# Ensure table exists on module import
_ensure_workflows_table()


class OfflineWorkflowProvider(WorkflowProvider):
    """Offline implementation — SQLite-backed workflow provider."""

    # ------------------------------------------------------------------
    # Workflow CRUD
    # ------------------------------------------------------------------

    async def list_user_workflows(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        enabled: bool = None,
    ) -> PaginatedResponse:
        with get_offline_cursor() as cursor:
            sql = "SELECT * FROM workflows WHERE user_id = ?"
            params: list = [user_id]
            if enabled is not None:
                sql += " AND is_active = ?"
                params.append(1 if enabled else 0)
            sql += " ORDER BY updated_at DESC"

            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        items = [self._row_to_dto(r) for r in rows[start:end]]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=end < total,
            has_prev=page > 1,
        )

    async def get_workflow(
        self,
        user_id: str,
        workflow_id: str,
        include_graph: bool = True,
    ) -> Optional[WorkflowDTO]:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM workflows WHERE id = ? AND user_id = ?",
                (workflow_id, user_id),
            )
            row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_dto(row, include_graph=include_graph)

    async def create_workflow(
        self,
        user_id: str,
        data: WorkflowCreateDTO,
    ) -> WorkflowDTO:
        wf_id = str(uuid.uuid4())
        now = _utc_iso()
        trigger_type = data.trigger_type.value if isinstance(data.trigger_type, TriggerType) else (data.trigger_type or "manual")

        with get_offline_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO workflows (
                    id, user_id, name, description, is_active,
                    trigger_type, trigger_config,
                    nodes, edges, tags,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    wf_id,
                    user_id,
                    data.name,
                    data.description,
                    trigger_type,
                    json.dumps(data.trigger_config or {}),
                    json.dumps([n.model_dump(by_alias=True) for n in data.nodes]),
                    json.dumps([e.model_dump(by_alias=True) for e in data.edges]),
                    json.dumps(data.tags or []),
                    now,
                    now,
                ),
            )

        return await self.get_workflow(user_id, wf_id)  # type: ignore[return-value]

    async def update_workflow(
        self,
        user_id: str,
        workflow_id: str,
        data: WorkflowUpdateDTO,
    ) -> Optional[WorkflowDTO]:
        existing = await self.get_workflow(user_id, workflow_id)
        if not existing:
            return None

        sets: list[str] = []
        params: list = []

        if data.name is not None:
            sets.append("name = ?")
            params.append(data.name)
        if data.description is not None:
            sets.append("description = ?")
            params.append(data.description)
        if data.is_active is not None:
            sets.append("is_active = ?")
            params.append(1 if data.is_active else 0)
        if data.trigger_type is not None:
            val = data.trigger_type.value if isinstance(data.trigger_type, TriggerType) else data.trigger_type
            sets.append("trigger_type = ?")
            params.append(val)
        if data.trigger_config is not None:
            sets.append("trigger_config = ?")
            params.append(json.dumps(data.trigger_config))
        if data.tags is not None:
            sets.append("tags = ?")
            params.append(json.dumps(data.tags))
        if data.error_workflow_id is not None:
            sets.append("error_workflow_id = ?")
            params.append(data.error_workflow_id)
        if data.nodes is not None:
            sets.append("nodes = ?")
            params.append(json.dumps([n.model_dump(by_alias=True) for n in data.nodes]))
        if data.edges is not None:
            sets.append("edges = ?")
            params.append(json.dumps([e.model_dump(by_alias=True) for e in data.edges]))

        if not sets:
            return existing

        sets.append("updated_at = ?")
        params.append(_utc_iso())
        params.extend([workflow_id, user_id])

        with get_offline_cursor() as cursor:
            cursor.execute(
                f"UPDATE workflows SET {', '.join(sets)} WHERE id = ? AND user_id = ?",
                tuple(params),
            )

        return await self.get_workflow(user_id, workflow_id)

    async def delete_workflow(
        self,
        user_id: str,
        workflow_id: str,
    ) -> bool:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "DELETE FROM workflows WHERE id = ? AND user_id = ?",
                (workflow_id, user_id),
            )
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Execution — delegate to existing ExecutionRepository
    # ------------------------------------------------------------------

    async def execute_workflow(
        self,
        user_id: str,
        workflow_id: str,
        params: dict = None,
    ) -> ExecutionDTO:
        wf = await self.get_workflow(user_id, workflow_id)
        wf_name = wf.name if wf else "Untitled"

        execution = ExecutionRepository.create_execution(
            workflow_id=workflow_id,
            workflow_name=wf_name,
            user_id=user_id,
            input_params=params or {},
        )

        # Bump execution counter
        with get_offline_cursor() as cursor:
            cursor.execute(
                "UPDATE workflows SET total_executions = total_executions + 1, last_executed_at = ? WHERE id = ?",
                (_utc_iso(), workflow_id),
            )

        return ExecutionDTO(
            id=execution.id,
            workflow_id=workflow_id,
            user_id=user_id,
            status=ExecutionStatus.PENDING,
            started_at=_utc_now(),
            input_params=params or {},
        )

    async def list_executions(
        self,
        user_id: str,
        workflow_id: str,
        limit: int = 20,
    ) -> List[ExecutionDTO]:
        executions = ExecutionRepository.list_executions(
            workflow_id=workflow_id,
            user_id=user_id,
            limit=limit,
        )
        return [
            ExecutionDTO(
                id=e.id,
                workflow_id=e.workflow_id,
                user_id=e.user_id or user_id,
                status=ExecutionStatus(e.status),
                started_at=_parse_dt(e.started_at) or _utc_now(),
                finished_at=_parse_dt(e.finished_at),
                duration_ms=e.duration_ms,
                input_params=e.input_params or {},
                result_data=e.result_data,
                error_message=e.error_message,
            )
            for e in executions
        ]

    async def get_execution(
        self,
        user_id: str,
        workflow_id: str,
        execution_id: str,
    ) -> Optional[ExecutionDTO]:
        e = ExecutionRepository.get_execution(execution_id)
        if not e:
            return None
        return ExecutionDTO(
            id=e.id,
            workflow_id=e.workflow_id,
            user_id=e.user_id or user_id,
            status=ExecutionStatus(e.status),
            started_at=_parse_dt(e.started_at) or _utc_now(),
            finished_at=_parse_dt(e.finished_at),
            duration_ms=e.duration_ms,
            input_params=e.input_params or {},
            result_data=e.result_data,
            error_message=e.error_message,
        )

    async def update_execution(
        self,
        user_id: str,
        workflow_id: str,
        execution_id: str,
        status: str,
        result_data: dict = None,
        error_message: str = None,
        finished_at: str = None,
        duration_ms: int = None,
    ) -> bool:
        e = ExecutionRepository.get_execution(execution_id)
        if not e:
            return False

        ExecutionRepository.update_execution(
            execution_id=execution_id,
            status=status,
            result_data=result_data,
            error_message=error_message,
            finished_at=finished_at,
            duration_ms=duration_ms,
        )

        # Update workflow success/failed counts
        if status in ("success", "failed"):
            col = "success_count" if status == "success" else "failed_count"
            with get_offline_cursor() as cursor:
                cursor.execute(
                    f"UPDATE workflows SET {col} = {col} + 1 WHERE id = ?",
                    (workflow_id,),
                )

        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dto(row: dict, include_graph: bool = True) -> WorkflowDTO:
        """Map SQLite row dict to WorkflowDTO."""
        nodes = None
        edges = None

        if include_graph:
            raw_nodes = json.loads(row.get("nodes") or "[]")
            raw_edges = json.loads(row.get("edges") or "[]")
            nodes = [WorkflowNode(**n) for n in raw_nodes] if raw_nodes else []
            edges = [WorkflowEdge(**e) for e in raw_edges] if raw_edges else []

        return WorkflowDTO(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            description=row.get("description"),
            is_active=bool(row.get("is_active", 1)),
            trigger_type=TriggerType(row.get("trigger_type", "manual")),
            trigger_config=json.loads(row.get("trigger_config") or "{}"),
            total_executions=row.get("total_executions", 0),
            success_count=row.get("success_count", 0),
            failed_count=row.get("failed_count", 0),
            created_at=_parse_dt(row.get("created_at")) or _utc_now(),
            updated_at=_parse_dt(row.get("updated_at")) or _utc_now(),
            last_executed_at=_parse_dt(row.get("last_executed_at")),
            nodes=nodes,
            edges=edges,
            source=DataSource.USER,
            tags=json.loads(row.get("tags") or "[]"),
            error_workflow_id=row.get("error_workflow_id"),
            capabilities={
                "execute": True,
                "edit": True,
                "delete": True,
                "share": False,
                "publish": False,
            },
        )
