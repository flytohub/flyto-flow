"""Template DTO Models"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from gateway.providers.data.models.common import DataSource


class TemplateDTO(BaseModel):
    """
    Unified Template DTO

    Templates are workflow presets that can be shared or published.
    """
    # Identity
    id: str

    # Basic info
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"

    # Author (supports both author_id and creator_id formats)
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    creator_id: Optional[str] = None  # Firestore original field
    creator_name: Optional[str] = None  # Firestore original field

    # Organization
    folder_id: Optional[str] = None  # Template folder ID

    # Category and tags
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # Source
    source: DataSource = DataSource.USER

    # Visibility and Status
    visibility: Optional[str] = "private"  # private, public
    status: Optional[str] = "draft"  # draft, published (template_status)
    is_public: bool = False
    is_verified: bool = False
    is_featured: bool = False

    # Pricing
    pricing: Optional[str] = "free"  # 'free', 'paid', or 'per_call'
    price: Optional[int] = 0  # Price in cents (one-time purchase)
    call_price: Optional[int] = None  # Credits per execution (for per_call pricing)

    # Versioning
    version_number: int = 1  # Incremental version number
    latest_version_id: Optional[str] = None  # Reference to latest version in template_versions

    # Fork relationship
    parent_template_id: Optional[str] = None  # Source template if this is a fork
    parent_version_id: Optional[str] = None   # Version forked from
    is_fork: bool = False
    fork_count: int = 0  # Number of times this template was forked

    # Marketplace status (separate from purchaser access)
    marketplace_status: str = "visible"  # visible, hidden, deleted

    # Workflow protection (mutability)
    mutability: str = "fork_on_use"  # locked, fork_on_use, editable
    is_workflow_visible: bool = True  # False when locked and not owner
    is_collaborator: bool = False  # True when requesting user is in collaboration_members

    # Marketplace snapshot (frozen version shown in marketplace)
    # When published, this captures the template state for marketplace display
    # Edits to live template don't affect this until explicitly updated
    marketplace_snapshot: Optional[Dict[str, Any]] = None  # {steps, ui, name, description, published_at, version_id}
    has_pending_changes: bool = False  # True if live template differs from marketplace_snapshot

    # Statistics
    execution_count: int = 0
    install_count: int = 0
    downloads: int = 0  # Field name used by frontend
    download_count: int = 0  # Firestore original field name
    rating: Optional[float] = None
    rating_sum: int = 0
    rating_count: int = 0

    # Media
    icon_url: Optional[str] = None  # Template image
    color: Optional[str] = None  # Hex color like #8B5CF6
    # Rich content
    video_url: Optional[str] = None
    usage_instructions: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)

    # Permissions required to run
    required_permissions: List[str] = Field(default_factory=list)

    # Required secrets (Template v2)
    required_secrets: List[str] = Field(default_factory=list)  # e.g. ["OPENAI_API_KEY"]

    # Plugin dependencies (Template v2)
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    # Format: [{"plugin": "flyto-official/llm", "version": ">=1.0.0"}]

    # Template schema version (Template v2)
    template_version: str = "1.0.0"

    # Timestamps
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    # Optimistic locking (RACE-1)
    revision: Optional[str] = None  # UUID for optimistic concurrency control

    # Error handling
    error_workflow_id: Optional[str] = None
    error_handling: Optional[Dict[str, Any]] = None

    # Workflow data (the actual template content)
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    ui: Optional[Dict[str, Any]] = None
    workflow_data: Optional[Dict[str, Any]] = None  # Legacy
    # Checkpoints (human-in-the-loop pause points)
    checkpoints: Optional[List[str]] = None

    # Capabilities
    capabilities: Dict[str, bool] = Field(default_factory=lambda: {
        "execute": True,
        "edit": True,
        "delete": True,
        "share": False,
        "publish": False,
        "install": False,
    })

    # Context fields (populated when retrieved from library)
    purchase_context: Optional[Dict[str, Any]] = None  # {purchase_id, purchased_at, has_update, etc.}
    fork_context: Optional[Dict[str, Any]] = None  # {fork_id, source_template_id, forked_at}

    # Template as Node support
    input_schema: Optional[Dict[str, Any]] = None  # JSON Schema for input parameters
    output_schema: Optional[Dict[str, Any]] = None  # JSON Schema for output structure
    # Pre-computed params_schema (computed from UI at save time, used by template.invoke)
    params_schema: Optional[Dict[str, Any]] = None

    # i18n support
    default_language: str = "en"  # Default language code
    translations: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    # Format: {"zh-TW": {"name": "...", "description": "..."}, "ja": {...}}

    # Regional visibility
    visibility_regions: List[str] = Field(default_factory=list)  # Empty = global
    blocked_regions: List[str] = Field(default_factory=list)

    # Search optimization
    search_tokens: Dict[str, List[str]] = Field(default_factory=dict)
    # Format: {"en": ["email", "automation"], "zh-TW": ["電子", "郵件"]}

    # Collaboration
    contributors: List[Dict[str, Any]] = Field(default_factory=list)
    # [{ user_id, user_name, avatar, merged_count, first_contributed_at }]
    contributor_count: int = 0
    open_pr_count: int = 0
    open_issue_count: int = 0

    # Merge protection settings
    merge_settings: Dict[str, Any] = Field(default_factory=lambda: {
        "require_approval": False,
        "min_reviewers": 0,
    })

    model_config = ConfigDict(use_enum_values=True)


class TemplateCreateDTO(BaseModel):
    """DTO for creating a template"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    # Visibility and pricing
    visibility: Optional[str] = "private"  # private, public
    pricing: Optional[str] = "free"  # free, paid, per_call
    price: Optional[int] = 0  # Price in cents (one-time purchase)
    call_price: Optional[int] = None  # Credits per execution (for per_call pricing)
    # Workflow data
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    ui: Optional[Dict[str, Any]] = None
    workflow_data: Optional[Dict[str, Any]] = None  # Legacy field
    # Media
    icon_url: Optional[str] = None
    required_permissions: List[str] = Field(default_factory=list)
    # Template v2 fields
    required_secrets: List[str] = Field(default_factory=list)
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    template_version: str = "1.0.0"
    # i18n
    default_language: str = "en"
    translations: Optional[Dict[str, Dict[str, str]]] = None
    visibility_regions: Optional[List[str]] = None
    blocked_regions: Optional[List[str]] = None
    # Template as Node support
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    # Pre-computed params_schema (computed from UI at save time)
    params_schema: Optional[Dict[str, Any]] = None
    # Error handling
    error_workflow_id: Optional[str] = None
    error_handling: Optional[Dict[str, Any]] = None
    # Checkpoints (human-in-the-loop pause points)
    checkpoints: Optional[List[str]] = None
    # Organization
    folder_id: Optional[str] = None


class TemplateUpdateDTO(BaseModel):
    """DTO for updating a template"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    # Visibility and pricing
    visibility: Optional[str] = None  # private, public
    pricing: Optional[str] = None  # free, paid, per_call
    price: Optional[int] = None
    call_price: Optional[int] = None  # Credits per execution (for per_call pricing)
    # Status
    status: Optional[str] = None  # draft, published
    is_public: Optional[bool] = None  # Legacy
    # Marketplace listing
    listed: Optional[bool] = None
    # Enabled/disabled toggle
    enabled: Optional[bool] = None
    # Workflow protection
    mutability: Optional[str] = None  # locked, fork_on_use, editable
    # Workflow data
    steps: Optional[List[Dict[str, Any]]] = None
    ui: Optional[Dict[str, Any]] = None
    workflow_data: Optional[Dict[str, Any]] = None  # Legacy
    # Media
    icon_url: Optional[str] = None
    color: Optional[str] = None  # Hex color like #8B5CF6
    # Template v2 fields
    required_permissions: Optional[List[str]] = None
    required_secrets: Optional[List[str]] = None
    dependencies: Optional[List[Dict[str, Any]]] = None
    template_version: Optional[str] = None
    # Optimistic locking (RACE-1)
    expected_revision: Optional[str] = None  # If set, update fails if revision mismatch
    # Version change summary (for creating new version on update)
    change_summary: Optional[str] = None
    # i18n
    default_language: Optional[str] = None
    translations: Optional[Dict[str, Dict[str, str]]] = None
    visibility_regions: Optional[List[str]] = None
    blocked_regions: Optional[List[str]] = None
    # Template as Node support
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    # Pre-computed params_schema (computed from UI at save time)
    params_schema: Optional[Dict[str, Any]] = None
    # Rich content
    video_url: Optional[str] = None
    usage_instructions: Optional[str] = None
    screenshots: Optional[List[str]] = None
    # Error handling
    error_workflow_id: Optional[str] = None
    error_handling: Optional[Dict[str, Any]] = None
    # Checkpoints (human-in-the-loop pause points)
    checkpoints: Optional[List[str]] = None
    # Organization
    folder_id: Optional[str] = None


class TemplateVersionDTO(BaseModel):
    """Template version snapshot for version history"""
    id: str
    template_id: str
    version_number: int
    version_tag: Optional[str] = None  # Semantic version like "v2.0.0"
    content_hash: str  # SHA-256 of definition
    definition: Dict[str, Any]  # Full template snapshot
    change_summary: Optional[str] = None
    created_by: str
    created_at: datetime
    is_published: bool = False


class PurchaseSnapshotDTO(BaseModel):
    """Complete purchase record with template snapshot"""
    id: str
    template_id: str  # Original template reference
    original_creator_id: str
    purchased_at: datetime
    purchase_price: int  # Price paid in cents

    # Version tracking
    purchased_version_id: str  # Version at purchase time
    current_version_id: str  # May differ if synced

    # Complete template snapshot (owned by purchaser)
    snapshot: Dict[str, Any]

    # Status
    sync_policy: str = "manual"  # Always manual per user choice
    has_pending_update: bool = False
    source_deleted: bool = False
    source_unpublished: bool = False

    # Auto-update settings for Template as Node
    auto_update: str = "off"  # off | patch | minor | all


class LibrarySettingsUpdateDTO(BaseModel):
    """DTO for updating library item settings"""
    auto_update: Optional[str] = None  # off | patch | minor | all


class ForkTemplateDTO(BaseModel):
    """User's forked template (personal copy)"""
    id: str
    source_type: str  # "purchased" or "public"
    source_template_id: str
    source_version_id: str
    source_purchase_id: Optional[str] = None  # If forked from purchase
    forked_at: datetime

    # Complete template content (fully editable by fork owner)
    template: Dict[str, Any]

    # Sync status with source
    is_synced_with_source: bool = False
    last_sync_at: Optional[datetime] = None
