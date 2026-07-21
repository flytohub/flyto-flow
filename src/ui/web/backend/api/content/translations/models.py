"""
Pydantic models for Translation Management API.
"""

from typing import Optional, Dict, List

from pydantic import BaseModel


class TranslationFile(BaseModel):
    """Metadata for a single translation file in a locale."""
    name: str  # e.g., "modules.browser"
    filename: str  # e.g., "modules.browser.json"
    locale: str
    category: str  # "modules" | "cloud" | "common"
    key_count: int
    translated_count: int
    completion: float


class TranslationEntry(BaseModel):
    """A single translation key with source and target values."""
    key: str
    source: str  # English value
    value: str  # Target locale value
    is_empty: bool
    is_modified: bool = False


class UpdateTranslationsRequest(BaseModel):
    """Request body for updating translation key-value pairs."""
    translations: Dict[str, str]


class CreatePRRequest(BaseModel):
    """Request body for creating a GitHub PR with translation changes."""
    title: Optional[str] = None
    description: Optional[str] = None
    files: Dict[str, Dict[str, str]]  # { "filename": { "key": "value" } }


class AITranslateRequest(BaseModel):
    """Request body for AI-powered translation of selected keys."""
    keys: List[str]  # Keys to translate
    source_locale: str = "en"
    target_locale: str
    style: str = "formal"  # "formal" | "casual"


class SaveTranslationsRequest(BaseModel):
    """Request model for saving translations."""
    translations: Dict[str, str]
    commit_message: Optional[str] = None


class ImportTranslationsRequest(BaseModel):
    """Request model for importing translations."""
    translations: Dict[str, str]
    merge: bool = True  # If true, merge with existing; if false, replace
