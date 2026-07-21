"""
Data Provider Interfaces - Split by Domain

Each provider handles a specific domain of data operations.
"""

from gateway.providers.data.providers.workflow_provider import (
    WorkflowProvider,
    TemplateProvider,
    TemplateNotFoundError,
    TemplateOwnershipError,
    TemplateRevisionConflictError,
)
from gateway.providers.data.providers.chat_provider import ChatProvider
from gateway.providers.data.providers.user_provider import UserProfileProvider
from gateway.providers.data.providers.notification_provider import NotificationProvider
from gateway.providers.data.providers.dashboard_provider import DashboardProvider
from gateway.providers.data.providers.admin_provider import AdminProvider
from gateway.providers.data.providers.license_provider import LicenseProvider
from gateway.providers.data.providers.storage_provider import StorageProvider
from gateway.providers.data.providers.data_provider import DataProvider
from gateway.providers.data.providers.review_provider import ReviewProvider
from gateway.providers.data.providers.subscription_provider import SubscriptionProvider
from gateway.providers.data.providers.earnings_provider import EarningsProvider
from gateway.providers.data.providers.payment_provider import PaymentProvider
from gateway.providers.data.providers.per_call_settlement_provider import PerCallSettlementProvider
from gateway.providers.data.providers.ai_usage_provider import AIUsageProvider
from gateway.providers.data.providers.telemetry_provider import TelemetryProvider, TelemetryRecord
from gateway.providers.data.providers.audit_provider import AuditLogProvider
from gateway.providers.data.providers.deletion_provider import DeletionRequestProvider
from gateway.providers.data.providers.user_deletion_provider import UserDeletionProvider
from gateway.providers.data.providers.user_tool_provider import UserToolProvider
from gateway.providers.data.providers.order_provider import OrderProvider
from gateway.providers.data.providers.invite_key_provider import InviteKeyProvider
from gateway.providers.data.providers.module_access_provider import ModuleAccessProvider
from gateway.providers.data.providers.report_provider import ReportProvider
from gateway.providers.data.providers.api_key_provider import ApiKeyProvider
from gateway.providers.data.providers.issue_provider import IssueProvider
from gateway.providers.data.providers.pull_request_provider import PullRequestProvider
from gateway.providers.data.providers.template_issue_provider import TemplateIssueProvider
from gateway.providers.data.providers.webhook_provider import WebhookProvider
from gateway.providers.data.providers.schedule_provider import ScheduleProvider
from gateway.providers.data.providers.wallet_provider import WalletProvider
from gateway.providers.data.providers.ai_insights_provider import AIInsightsProvider
from gateway.providers.data.providers.trial_provider import TrialProvider
from gateway.providers.data.providers.feature_usage_provider import FeatureUsageProvider
from gateway.providers.data.providers.plan_config_provider import PlanConfigProvider
from gateway.providers.data.providers.device_provider import DeviceProvider
from gateway.providers.data.providers.desktop_oauth_provider import DesktopOAuthProvider
from gateway.providers.data.providers.vscode_auth_code_provider import VscodeAuthCodeProvider
from gateway.providers.data.providers.collaboration_quota_provider import CollaborationQuotaProvider
from gateway.providers.data.providers.collaboration_request_provider import CollaborationRequestProvider
from gateway.providers.data.providers.collaboration_provider import (
    CollaborationInviteCodeExhaustedError,
    CollaborationPermissionError,
    CollaborationProvider,
    CollaborationTemplateNotFoundError,
)
from gateway.providers.data.providers.creator_program_provider import CreatorProgramProvider
from gateway.providers.data.providers.line_provider import LineProvider
from gateway.providers.data.providers.breakpoint_provider import (
    BreakpointProvider,
    BreakpointRecord,
    BreakpointResponseRecord,
    DuplicateBreakpointResponseError,
)

__all__ = [
    # Core
    "WorkflowProvider",
    "TemplateProvider",
    "TemplateNotFoundError",
    "TemplateOwnershipError",
    "TemplateRevisionConflictError",
    "DataProvider",
    # User
    "ChatProvider",
    "UserProfileProvider",
    # System
    "NotificationProvider",
    "DashboardProvider",
    "AdminProvider",
    "LicenseProvider",
    "StorageProvider",
    # Commerce
    "ReviewProvider",
    "SubscriptionProvider",
    "EarningsProvider",
    "PaymentProvider",
    "PerCallSettlementProvider",
    # Tracking
    "AIUsageProvider",
    "TelemetryProvider",
    "TelemetryRecord",
    "AuditLogProvider",
    # Access
    "DeletionRequestProvider",
    "UserDeletionProvider",
    "UserToolProvider",
    "OrderProvider",
    "InviteKeyProvider",
    "ModuleAccessProvider",
    "ReportProvider",
    "ApiKeyProvider",
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
]
