"""
Capability System Types

Dual-Axis Model:
- Axis A: LicenseType (Business Rights) - What you paid for
- Axis B: DeploymentMode (Technical Constraints) - What's technically possible

Feature Enabled = License Gate ∩ Deployment Gate
"""

from enum import Enum


# =============================================================================
# Axis A: License Type (Business Rights)
# =============================================================================

class LicenseType(str, Enum):
    """
    License types determine what features you have the RIGHT to use.

    This is a business decision, not a technical one.

    NOTE: Values must match frontend constants/subscription.js SUBSCRIPTION_PLANS
    """
    FREE = "free"
    """
    Free tier - basic features only.
    - Target: Trial users, learners
    - Payment: None
    - Features: Core workflow builder + execution
    """

    PRO = "pro"
    """
    Pro tier - full features + cloud services.
    - Target: Individuals
    - Payment: Monthly/Yearly subscription
    - Features: All local features + cloud sync + marketplace
    """

    TEAM = "team"
    """
    Team tier - same as Pro, for teams.
    - Target: Small teams
    - Payment: Monthly/Yearly subscription (per seat)
    - Features: Same as Pro + team collaboration
    """

    OFFLINE = "offline"
    """
    Offline license - full local features, no cloud dependency.
    - Target: Professionals, small businesses
    - Payment: One-time purchase
    - Features: All local features (no cloud)
    """

    ENTERPRISE = "enterprise"
    """
    Enterprise license - full features + governance + self-host.
    - Target: Enterprise customers
    - Payment: Annual contract
    - Features: Everything + RBAC/SSO/Org
    """


# =============================================================================
# Axis B: Deployment Mode (Technical Constraints)
# =============================================================================

class CapabilityDeployMode(str, Enum):
    """
    Deployment modes determine what features are TECHNICALLY POSSIBLE.

    This is a technical constraint, not a business one.
    """
    SAAS_CLOUD = "saas_cloud"
    """
    Cloud SaaS deployment.
    - Location: Hosted in cloud
    - Network: Required (internet)
    - Database: Firebase
    - Auth: Firebase Auth
    - Constraints: No local storage, no self-host features
    """

    LOCAL_ONLINE = "local_online"
    """
    Local installation with internet connection.
    - Location: User's machine
    - Network: Required (internet)
    - Database: SQLite (local)
    - Auth: Firebase Auth (remote)
    - Constraints: Can use cloud services
    """

    ENTERPRISE_INTRANET = "enterprise_intranet"
    """
    Enterprise on-premise deployment.
    - Location: Enterprise data center
    - Network: Intranet only (no internet)
    - Database: PostgreSQL
    - Auth: LDAP/SAML/OIDC
    - Constraints: No cloud services, can self-host everything
    """

    LOCAL_OFFLINE = "local_offline"
    """
    Local installation without internet.
    - Location: User's machine
    - Network: None
    - Database: SQLite (local)
    - Auth: Local JWT
    - Constraints: No cloud, no self-host services
    """


# =============================================================================
# Feature Categories
# =============================================================================

class FeatureCategory(str, Enum):
    """
    Feature categories for organization and documentation.
    """
    LOCAL_ONLY = "local_only"
    """
    Category A: Can run purely on local machine, no network needed.
    Examples: workflow run, local metrics, local audit
    """

    SELF_HOSTABLE = "self_hostable"
    """
    Category B: Needs network but can be self-hosted (no cloud dependency).
    Examples: orchestrator, multi-runner, RBAC, SSO
    """

    CLOUD_ONLY = "cloud_only"
    """
    Category C: Requires cloud infrastructure, cannot be self-hosted.
    Examples: marketplace, cloud sync, hosted observability
    """


# =============================================================================
# Features
# =============================================================================

class Feature(str, Enum):
    """
    All system features.

    Naming convention: category.feature_name
    """

    # =========================================================================
    # Category A: Local-Only Features
    # =========================================================================

    # Core (available to all)
    CORE_WORKFLOW_RUN = "core.workflow_run"
    CORE_TEMPLATE_BUILDER = "core.template_builder"
    CORE_EXECUTION_HISTORY = "core.execution_history"  # Note: LIMITED for free (recent N)
    CORE_BASIC_LOGGING = "core.basic_logging"

    # Full execution history (paid - prerequisite for replay/rerun/debug)
    EXECUTION_RECORD_FULL = "core.execution_record_full"  # Full snapshots & artifacts

    # Phase 8: Local Observability (paid)
    LOCAL_METRICS = "local.metrics"
    LOCAL_TRACING = "local.tracing"
    LOCAL_ALERTS = "local.alerts"
    EXPORT_PROMETHEUS = "local.export_prometheus"

    # Phase 9: Local Versioning (paid)
    LOCAL_VERSIONING = "local.versioning"
    LOCAL_VERSION_ROLLBACK = "local.version_rollback"

    # Phase 9: Local Audit (paid)
    LOCAL_AUDIT = "local.audit"
    LOCAL_AUDIT_CHAIN = "local.audit_chain"  # Hash chain integrity
    LOCAL_AUDIT_VERIFY = "local.audit_verify"

    # Execution Features (paid)
    EXECUTION_REPLAY = "execution.replay"
    EXECUTION_RERUN = "execution.rerun"
    EXECUTION_DEBUG = "execution.debug"
    EVIDENCE_VIEW = "execution.evidence"
    LINEAGE_VIEW = "execution.lineage"

    # =========================================================================
    # Category B: Self-Hostable Features (Paid + Enterprise)
    # =========================================================================

    # Orchestration - Basic (available to subscription/offline_license)
    ORCH_BASIC_SCHEDULER = "selfhost.orch_basic_scheduler"  # Single-machine scheduling
    ORCH_BASIC_QUEUE = "selfhost.orch_basic_queue"  # Local job queue

    # Orchestration - Enterprise (enterprise only)
    ORCHESTRATOR = "selfhost.orchestrator"  # Full enterprise orchestrator
    MULTI_RUNNER = "selfhost.multi_runner"  # Distributed runners
    CENTRAL_LOGGING = "selfhost.central_logging"
    CENTRAL_METRICS = "selfhost.central_metrics"
    RUNNER_ISOLATION = "selfhost.runner_isolation"  # Resource isolation
    RUNNER_QUOTAS = "selfhost.runner_quotas"  # Resource quotas

    # Organization & Access Control
    ORG_STRUCTURE = "selfhost.org_structure"
    ORG_DEPARTMENTS = "selfhost.org_departments"
    ORG_TEAMS = "selfhost.org_teams"
    RBAC_FULL = "selfhost.rbac_full"

    # SSO
    SSO_LDAP = "selfhost.sso_ldap"
    SSO_SAML = "selfhost.sso_saml"
    SSO_OIDC = "selfhost.sso_oidc"

    # Enterprise Workflow
    APPROVAL_WORKFLOW = "selfhost.approval_workflow"
    SECRETS_VAULT = "selfhost.secrets_vault"

    # =========================================================================
    # Category C: Cloud-Only Features
    # =========================================================================

    MARKETPLACE_BROWSE = "cloud.marketplace_browse"
    MARKETPLACE_PURCHASE = "cloud.marketplace_purchase"
    MARKETPLACE_PUBLISH = "cloud.marketplace_publish"
    CLOUD_SYNC = "cloud.sync"
    HOSTED_OBSERVABILITY = "cloud.hosted_observability"
    BILLING_STRIPE = "cloud.billing_stripe"

    # =========================================================================
    # Category D: Pro Modules (Paid Features)
    # =========================================================================

    # Stealth Browser Automation
    PRO_MODULES_STEALTH = "pro.modules.stealth"

    # Captcha Solving
    PRO_MODULES_CAPTCHA = "pro.modules.captcha"

    # Enterprise Connectors (SAP, Salesforce, SSO, LDAP)
    PRO_MODULES_ENTERPRISE = "pro.modules.enterprise"

    # Parallel Execution (Batch, Pool, Rate Limit, MapReduce)
    PRO_MODULES_PARALLEL = "pro.modules.parallel"

    # Checkpoint/Resume
    PRO_MODULES_CHECKPOINT = "pro.modules.checkpoint"

    # Advanced Document Processing (OCR, PDF, Tables, Forms)
    PRO_MODULES_DOCUMENT = "pro.modules.document"

    # Computer Vision (Object Detection, Face Detection, Element Finding)
    PRO_MODULES_VISION = "pro.modules.vision"

    # All Pro Modules Bundle
    PRO_MODULES_ALL = "pro.modules.all"

    # =========================================================================
    # Category E: Desktop-Only Features
    # =========================================================================

    # Workflow Recording (browser action capture → workflow compilation)
    WORKFLOW_RECORDING = "desktop.workflow_recording"


# =============================================================================
# Feature Metadata
# =============================================================================

FEATURE_METADATA = {
    # Core features
    Feature.CORE_WORKFLOW_RUN: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Workflow Execution",
        "description": "Execute workflows locally",
    },
    Feature.CORE_TEMPLATE_BUILDER: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Template Builder",
        "description": "Visual workflow editor",
    },
    Feature.CORE_EXECUTION_HISTORY: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Execution History",
        "description": "View past executions (FREE: limited to recent 30 days/100 records)",
    },
    Feature.CORE_BASIC_LOGGING: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Basic Logging",
        "description": "Basic execution logs",
    },
    Feature.EXECUTION_RECORD_FULL: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Full Execution Record",
        "description": "Complete execution snapshots with input/output/artifacts. Prerequisite for replay/rerun/debug.",
        "prerequisites": [],  # Base feature
    },

    # Local Observability
    Feature.LOCAL_METRICS: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Local Metrics",
        "description": "Collect metrics to local storage",
    },
    Feature.LOCAL_TRACING: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Local Tracing",
        "description": "Distributed tracing to local storage",
    },
    Feature.LOCAL_ALERTS: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Local Alerts",
        "description": "Alert rules with local notifications",
    },
    Feature.EXPORT_PROMETHEUS: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Prometheus Export",
        "description": "Export metrics in Prometheus format",
    },

    # Local Versioning
    Feature.LOCAL_VERSIONING: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Workflow Versioning",
        "description": "Version control for workflows",
    },
    Feature.LOCAL_VERSION_ROLLBACK: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Version Rollback",
        "description": "Rollback to previous versions",
    },

    # Local Audit
    Feature.LOCAL_AUDIT: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Audit Logging",
        "description": "Comprehensive audit trail",
    },
    Feature.LOCAL_AUDIT_CHAIN: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Audit Chain",
        "description": "Hash chain for audit integrity",
    },
    Feature.LOCAL_AUDIT_VERIFY: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Audit Verification",
        "description": "Verify audit log integrity",
    },

    # Execution Features (require EXECUTION_RECORD_FULL as prerequisite)
    Feature.EXECUTION_REPLAY: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Execution Replay",
        "description": "Replay past executions step by step",
        "prerequisites": ["core.execution_record_full"],
    },
    Feature.EXECUTION_RERUN: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Execution Rerun",
        "description": "Rerun from specific node with same inputs",
        "prerequisites": ["core.execution_record_full"],
    },
    Feature.EXECUTION_DEBUG: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Execution Debug",
        "description": "Debug executions with breakpoints and variable inspection",
        "prerequisites": ["core.execution_record_full"],
    },
    Feature.EVIDENCE_VIEW: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Execution Evidence",
        "description": "View execution evidence including screenshots and DOM snapshots",
        "prerequisites": ["core.execution_record_full"],
    },
    Feature.LINEAGE_VIEW: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Execution Lineage",
        "description": "View data flow lineage graphs for executions",
        "prerequisites": ["core.execution_record_full"],
    },

    # Self-hostable features - Basic Orchestration (subscription/offline_license)
    Feature.ORCH_BASIC_SCHEDULER: {
        "category": FeatureCategory.SELF_HOSTABLE,
        "name": "Basic Scheduler",
        "description": "Single-machine job scheduling (cron-like)",
    },
    Feature.ORCH_BASIC_QUEUE: {
        "category": FeatureCategory.SELF_HOSTABLE,
        "name": "Basic Queue",
        "description": "Local job queue for sequential execution",
    },

    # Self-hostable features - Enterprise Orchestration
    Feature.ORCHESTRATOR: {
        "category": FeatureCategory.SELF_HOSTABLE,
        "name": "Orchestrator",
        "description": "Full enterprise orchestrator with distributed scheduling",
    },
    Feature.MULTI_RUNNER: {
        "category": FeatureCategory.SELF_HOSTABLE,
        "name": "Multi-Runner",
        "description": "Distributed execution workers across machines",
    },
    Feature.RUNNER_ISOLATION: {
        "category": FeatureCategory.SELF_HOSTABLE,
        "name": "Runner Isolation",
        "description": "Container/VM isolation for runner execution",
    },
    Feature.RUNNER_QUOTAS: {
        "category": FeatureCategory.SELF_HOSTABLE,
        "name": "Runner Quotas",
        "description": "Resource quotas per team/user/workflow",
    },
    Feature.ORG_STRUCTURE: {
        "category": FeatureCategory.SELF_HOSTABLE,
        "name": "Organization Structure",
        "description": "Organization hierarchy management",
    },
    Feature.RBAC_FULL: {
        "category": FeatureCategory.SELF_HOSTABLE,
        "name": "Full RBAC",
        "description": "Complete role-based access control",
    },
    Feature.SSO_LDAP: {
        "category": FeatureCategory.SELF_HOSTABLE,
        "name": "LDAP SSO",
        "description": "LDAP authentication integration",
    },
    Feature.SSO_SAML: {
        "category": FeatureCategory.SELF_HOSTABLE,
        "name": "SAML SSO",
        "description": "SAML authentication integration",
    },
    Feature.SSO_OIDC: {
        "category": FeatureCategory.SELF_HOSTABLE,
        "name": "OIDC SSO",
        "description": "OpenID Connect authentication",
    },

    # Cloud features
    Feature.MARKETPLACE_BROWSE: {
        "category": FeatureCategory.CLOUD_ONLY,
        "name": "Marketplace Browse",
        "description": "Browse template marketplace",
    },
    Feature.MARKETPLACE_PURCHASE: {
        "category": FeatureCategory.CLOUD_ONLY,
        "name": "Marketplace Purchase",
        "description": "Purchase templates",
    },
    Feature.CLOUD_SYNC: {
        "category": FeatureCategory.CLOUD_ONLY,
        "name": "Cloud Sync",
        "description": "Sync data to cloud",
    },
    Feature.HOSTED_OBSERVABILITY: {
        "category": FeatureCategory.CLOUD_ONLY,
        "name": "Hosted Observability",
        "description": "Cloud-hosted metrics and tracing UI",
    },

    # Pro Modules
    Feature.PRO_MODULES_STEALTH: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Stealth Browser",
        "description": "Anti-detection browser automation with fingerprint spoofing",
    },
    Feature.PRO_MODULES_CAPTCHA: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Captcha Solving",
        "description": "Automated CAPTCHA solving via 2Captcha, Anti-Captcha, etc.",
    },
    Feature.PRO_MODULES_ENTERPRISE: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Enterprise Connectors",
        "description": "Salesforce, SAP, SSO, LDAP integrations",
    },
    Feature.PRO_MODULES_PARALLEL: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Parallel Execution",
        "description": "Batch processing, worker pools, rate limiting, map-reduce",
    },
    Feature.PRO_MODULES_CHECKPOINT: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Checkpoint/Resume",
        "description": "Save and restore workflow execution state",
    },
    Feature.PRO_MODULES_DOCUMENT: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Document Processing",
        "description": "OCR, PDF extraction, table/form parsing",
    },
    Feature.PRO_MODULES_VISION: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Computer Vision",
        "description": "Object detection, image classification, face detection, UI element finding",
    },
    Feature.PRO_MODULES_ALL: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "All Pro Modules",
        "description": "Bundle of all Pro automation modules",
    },

    # Desktop-only features
    Feature.WORKFLOW_RECORDING: {
        "category": FeatureCategory.LOCAL_ONLY,
        "name": "Workflow Recording",
        "description": "Record browser actions and compile into reusable workflows",
    },
}
