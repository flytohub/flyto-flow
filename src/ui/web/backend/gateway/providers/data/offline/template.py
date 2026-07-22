"""SQLite workflow-template CRUD for the single local CE workspace."""

import json
import uuid
from datetime import datetime, timezone

from gateway.providers.data.models import (
    PaginatedResponse,
    TemplateCreateDTO,
    TemplateDTO,
    TemplateUpdateDTO,
)
from gateway.storage.offline_db import get_offline_cursor


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso() -> str:
    return _utc_now().isoformat()


def _parse_dt(value: str | None) -> datetime:
    if value:
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            pass
    return _utc_now()


def _workflow_data(data: TemplateCreateDTO | TemplateUpdateDTO, existing=None) -> dict:
    result = dict(existing or {})
    if data.workflow_data is not None:
        result.update(data.workflow_data)
    for field in ("steps", "ui", "input_schema", "output_schema", "checkpoints", "error_handling", "error_workflow_id"):
        value = getattr(data, field)
        if value is not None:
            result[field] = value
    return result


class OfflineTemplateProvider:
    """Local workflow definitions backed by SQLite."""

    async def list_workspace_templates(
        self,
        workspace_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM templates WHERE workspace_id = ? ORDER BY updated_at DESC",
                (workspace_id,),
            )
            rows = cursor.fetchall()
        start = (page - 1) * page_size
        end = start + page_size
        return PaginatedResponse(
            items=[self._row_to_dto(row) for row in rows[start:end]],
            total=len(rows),
            page=page,
            page_size=page_size,
            has_next=end < len(rows),
            has_prev=page > 1,
        )

    async def get_template(self, template_id: str, workspace_id: str | None = None) -> TemplateDTO | None:
        with get_offline_cursor() as cursor:
            if workspace_id:
                cursor.execute(
                    "SELECT * FROM templates WHERE id = ? AND workspace_id = ?",
                    (template_id, workspace_id),
                )
            else:
                cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
            row = cursor.fetchone()
        return self._row_to_dto(row) if row else None

    async def create_template(self, workspace_id: str, data: TemplateCreateDTO) -> TemplateDTO:
        template_id = str(uuid.uuid4())
        now = _utc_iso()
        with get_offline_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO templates (
                    id, workspace_id, name, description, category, tags,
                    workflow_data, params_schema, color, version,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    template_id,
                    workspace_id,
                    data.name,
                    data.description,
                    data.category,
                    json.dumps(data.tags),
                    json.dumps(_workflow_data(data)),
                    json.dumps(data.params_schema),
                    data.color,
                    now,
                    now,
                ),
            )
        return await self.get_template(template_id)  # type: ignore[return-value]

    async def update_template(
        self,
        workspace_id: str,
        template_id: str,
        data: TemplateUpdateDTO,
    ) -> TemplateDTO | None:
        existing = await self.get_template(template_id, workspace_id)
        if not existing:
            return None

        sets: list[str] = []
        params: list = []
        for field, column, encoder in (
            ("name", "name", None),
            ("description", "description", None),
            ("category", "category", None),
            ("tags", "tags", json.dumps),
            ("color", "color", None),
            ("params_schema", "params_schema", json.dumps),
        ):
            value = getattr(data, field)
            if value is not None:
                sets.append(f"{column} = ?")
                params.append(encoder(value) if encoder else value)

        workflow_fields = (
            data.workflow_data,
            data.steps,
            data.ui,
            data.input_schema,
            data.output_schema,
            data.checkpoints,
            data.error_handling,
            data.error_workflow_id,
        )
        if any(value is not None for value in workflow_fields):
            sets.extend(("workflow_data = ?", "version = version + 1"))
            params.append(json.dumps(_workflow_data(data, existing.workflow_data)))

        if not sets:
            return existing
        sets.append("updated_at = ?")
        params.extend((_utc_iso(), template_id, workspace_id))
        with get_offline_cursor() as cursor:
            cursor.execute(
                f"UPDATE templates SET {', '.join(sets)} WHERE id = ? AND workspace_id = ?",
                tuple(params),
            )
        return await self.get_template(template_id, workspace_id)

    async def delete_template(self, workspace_id: str, template_id: str) -> bool:
        with get_offline_cursor() as cursor:
            cursor.execute(
                "DELETE FROM templates WHERE id = ? AND workspace_id = ?",
                (template_id, workspace_id),
            )
            return cursor.rowcount > 0

    async def update_template_schemas(self, template_id: str, schemas: dict) -> bool:
        template = await self.get_template(template_id)
        if not template:
            return False
        params_schema = schemas.get("params_schema", template.params_schema)
        workflow_data = dict(template.workflow_data)
        if "output_schema" in schemas:
            workflow_data["output_schema"] = schemas["output_schema"]
        with get_offline_cursor() as cursor:
            cursor.execute(
                "UPDATE templates SET params_schema = ?, workflow_data = ?, updated_at = ? WHERE id = ?",
                (json.dumps(params_schema), json.dumps(workflow_data), _utc_iso(), template_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_dto(row: dict) -> TemplateDTO:
        workflow_data = json.loads(row.get("workflow_data") or "{}")
        return TemplateDTO(
            id=row["id"],
            name=row["name"],
            description=row.get("description"),
            version=str(row.get("version", 1)),
            category=row.get("category"),
            tags=json.loads(row.get("tags") or "[]"),
            color=row.get("color"),
            steps=workflow_data.get("steps", []),
            ui=workflow_data.get("ui"),
            workflow_data=workflow_data,
            params_schema=json.loads(row.get("params_schema") or "{}"),
            input_schema=workflow_data.get("input_schema"),
            output_schema=workflow_data.get("output_schema"),
            checkpoints=workflow_data.get("checkpoints", []),
            error_workflow_id=workflow_data.get("error_workflow_id"),
            error_handling=workflow_data.get("error_handling"),
            created_at=_parse_dt(row.get("created_at")),
            updated_at=_parse_dt(row.get("updated_at")),
        )
