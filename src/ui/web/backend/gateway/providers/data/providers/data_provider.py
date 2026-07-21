"""
Combined Data Provider Interface
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from gateway.providers.data.providers.workflow_provider import WorkflowProvider, TemplateProvider
from gateway.providers.data.providers.chat_provider import ChatProvider
from gateway.providers.data.providers.user_provider import UserProfileProvider
from gateway.providers.data.providers.notification_provider import NotificationProvider
from gateway.providers.data.providers.dashboard_provider import DashboardProvider
from gateway.providers.data.providers.admin_provider import AdminProvider
from gateway.providers.data.providers.license_provider import LicenseProvider
from gateway.providers.data.providers.storage_provider import StorageProvider
from gateway.providers.data.providers.review_provider import ReviewProvider
from gateway.providers.data.providers.subscription_provider import SubscriptionProvider
from gateway.providers.data.providers.earnings_provider import EarningsProvider
from gateway.providers.data.providers.payment_provider import PaymentProvider
from gateway.providers.data.providers.ai_usage_provider import AIUsageProvider
from gateway.providers.data.providers.telemetry_provider import TelemetryProvider
from gateway.providers.data.providers.per_call_settlement_provider import PerCallSettlementProvider
from gateway.providers.data.providers.audit_provider import AuditLogProvider
from gateway.providers.data.providers.deletion_provider import DeletionRequestProvider
from gateway.providers.data.providers.user_deletion_provider import UserDeletionProvider
from gateway.providers.data.providers.user_tool_provider import UserToolProvider
from gateway.providers.data.providers.order_provider import OrderProvider
from gateway.providers.data.providers.invite_key_provider import InviteKeyProvider
from gateway.providers.data.providers.module_access_provider import ModuleAccessProvider
from gateway.providers.data.providers.report_provider import ReportProvider
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
from gateway.providers.data.providers.collaboration_quota_provider import (
    CollaborationQuotaProvider,
)
from gateway.providers.data.providers.collaboration_request_provider import (
    CollaborationRequestProvider,
)
from gateway.providers.data.providers.collaboration_provider import CollaborationProvider
from gateway.providers.data.providers.creator_program_provider import CreatorProgramProvider
from gateway.providers.data.providers.line_provider import LineProvider
from gateway.providers.data.providers.breakpoint_provider import BreakpointProvider


class DataProvider(ABC):
    """
    Combined data provider.

    Provides access to all data providers.
    """

    @property
    @abstractmethod
    def workflows(self) -> WorkflowProvider:
        """Get workflow provider"""
        pass

    @property
    @abstractmethod
    def templates(self) -> TemplateProvider:
        """Get template provider"""
        pass

    @property
    @abstractmethod
    def chat(self) -> ChatProvider:
        """Get chat provider"""
        pass

    @property
    @abstractmethod
    def users(self) -> UserProfileProvider:
        """Get user profile provider"""
        pass

    @property
    @abstractmethod
    def notifications(self) -> NotificationProvider:
        """Get notification provider"""
        pass

    @property
    @abstractmethod
    def storage(self) -> StorageProvider:
        """Get storage provider"""
        pass

    @property
    @abstractmethod
    def dashboard(self) -> DashboardProvider:
        """Get dashboard provider"""
        pass

    @property
    @abstractmethod
    def admin(self) -> AdminProvider:
        """Get admin provider"""
        pass

    @property
    @abstractmethod
    def licenses(self) -> LicenseProvider:
        """Get license provider"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources"""
        pass

    @property
    @abstractmethod
    def reviews(self) -> ReviewProvider:
        """Get review provider"""
        pass

    @property
    @abstractmethod
    def subscriptions(self) -> SubscriptionProvider:
        """Get subscription provider"""
        pass

    @property
    @abstractmethod
    def earnings(self) -> EarningsProvider:
        """Get earnings provider"""
        pass

    @property
    @abstractmethod
    def payments(self) -> PaymentProvider:
        """Get payment provider"""
        pass

    @property
    @abstractmethod
    def per_call_settlement(self) -> PerCallSettlementProvider:
        """Get per-call settlement provider"""
        pass

    @property
    @abstractmethod
    def ai_usage(self) -> AIUsageProvider:
        """Get AI usage provider"""
        pass

    @property
    @abstractmethod
    def telemetry(self) -> TelemetryProvider:
        """Get telemetry provider"""
        pass

    @property
    @abstractmethod
    def ai_insights(self) -> AIInsightsProvider:
        """Get AI insights provider"""
        pass

    @property
    @abstractmethod
    def trials(self) -> TrialProvider:
        """Get cloud trial provider"""
        pass

    @property
    @abstractmethod
    def feature_usage(self) -> FeatureUsageProvider:
        """Get feature usage provider"""
        pass

    @property
    @abstractmethod
    def plan_config(self) -> PlanConfigProvider:
        """Get plan config provider"""
        pass

    @property
    @abstractmethod
    def audit_logs(self) -> AuditLogProvider:
        """Get audit log provider"""
        pass

    @property
    @abstractmethod
    def deletion_requests(self) -> DeletionRequestProvider:
        """Get deletion request provider"""
        pass

    @property
    @abstractmethod
    def user_deletion(self) -> UserDeletionProvider:
        """Get user deletion provider"""
        pass

    @property
    @abstractmethod
    def user_tools(self) -> UserToolProvider:
        """Get user tool provider"""
        pass

    @property
    @abstractmethod
    def orders(self) -> OrderProvider:
        """Get order provider"""
        pass

    @property
    @abstractmethod
    def invite_keys(self) -> InviteKeyProvider:
        """Get invite key provider"""
        pass

    @property
    @abstractmethod
    def module_access(self) -> ModuleAccessProvider:
        """Get module access provider"""
        pass

    @property
    @abstractmethod
    def reports(self) -> ReportProvider:
        """Get report provider"""
        pass

    @property
    @abstractmethod
    def issues(self) -> IssueProvider:
        """Get issue provider"""
        pass

    @property
    @abstractmethod
    def pull_requests(self) -> PullRequestProvider:
        """Get pull request provider"""
        pass

    @property
    @abstractmethod
    def template_issues(self) -> TemplateIssueProvider:
        """Get template issue provider"""
        pass

    @property
    @abstractmethod
    def wallet(self) -> WalletProvider:
        """Get wallet/credits provider"""
        pass

    @property
    @abstractmethod
    def webhooks(self) -> WebhookProvider:
        """Get webhook provider"""
        pass

    @property
    @abstractmethod
    def schedules(self) -> ScheduleProvider:
        """Get schedule provider"""
        pass

    @property
    @abstractmethod
    def devices(self) -> DeviceProvider:
        """Get device provider"""
        pass

    @property
    @abstractmethod
    def desktop_oauth(self) -> DesktopOAuthProvider:
        """Get desktop OAuth provider"""
        pass

    @property
    @abstractmethod
    def vscode_auth_codes(self) -> VscodeAuthCodeProvider:
        """Get VSCode auth-code provider"""
        pass

    @property
    @abstractmethod
    def collaboration_quota(self) -> CollaborationQuotaProvider:
        """Get collaboration quota provider"""
        pass

    @property
    @abstractmethod
    def collaboration_requests(self) -> CollaborationRequestProvider:
        """Get collaboration request provider"""
        pass

    @property
    @abstractmethod
    def collaboration(self) -> CollaborationProvider:
        """Get collaboration invite/member provider"""
        pass

    @property
    @abstractmethod
    def creator_program(self) -> CreatorProgramProvider:
        """Get creator program provider"""
        pass

    @property
    @abstractmethod
    def line(self) -> LineProvider:
        """Get LINE message/conversation provider"""
        pass

    @property
    @abstractmethod
    def breakpoints(self) -> BreakpointProvider:
        """Get durable breakpoint persistence provider"""
        pass
