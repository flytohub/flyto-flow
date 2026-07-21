"""
Variable Repository

Storage layer for workflow variables with scope-based inheritance.
Supports organization, project, and workflow level variables.
"""

import base64
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from gateway.storage.database import get_cursor, get_db

logger = logging.getLogger(__name__)

_table_ensured = False


class VariableScope(str, Enum):
    """Variable scope levels."""

    ORGANIZATION = "organization"
    PROJECT = "project"
    WORKFLOW = "workflow"


class VariableType(str, Enum):
    """Variable value types."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"
    SECRET = "secret"


class Environment(str, Enum):
    """Deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ALL = "all"


@dataclass
class Variable:
    """
    Variable definition.

    Variables are scoped to organization/project/workflow and can be
    environment-specific. Secrets are stored encrypted.
    """

    id: str
    name: str
    value: str
    value_type: VariableType = VariableType.STRING

    # Scope
    scope: VariableScope = VariableScope.WORKFLOW
    scope_id: str = ""
    environment: Environment = Environment.ALL

    # Security
    is_secret: bool = False
    encrypted_value: Optional[str] = None

    # Metadata
    description: Optional[str] = None
    created_by: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self, include_value: bool = True) -> Dict[str, Any]:
        """Convert to dict, optionally excluding value for secrets."""
        data = {
            "id": self.id,
            "name": self.name,
            "value_type": self.value_type.value if isinstance(self.value_type, VariableType) else self.value_type,
            "scope": self.scope.value if isinstance(self.scope, VariableScope) else self.scope,
            "scope_id": self.scope_id,
            "environment": self.environment.value if isinstance(self.environment, Environment) else self.environment,
            "is_secret": self.is_secret,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        if include_value:
            if self.is_secret:
                data["value"] = "[REDACTED]"
            else:
                data["value"] = self.value

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Variable":
        """Create from dict."""
        return cls(
            id=data.get("id", str(uuid4())),
            name=data["name"],
            value=data.get("value", ""),
            value_type=VariableType(data.get("value_type", "string")),
            scope=VariableScope(data.get("scope", "workflow")),
            scope_id=data.get("scope_id", ""),
            environment=Environment(data.get("environment", "all")),
            is_secret=data.get("is_secret", False),
            encrypted_value=data.get("encrypted_value"),
            description=data.get("description"),
            created_by=data.get("created_by"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )


def _ensure_table() -> None:
    """Ensure variables table exists."""
    global _table_ensured
    if _table_ensured:
        return

    with get_cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS variables (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                value TEXT,
                value_type TEXT DEFAULT 'string',
                scope TEXT DEFAULT 'workflow',
                scope_id TEXT NOT NULL,
                environment TEXT DEFAULT 'all',
                is_secret INTEGER DEFAULT 0,
                encrypted_value TEXT,
                description TEXT,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_variables_scope
            ON variables(scope, scope_id, environment)
        """)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_variables_unique_name
            ON variables(scope, scope_id, environment, name)
        """)

    _table_ensured = True


def _encrypt(value: str) -> str:
    """Encrypt a secret value (placeholder - use proper encryption in production)."""
    return base64.b64encode(value.encode()).decode()


def _decrypt(encrypted: str) -> str:
    """Decrypt a secret value (placeholder - use proper encryption in production)."""
    try:
        return base64.b64decode(encrypted.encode()).decode()
    except Exception:
        return ""


def _row_to_variable(row, include_secrets: bool = False) -> Variable:
    """Convert database row to Variable."""
    variable = Variable(
        id=row["id"],
        name=row["name"],
        value=row["value"] or "",
        value_type=VariableType(row["value_type"] or "string"),
        scope=VariableScope(row["scope"] or "workflow"),
        scope_id=row["scope_id"] or "",
        environment=Environment(row["environment"] or "all"),
        is_secret=bool(row["is_secret"]),
        encrypted_value=row["encrypted_value"],
        description=row["description"],
        created_by=row["created_by"],
        created_at=row["created_at"] or "",
        updated_at=row["updated_at"] or "",
    )

    if variable.is_secret and include_secrets and variable.encrypted_value:
        variable.value = _decrypt(variable.encrypted_value)

    return variable


def _parse_value(variable: Variable) -> Any:
    """Parse variable value based on type."""
    value = variable.value

    if variable.value_type == VariableType.NUMBER:
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    if variable.value_type == VariableType.BOOLEAN:
        return value.lower() in ("true", "1", "yes")

    if variable.value_type == VariableType.JSON:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    return value


class VariableRepository:
    """Repository for variable CRUD operations."""

    @staticmethod
    def create(variable: Variable) -> Variable:
        """Create a new variable."""
        _ensure_table()

        if not variable.id:
            variable.id = str(uuid4())

        now = datetime.now(timezone.utc).isoformat()
        variable.created_at = now
        variable.updated_at = now

        stored_value = variable.value
        if variable.is_secret:
            variable.encrypted_value = _encrypt(variable.value)
            stored_value = ""

        with get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO variables
                (id, name, value, value_type, scope, scope_id, environment,
                 is_secret, encrypted_value, description, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    variable.id,
                    variable.name,
                    stored_value,
                    variable.value_type.value if isinstance(variable.value_type, VariableType) else variable.value_type,
                    variable.scope.value if isinstance(variable.scope, VariableScope) else variable.scope,
                    variable.scope_id,
                    variable.environment.value if isinstance(variable.environment, Environment) else variable.environment,
                    1 if variable.is_secret else 0,
                    variable.encrypted_value,
                    variable.description,
                    variable.created_by,
                    variable.created_at,
                    variable.updated_at,
                ),
            )

        logger.info(f"Created variable: {variable.name} (scope={variable.scope})")
        return variable

    @staticmethod
    def get(variable_id: str) -> Optional[Variable]:
        """Get variable by ID."""
        _ensure_table()

        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM variables WHERE id = ?", (variable_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return _row_to_variable(row)

    @staticmethod
    def get_by_name(
        name: str,
        scope: VariableScope,
        scope_id: str,
        environment: Optional[Environment] = None,
    ) -> Optional[Variable]:
        """Get variable by name within a scope."""
        _ensure_table()

        with get_cursor() as cursor:
            if environment:
                cursor.execute(
                    """
                    SELECT * FROM variables
                    WHERE name = ? AND scope = ? AND scope_id = ?
                    AND (environment = ? OR environment = 'all')
                    ORDER BY CASE environment WHEN ? THEN 0 ELSE 1 END
                    LIMIT 1
                    """,
                    (name, scope.value, scope_id, environment.value, environment.value),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM variables
                    WHERE name = ? AND scope = ? AND scope_id = ?
                    LIMIT 1
                    """,
                    (name, scope.value, scope_id),
                )
            row = cursor.fetchone()

        if not row:
            return None

        return _row_to_variable(row)

    @staticmethod
    def list_variables(
        scope: Optional[VariableScope] = None,
        scope_id: Optional[str] = None,
        environment: Optional[Environment] = None,
        include_secrets: bool = False,
    ) -> List[Variable]:
        """List variables with optional filters."""
        _ensure_table()

        conditions = []
        params = []

        if scope:
            conditions.append("scope = ?")
            params.append(scope.value)

        if scope_id:
            conditions.append("scope_id = ?")
            params.append(scope_id)

        if environment:
            conditions.append("(environment = ? OR environment = 'all')")
            params.append(environment.value)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM variables
                WHERE {where_clause}
                ORDER BY scope, name
                """,
                tuple(params),
            )
            rows = cursor.fetchall()

        return [_row_to_variable(row, include_secrets) for row in rows]

    @staticmethod
    def update(variable_id: str, **kwargs) -> bool:
        """Update variable fields."""
        _ensure_table()

        allowed_fields = {
            "name", "value", "value_type", "environment",
            "is_secret", "description"
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        if "value" in updates and updates.get("is_secret", False):
            updates["encrypted_value"] = _encrypt(updates["value"])
            updates["value"] = ""

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        if "value_type" in updates and isinstance(updates["value_type"], VariableType):
            updates["value_type"] = updates["value_type"].value
        if "environment" in updates and isinstance(updates["environment"], Environment):
            updates["environment"] = updates["environment"].value

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [variable_id]

        with get_cursor() as cursor:
            cursor.execute(
                f"UPDATE variables SET {set_clause} WHERE id = ?",
                tuple(values),
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete(variable_id: str) -> bool:
        """Delete a variable."""
        _ensure_table()

        with get_cursor() as cursor:
            cursor.execute("DELETE FROM variables WHERE id = ?", (variable_id,))
            return cursor.rowcount > 0

    @staticmethod
    def resolve_variables(
        workflow_id: str,
        project_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        environment: Environment = Environment.DEVELOPMENT,
    ) -> Dict[str, Any]:
        """
        Resolve all variables for a workflow execution.

        Inheritance order (lower overrides higher):
        1. Organization variables
        2. Project variables
        3. Workflow variables
        """
        _ensure_table()

        resolved: Dict[str, Any] = {}

        if organization_id:
            org_vars = VariableRepository.list_variables(
                scope=VariableScope.ORGANIZATION,
                scope_id=organization_id,
                environment=environment,
                include_secrets=True,
            )
            for var in org_vars:
                resolved[var.name] = _parse_value(var)

        if project_id:
            proj_vars = VariableRepository.list_variables(
                scope=VariableScope.PROJECT,
                scope_id=project_id,
                environment=environment,
                include_secrets=True,
            )
            for var in proj_vars:
                resolved[var.name] = _parse_value(var)

        wf_vars = VariableRepository.list_variables(
            scope=VariableScope.WORKFLOW,
            scope_id=workflow_id,
            environment=environment,
            include_secrets=True,
        )
        for var in wf_vars:
            resolved[var.name] = _parse_value(var)

        return resolved
