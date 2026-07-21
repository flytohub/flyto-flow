"""
HuggingFace Installed Models Provider

Manages installed HuggingFace models as workflow-usable presets.

Architecture:
- Models are organized by TASK (not individual modules)
- Each task has a fixed module in core (e.g., huggingface.speech-to-text)
- Installed models are PRESETS for those task modules

Data Flow:
- Plugin Store installs → writes to installed_models.json
- Template Builder reads → gets task modules + installed model presets
- Workflow Engine executes → uses task module with selected model preset

Single Responsibility:
- This service ONLY manages the installed models data layer
- Does NOT handle HuggingFace API calls (that's in plugins/routes.py)
- Does NOT handle execution (that's in core modules)
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Default storage location
FLYTO_HOME = Path.home() / ".flyto"
MODELS_DIR = FLYTO_HOME / "models"
INSTALLED_MODELS_FILE = FLYTO_HOME / "installed_models.json"

# Ensure directories exist
FLYTO_HOME.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class RuntimeMode(str, Enum):
    """How the model should be executed"""
    INFERENCE_API = "inference_api"  # Use HuggingFace Serverless Inference
    LOCAL = "local"                   # Use local transformers pipeline
    AUTO = "auto"                     # Auto-select based on availability


class DownloadStatus(str, Enum):
    """Model download status"""
    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    FAILED = "failed"


# =============================================================================
# Data Models (Schema)
# =============================================================================

@dataclass
class InstalledModel:
    """
    Schema for a single installed HuggingFace model.

    This is a PRESET - a configured instance of a task module.
    """
    # Identity
    model_id: str                           # e.g., "openai/whisper-large-v3"
    task: str                               # e.g., "automatic-speech-recognition"

    # Display
    name: str                               # e.g., "Whisper Large V3"
    author: str                             # e.g., "openai"

    # Status
    download_status: str = DownloadStatus.NOT_DOWNLOADED.value
    downloaded_at: Optional[str] = None     # ISO timestamp
    installed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Storage
    local_path: Optional[str] = None        # Path to downloaded files
    size_bytes: Optional[int] = None        # Model size in bytes

    # Runtime preferences
    preferred_runtime: str = RuntimeMode.AUTO.value

    # Metadata from HuggingFace
    downloads: int = 0
    likes: int = 0
    tags: List[str] = field(default_factory=list)
    pipeline_tag: Optional[str] = None
    library_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InstalledModel':
        """Create from dictionary"""
        # Handle legacy fields
        if 'download_status' not in data:
            data['download_status'] = DownloadStatus.NOT_DOWNLOADED.value
        if 'preferred_runtime' not in data:
            data['preferred_runtime'] = RuntimeMode.AUTO.value

        # Filter to only known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}

        return cls(**filtered_data)


@dataclass
class InstalledModelsStore:
    """
    Root schema for installed_models.json
    """
    version: str = "1.0.0"
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    models: List[InstalledModel] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "version": self.version,
            "updated_at": self.updated_at,
            "models": [m.to_dict() for m in self.models]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InstalledModelsStore':
        """Create from dictionary"""
        models = [InstalledModel.from_dict(m) for m in data.get('models', [])]
        return cls(
            version=data.get('version', '1.0.0'),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            models=models
        )


# =============================================================================
# Service Class
# =============================================================================

class InstalledModelProvider:
    """
    Service for managing installed HuggingFace models.

    This is the single source of truth for:
    - What models are installed
    - What their download status is
    - What runtime mode to use

    Usage:
        provider = get_installed_model_provider()
        models = provider.list_installed()
        models_for_task = provider.list_by_task("automatic-speech-recognition")
    """

    _instance: Optional['InstalledModelProvider'] = None

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize with optional custom storage path for installed_models.json."""
        self._storage_path = storage_path or INSTALLED_MODELS_FILE
        self._cache: Optional[InstalledModelsStore] = None
        self._cache_mtime: Optional[float] = None

    def _load(self) -> InstalledModelsStore:
        """Load from file, with caching"""
        if self._storage_path.exists():
            current_mtime = self._storage_path.stat().st_mtime
            if self._cache is not None and self._cache_mtime == current_mtime:
                return self._cache

        if self._storage_path.exists():
            try:
                data = json.loads(self._storage_path.read_text(encoding='utf-8'))
                self._cache = InstalledModelsStore.from_dict(data)
                self._cache_mtime = self._storage_path.stat().st_mtime
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Invalid installed_models.json, creating new: {e}")
                self._cache = InstalledModelsStore()
        else:
            self._cache = InstalledModelsStore()

        return self._cache

    def _save(self, store: InstalledModelsStore) -> None:
        """Save to file"""
        store.updated_at = datetime.now().isoformat()
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._storage_path.write_text(
            json.dumps(store.to_dict(), indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        self._cache = store
        self._cache_mtime = self._storage_path.stat().st_mtime

    # -------------------------------------------------------------------------
    # Read Operations
    # -------------------------------------------------------------------------

    def list_installed(self) -> List[InstalledModel]:
        """Get all installed models"""
        return self._load().models

    def list_by_task(self, task: str) -> List[InstalledModel]:
        """Get installed models for a specific task"""
        return [m for m in self._load().models if m.task == task]

    def get(self, model_id: str) -> Optional[InstalledModel]:
        """Get a specific installed model by ID"""
        for model in self._load().models:
            if model.model_id == model_id:
                return model
        return None

    def is_installed(self, model_id: str) -> bool:
        """Check if a model is installed"""
        return self.get(model_id) is not None

    def is_downloaded(self, model_id: str) -> bool:
        """Check if a model's files are downloaded locally"""
        model = self.get(model_id)
        return model is not None and model.download_status == DownloadStatus.DOWNLOADED.value

    def get_default_for_task(self, task: str) -> Optional[InstalledModel]:
        """Get the default (first installed) model for a task"""
        models = self.list_by_task(task)
        return models[0] if models else None

    def get_tasks_with_models(self) -> Dict[str, List[InstalledModel]]:
        """Get all tasks that have installed models, grouped by task"""
        tasks: Dict[str, List[InstalledModel]] = {}
        for model in self._load().models:
            if model.task not in tasks:
                tasks[model.task] = []
            tasks[model.task].append(model)
        return tasks

    # -------------------------------------------------------------------------
    # Write Operations
    # -------------------------------------------------------------------------

    def add(self, model: InstalledModel) -> InstalledModel:
        """Add a new installed model. If already exists, updates it."""
        store = self._load()

        for i, existing in enumerate(store.models):
            if existing.model_id == model.model_id:
                store.models[i] = model
                self._save(store)
                logger.info(f"Updated installed model: {model.model_id}")
                return model

        store.models.append(model)
        self._save(store)
        logger.info(f"Added installed model: {model.model_id}")
        return model

    def remove(self, model_id: str) -> bool:
        """Remove an installed model"""
        store = self._load()
        original_count = len(store.models)
        store.models = [m for m in store.models if m.model_id != model_id]

        if len(store.models) < original_count:
            self._save(store)
            logger.info(f"Removed installed model: {model_id}")
            return True
        return False

    def update_download_status(
        self,
        model_id: str,
        status: DownloadStatus,
        local_path: Optional[str] = None,
        size_bytes: Optional[int] = None
    ) -> Optional[InstalledModel]:
        """Update a model's download status"""
        store = self._load()

        for model in store.models:
            if model.model_id == model_id:
                model.download_status = status.value
                if local_path:
                    model.local_path = local_path
                if size_bytes:
                    model.size_bytes = size_bytes
                if status == DownloadStatus.DOWNLOADED:
                    model.downloaded_at = datetime.now().isoformat()
                self._save(store)
                return model

        return None

    def set_preferred_runtime(
        self,
        model_id: str,
        runtime: RuntimeMode
    ) -> Optional[InstalledModel]:
        """Set a model's preferred runtime mode"""
        store = self._load()

        for model in store.models:
            if model.model_id == model_id:
                model.preferred_runtime = runtime.value
                self._save(store)
                return model

        return None

    # -------------------------------------------------------------------------
    # Runtime Policy
    # -------------------------------------------------------------------------

    def get_runtime_policy(
        self,
        model_id: str,
        offline_mode: bool = False,
        user_preference: Optional[RuntimeMode] = None
    ) -> Dict[str, Any]:
        """
        Determine the runtime policy for executing a model.

        Decision order:
        1. offline_mode=true → must be local (error if not downloaded)
        2. user_preference=local → must be local (error if not downloaded)
        3. model downloaded → prefer local
        4. else → use inference API
        """
        model = self.get(model_id)

        if model is None:
            return {
                "runtime": None,
                "model_id": model_id,
                "can_execute": False,
                "error": f"Model not installed: {model_id}",
                "requires_token": False
            }

        is_downloaded = model.download_status == DownloadStatus.DOWNLOADED.value

        if offline_mode:
            if is_downloaded:
                return {
                    "runtime": RuntimeMode.LOCAL.value,
                    "model_id": model_id,
                    "can_execute": True,
                    "error": None,
                    "requires_token": False
                }
            else:
                return {
                    "runtime": None,
                    "model_id": model_id,
                    "can_execute": False,
                    "error": "Offline mode requires downloaded model. Please download first.",
                    "requires_token": False
                }

        effective_pref = user_preference or RuntimeMode(model.preferred_runtime)
        if effective_pref == RuntimeMode.LOCAL:
            if is_downloaded:
                return {
                    "runtime": RuntimeMode.LOCAL.value,
                    "model_id": model_id,
                    "can_execute": True,
                    "error": None,
                    "requires_token": False
                }
            else:
                return {
                    "runtime": None,
                    "model_id": model_id,
                    "can_execute": False,
                    "error": "Local execution requires downloaded model. Please download first.",
                    "requires_token": False
                }

        if is_downloaded:
            return {
                "runtime": RuntimeMode.LOCAL.value,
                "model_id": model_id,
                "can_execute": True,
                "error": None,
                "requires_token": False
            }

        return {
            "runtime": RuntimeMode.INFERENCE_API.value,
            "model_id": model_id,
            "can_execute": True,
            "error": None,
            "requires_token": True
        }

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about installed models"""
        store = self._load()

        by_task: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        total_size = 0

        for model in store.models:
            by_task[model.task] = by_task.get(model.task, 0) + 1
            by_status[model.download_status] = by_status.get(model.download_status, 0) + 1
            if model.size_bytes:
                total_size += model.size_bytes

        return {
            "total_installed": len(store.models),
            "by_task": by_task,
            "by_status": by_status,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size > 0 else 0,
            "storage_path": str(self._storage_path)
        }


# =============================================================================
# Singleton Accessor
# =============================================================================

_provider_instance: Optional[InstalledModelProvider] = None


def get_installed_model_provider() -> InstalledModelProvider:
    """Get the singleton InstalledModelProvider instance"""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = InstalledModelProvider()
    return _provider_instance


def reset_provider() -> None:
    """Reset the provider instance (for testing)"""
    global _provider_instance
    _provider_instance = None
