"""Small shared data types for the local CE provider boundary."""

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceContext(BaseModel):
    """Fixed local workspace actor used only for resource scoping."""

    id: str
    roles: list[str] = Field(default_factory=list)
    is_admin: bool = True
    is_active: bool = True

    model_config = ConfigDict(frozen=True)
