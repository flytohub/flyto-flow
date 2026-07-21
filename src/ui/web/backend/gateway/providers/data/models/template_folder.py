"""Template Folder DTO Models"""

from typing import Optional
from pydantic import BaseModel


class TemplateFolderDTO(BaseModel):
    """Folder for organizing templates."""
    id: str
    name: str
    parent_id: Optional[str] = None
    tab: str  # "created" | "installed"
    color: Optional[str] = None
    order: int = 0
    created_at: str = ""
    updated_at: str = ""
