"""
Offline Template Provider

SQLite-based template CRUD for offline/desktop mode.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from gateway.providers.data.base import TemplateProvider
from gateway.providers.data.models import (
    TemplateDTO,
    TemplateCreateDTO,
    TemplateUpdateDTO,
    ExecutionDTO,
    ExecutionStatus,
    PaginatedResponse,
    DataSource,
)
from gateway.providers.data.models.template_folder import TemplateFolderDTO
from gateway.storage.offline_db import get_offline_cursor
from gateway.storage.execution_repo import ExecutionRepository

logger = logging.getLogger(__name__)
MAX_FOLDER_DEPTH = 3


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso() -> str:
    return _utc_now().isoformat()


def _parse_dt(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class OfflineTemplateProvider(TemplateProvider):
    """Offline implementation — SQLite-backed template provider."""

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    async def list_user_templates(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM templates WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            )
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

    async def list_public_templates(
        self,
        category: str = None,
        tags: List[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        with get_offline_cursor() as cursor:
            sql = "SELECT * FROM templates WHERE is_public = 1"
            params: list = []
            if category:
                sql += " AND category = ?"
                params.append(category)
            sql += " ORDER BY updated_at DESC"
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

        # Client-side tag filter (tags stored as JSON array)
        if tags:
            tag_set = set(tags)
            rows = [
                r for r in rows
                if tag_set.intersection(json.loads(r.get("tags") or "[]"))
            ]

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

    # ------------------------------------------------------------------
    # Get / Create / Update / Delete
    # ------------------------------------------------------------------

    async def get_template(
        self,
        template_id: str,
        user_id: str = None,
    ) -> Optional[TemplateDTO]:
        with get_offline_cursor() as cursor:
            if user_id:
                cursor.execute(
                    "SELECT * FROM templates WHERE id = ? AND (user_id = ? OR is_public = 1)",
                    (template_id, user_id),
                )
            else:
                cursor.execute(
                    "SELECT * FROM templates WHERE id = ?",
                    (template_id,),
                )
            row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_dto(row)

    async def create_template(
        self,
        user_id: str,
        data: TemplateCreateDTO,
    ) -> TemplateDTO:
        tpl_id = str(uuid.uuid4())
        now = _utc_iso()

        # Merge steps/ui/workflow_data into a single workflow_data blob
        workflow_data = data.workflow_data or {}
        if data.steps:
            workflow_data["steps"] = data.steps
        if data.ui:
            workflow_data["ui"] = data.ui
        if data.input_schema:
            workflow_data["input_schema"] = data.input_schema
        if data.output_schema:
            workflow_data["output_schema"] = data.output_schema
        if data.checkpoints:
            workflow_data["checkpoints"] = data.checkpoints
        if data.error_handling:
            workflow_data["error_handling"] = data.error_handling
        if data.error_workflow_id:
            workflow_data["error_workflow_id"] = data.error_workflow_id

        is_public = 1 if data.visibility == "public" else 0

        with get_offline_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO templates (
                    id, user_id, name, description, category, tags,
                    folder_id, workflow_data, params_schema, icon, color,
                    is_public, version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    tpl_id,
                    user_id,
                    data.name,
                    data.description,
                    data.category,
                    json.dumps(data.tags or []),
                    data.folder_id,
                    json.dumps(workflow_data),
                    json.dumps(data.params_schema or {}),
                    data.icon_url,
                    None,  # color not in create DTO
                    is_public,
                    now,
                    now,
                ),
            )

        return await self.get_template(tpl_id)  # type: ignore[return-value]

    async def update_template(
        self,
        user_id: str,
        template_id: str,
        data: TemplateUpdateDTO,
    ) -> Optional[TemplateDTO]:
        existing = await self.get_template(template_id, user_id)
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
        if data.category is not None:
            sets.append("category = ?")
            params.append(data.category)
        if data.tags is not None:
            sets.append("tags = ?")
            params.append(json.dumps(data.tags))
        if data.icon_url is not None:
            sets.append("icon = ?")
            params.append(data.icon_url)
        if data.color is not None:
            sets.append("color = ?")
            params.append(data.color)
        if data.folder_id is not None:
            sets.append("folder_id = ?")
            params.append(data.folder_id)

        # Visibility
        if data.visibility is not None:
            sets.append("is_public = ?")
            params.append(1 if data.visibility == "public" else 0)
        if data.is_public is not None:
            sets.append("is_public = ?")
            params.append(1 if data.is_public else 0)

        # Version bump
        if data.steps is not None or data.ui is not None or data.workflow_data is not None:
            # Rebuild workflow_data blob
            current_wd = json.loads(existing.workflow_data or "{}") if isinstance(existing.workflow_data, str) else (existing.workflow_data or {})
            if data.steps is not None:
                current_wd["steps"] = data.steps
            if data.ui is not None:
                current_wd["ui"] = data.ui
            if data.workflow_data is not None:
                current_wd.update(data.workflow_data)
            if data.input_schema is not None:
                current_wd["input_schema"] = data.input_schema
            if data.output_schema is not None:
                current_wd["output_schema"] = data.output_schema
            if data.checkpoints is not None:
                current_wd["checkpoints"] = data.checkpoints
            if data.error_handling is not None:
                current_wd["error_handling"] = data.error_handling
            if data.error_workflow_id is not None:
                current_wd["error_workflow_id"] = data.error_workflow_id
            sets.append("workflow_data = ?")
            params.append(json.dumps(current_wd))
            sets.append("version = version + 1")

        if data.params_schema is not None:
            sets.append("params_schema = ?")
            params.append(json.dumps(data.params_schema))

        if not sets:
            return existing

        sets.append("updated_at = ?")
        params.append(_utc_iso())
        params.extend([template_id, user_id])

        with get_offline_cursor() as cursor:
            cursor.execute(
                f"UPDATE templates SET {', '.join(sets)} WHERE id = ? AND user_id = ?",
                tuple(params),
            )

        return await self.get_template(template_id, user_id)

    async def delete_template(
        self,
        user_id: str,
        template_id: str,
    ) -> bool:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "DELETE FROM templates WHERE id = ? AND user_id = ?",
                (template_id, user_id),
            )
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Folders
    # ------------------------------------------------------------------

    async def list_folders(self, user_id: str, tab: str) -> List[TemplateFolderDTO]:
        """Return template folders for a user/tab."""
        with get_offline_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM template_folders
                WHERE user_id = ? AND tab = ?
                ORDER BY order_index ASC, name ASC
                """,
                (user_id, tab),
            )
            rows = cursor.fetchall()
        return [self._folder_row_to_dto(row) for row in rows]

    async def create_folder(
        self,
        user_id: str,
        name: str,
        tab: str,
        parent_id: Optional[str] = None,
        color: Optional[str] = None,
    ) -> TemplateFolderDTO:
        """Create a template folder in offline SQLite."""
        if self._get_folder_depth(user_id, parent_id) > MAX_FOLDER_DEPTH:
            raise ValueError(f"Maximum folder depth ({MAX_FOLDER_DEPTH}) exceeded")

        folder_id = str(uuid.uuid4())
        now = _utc_iso()
        with get_offline_cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(MAX(order_index), -1) AS max_order
                FROM template_folders
                WHERE user_id = ? AND tab = ? AND parent_id IS ?
                """,
                (user_id, tab, parent_id),
            )
            row = cursor.fetchone() or {"max_order": -1}
            order_index = int(row.get("max_order") or -1) + 1
            cursor.execute(
                """
                INSERT INTO template_folders (
                    id, user_id, name, parent_id, tab, color,
                    order_index, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (folder_id, user_id, name, parent_id, tab, color, order_index, now, now),
            )

        return TemplateFolderDTO(
            id=folder_id,
            name=name,
            parent_id=parent_id,
            tab=tab,
            color=color,
            order=order_index,
            created_at=now,
            updated_at=now,
        )

    async def folder_exists(self, user_id: str, folder_id: str) -> bool:
        """Return whether a folder exists for the given user."""
        with get_offline_cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM template_folders WHERE user_id = ? AND id = ?",
                (user_id, folder_id),
            )
            return cursor.fetchone() is not None

    def _get_folder_depth(self, user_id: str, parent_id: Optional[str]) -> int:
        depth = 1
        current = parent_id
        visited: set[str] = set()
        with get_offline_cursor() as cursor:
            while current:
                if current in visited:
                    break
                visited.add(current)
                cursor.execute(
                    "SELECT parent_id FROM template_folders WHERE user_id = ? AND id = ?",
                    (user_id, current),
                )
                row = cursor.fetchone()
                if not row:
                    break
                depth += 1
                current = row.get("parent_id")
        return depth

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    async def execute_template(
        self,
        user_id: str,
        template_id: str,
        params: dict = None,
    ) -> ExecutionDTO:
        tpl = await self.get_template(template_id, user_id)
        tpl_name = tpl.name if tpl else "Untitled"

        execution = ExecutionRepository.create_execution(
            workflow_id=template_id,
            workflow_name=tpl_name,
            user_id=user_id,
            input_params=params or {},
        )

        return ExecutionDTO(
            id=execution.id,
            workflow_id=template_id,
            user_id=user_id,
            status=ExecutionStatus.PENDING,
            started_at=_utc_now(),
            input_params=params or {},
        )

    # ------------------------------------------------------------------
    # Marketplace methods — not applicable offline
    # ------------------------------------------------------------------

    async def update_marketplace_snapshot(
        self,
        user_id: str,
        template_id: str,
    ) -> bool:
        return False

    async def update_template_schemas(
        self,
        template_id: str,
        schemas: dict,
    ) -> bool:
        with get_offline_cursor() as cursor:
            sets = []
            params: list = []
            if "params_schema" in schemas:
                sets.append("params_schema = ?")
                params.append(json.dumps(schemas["params_schema"]))
            if "output_schema" in schemas:
                # Store in workflow_data blob
                cursor.execute(
                    "SELECT workflow_data FROM templates WHERE id = ?",
                    (template_id,),
                )
                row = cursor.fetchone()
                if row:
                    wd = json.loads(row.get("workflow_data") or "{}")
                    wd["output_schema"] = schemas["output_schema"]
                    sets.append("workflow_data = ?")
                    params.append(json.dumps(wd))
            if not sets:
                return False
            sets.append("updated_at = ?")
            params.append(_utc_iso())
            params.append(template_id)
            cursor.execute(
                f"UPDATE templates SET {', '.join(sets)} WHERE id = ?",
                tuple(params),
            )
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dto(row: dict) -> TemplateDTO:
        """Map SQLite row to TemplateDTO."""
        workflow_data = json.loads(row.get("workflow_data") or "{}")
        tags = json.loads(row.get("tags") or "[]")
        params_schema = json.loads(row.get("params_schema") or "{}")

        is_public = bool(row.get("is_public", 0))
        created_at = _parse_dt(row.get("created_at")) or _utc_now()
        updated_at = _parse_dt(row.get("updated_at")) or _utc_now()

        return TemplateDTO(
            id=row["id"],
            name=row["name"],
            description=row.get("description"),
            version=str(row.get("version", 1)),
            author_id=row.get("user_id"),
            creator_id=row.get("user_id"),
            folder_id=row.get("folder_id"),
            category=row.get("category"),
            tags=tags,
            source=DataSource.USER,
            visibility="public" if is_public else "private",
            is_public=is_public,
            pricing="free",
            steps=workflow_data.get("steps", []),
            ui=workflow_data.get("ui"),
            workflow_data=workflow_data,
            icon_url=row.get("icon"),
            color=row.get("color"),
            created_at=created_at,
            updated_at=updated_at,
            params_schema=params_schema,
            input_schema=workflow_data.get("input_schema"),
            output_schema=workflow_data.get("output_schema"),
            checkpoints=workflow_data.get("checkpoints"),
            error_workflow_id=workflow_data.get("error_workflow_id"),
            error_handling=workflow_data.get("error_handling"),
            capabilities={
                "execute": True,
                "edit": True,
                "delete": True,
                "share": False,
                "publish": False,
                "install": False,
            },
        )

    @staticmethod
    def _folder_row_to_dto(row: dict) -> TemplateFolderDTO:
        """Map SQLite folder row to TemplateFolderDTO."""
        return TemplateFolderDTO(
            id=row["id"],
            name=row["name"],
            parent_id=row.get("parent_id"),
            tab=row["tab"],
            color=row.get("color"),
            order=int(row.get("order_index") or 0),
            created_at=row.get("created_at") or "",
            updated_at=row.get("updated_at") or "",
        )
