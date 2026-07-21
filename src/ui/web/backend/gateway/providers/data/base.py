"""
Data Provider Base Classes

Abstract interfaces for workflow and template data operations.
Each deployment mode implements these interfaces differently.

NOTE: This file re-exports from the providers/ directory for backward compatibility.
All provider classes have been split into separate files under providers/.
"""

# Re-export all providers from the new modular structure
from gateway.providers.data.providers import (
    # Core workflow/template providers
    WorkflowProvider,
    TemplateProvider,
    TemplateNotFoundError,
    TemplateOwnershipError,
    TemplateRevisionConflictError,
    # Communication providers
    ChatProvider,
    # User management providers
    UserProfileProvider,
    NotificationProvider,
    # Dashboard/Admin providers
    DashboardProvider,
    AdminProvider,
    # Business providers
    LicenseProvider,
    StorageProvider,
    ReviewProvider,
    SubscriptionProvider,
    EarningsProvider,
    PaymentProvider,
    PerCallSettlementProvider,
    # Usage tracking providers
    AIUsageProvider,
    TelemetryProvider,
    TelemetryRecord,
    AuditLogProvider,
    UserDeletionProvider,
    # Access control providers
    DeletionRequestProvider,
    InviteKeyProvider,
    ModuleAccessProvider,
    # Custom tools provider
    UserToolProvider,
    # Order/Report providers
    OrderProvider,
    ReportProvider,
    # API Keys
    ApiKeyProvider,
    # Issues
    IssueProvider,
    # Template Collaboration
    PullRequestProvider,
    TemplateIssueProvider,
    # Wallet
    WalletProvider,
    AIInsightsProvider,
    TrialProvider,
    FeatureUsageProvider,
    PlanConfigProvider,
    DeviceProvider,
    DesktopOAuthProvider,
    VscodeAuthCodeProvider,
    CollaborationQuotaProvider,
    CollaborationRequestProvider,
    CollaborationProvider,
    CollaborationTemplateNotFoundError,
    CollaborationPermissionError,
    CollaborationInviteCodeExhaustedError,
    CreatorProgramProvider,
    LineProvider,
    BreakpointProvider,
    BreakpointRecord,
    BreakpointResponseRecord,
    DuplicateBreakpointResponseError,
    # Triggers
    WebhookProvider,
    ScheduleProvider,
    # Combined interface
    DataProvider,
)

__all__ = [
    # Core
    "WorkflowProvider",
    "TemplateProvider",
    "TemplateNotFoundError",
    "TemplateOwnershipError",
    "TemplateRevisionConflictError",
    # Communication
    "ChatProvider",
    # User management
    "UserProfileProvider",
    "NotificationProvider",
    # Dashboard/Admin
    "DashboardProvider",
    "AdminProvider",
    # Business
    "LicenseProvider",
    "StorageProvider",
    "ReviewProvider",
    "SubscriptionProvider",
    "EarningsProvider",
    "PaymentProvider",
    "PerCallSettlementProvider",
    # Usage tracking
    "AIUsageProvider",
    "TelemetryProvider",
    "TelemetryRecord",
    "AuditLogProvider",
    "UserDeletionProvider",
    # Access control
    "DeletionRequestProvider",
    "InviteKeyProvider",
    "ModuleAccessProvider",
    # Custom tools
    "UserToolProvider",
    # Order/Report
    "OrderProvider",
    "ReportProvider",
    # API Keys
    "ApiKeyProvider",
    # Issues
    "IssueProvider",
    # Template Collaboration
    "PullRequestProvider",
    "TemplateIssueProvider",
    # Wallet
    "WalletProvider",
    "AIInsightsProvider",
    "TrialProvider",
    "FeatureUsageProvider",
    "PlanConfigProvider",
    "DeviceProvider",
    "DesktopOAuthProvider",
    "VscodeAuthCodeProvider",
    "CollaborationQuotaProvider",
    "CollaborationRequestProvider",
    "CollaborationProvider",
    "CollaborationTemplateNotFoundError",
    "CollaborationPermissionError",
    "CollaborationInviteCodeExhaustedError",
    "CreatorProgramProvider",
    "LineProvider",
    "BreakpointProvider",
    "BreakpointRecord",
    "BreakpointResponseRecord",
    "DuplicateBreakpointResponseError",
    # Triggers
    "WebhookProvider",
    "ScheduleProvider",
    # Combined interface
    "DataProvider",
]
