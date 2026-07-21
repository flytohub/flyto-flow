"""
Offline Data Provider

Combined provider for offline/desktop mode.
Core providers (workflows, templates, users, notifications, audit_logs)
use SQLite. All other cloud-only providers raise NotImplementedError on access.
"""

from gateway.providers.data.base import DataProvider, WorkflowProvider, TemplateProvider
from gateway.providers.data.offline.workflow import OfflineWorkflowProvider
from gateway.providers.data.offline.template import OfflineTemplateProvider
from gateway.providers.data.offline.user_profile import OfflineUserProfileProvider
from gateway.providers.data.offline.notification import OfflineNotificationProvider
from gateway.providers.data.offline.audit_log import OfflineAuditLogProvider
from gateway.providers.data.offline.stubs import (
    OfflineChatProvider,
    OfflineStorageProvider,
    OfflineDashboardProvider,
    OfflineAdminProvider,
    OfflineLicenseProvider,
    OfflineReviewProvider,
    OfflineSubscriptionProvider,
    OfflineEarningsProvider,
    OfflinePaymentProvider,
    OfflinePerCallSettlementProvider,
    OfflineAIUsageProvider,
    OfflineTelemetryProvider,
    OfflineDeletionRequestProvider,
    OfflineUserDeletionProvider,
    OfflineUserToolProvider,
    OfflineOrderProvider,
    OfflineInviteKeyProvider,
    OfflineModuleAccessProvider,
    OfflineReportProvider,
    OfflineIssueProvider,
    OfflinePullRequestProvider,
    OfflineTemplateIssueProvider,
    OfflineWalletProvider,
    OfflineApiKeyProvider,
    OfflineWebhookProvider,
    OfflineScheduleProvider,
    OfflineAIInsightsProvider,
    OfflineTrialProvider,
    OfflineFeatureUsageProvider,
    OfflinePlanConfigProvider,
    OfflineDeviceProvider,
    OfflineDesktopOAuthProvider,
    OfflineVscodeAuthCodeProvider,
    OfflineCollaborationQuotaProvider,
    OfflineCollaborationRequestProvider,
    OfflineCollaborationProvider,
    OfflineCreatorProgramProvider,
    OfflineLineProvider,
    OfflineBreakpointProvider,
)


class OfflineDataProvider(DataProvider):
    """Combined Offline data provider.

    Offline mode stores workflows, templates, user profiles, notifications,
    and audit logs in a local SQLite database. Cloud-only features (payments,
    dashboard, marketplace, etc.) raise NotImplementedError.
    """

    def __init__(self):
        """Initialize offline sub-providers."""
        self._workflows = OfflineWorkflowProvider()
        self._templates = OfflineTemplateProvider()
        self._users = OfflineUserProfileProvider()
        self._notifications = OfflineNotificationProvider()
        self._audit_logs = OfflineAuditLogProvider()

        # Stubs for cloud-only features
        self._chat = OfflineChatProvider()
        self._storage = OfflineStorageProvider()
        self._dashboard = OfflineDashboardProvider()
        self._admin = OfflineAdminProvider()
        self._licenses = OfflineLicenseProvider()
        self._reviews = OfflineReviewProvider()
        self._subscriptions = OfflineSubscriptionProvider()
        self._earnings = OfflineEarningsProvider()
        self._payments = OfflinePaymentProvider()
        self._per_call_settlement = OfflinePerCallSettlementProvider()
        self._ai_usage = OfflineAIUsageProvider()
        self._telemetry = OfflineTelemetryProvider()
        self._deletion_requests = OfflineDeletionRequestProvider()
        self._user_deletion = OfflineUserDeletionProvider()
        self._user_tools = OfflineUserToolProvider()
        self._orders = OfflineOrderProvider()
        self._invite_keys = OfflineInviteKeyProvider()
        self._module_access = OfflineModuleAccessProvider()
        self._reports = OfflineReportProvider()
        self._api_keys = OfflineApiKeyProvider()
        self._issues = OfflineIssueProvider()
        self._pull_requests = OfflinePullRequestProvider()
        self._template_issues = OfflineTemplateIssueProvider()
        self._wallet = OfflineWalletProvider()
        self._webhooks = OfflineWebhookProvider()
        self._schedules = OfflineScheduleProvider()
        self._ai_insights = OfflineAIInsightsProvider()
        self._trials = OfflineTrialProvider()
        self._feature_usage = OfflineFeatureUsageProvider()
        self._plan_config = OfflinePlanConfigProvider()
        self._devices = OfflineDeviceProvider()
        self._desktop_oauth = OfflineDesktopOAuthProvider()
        self._vscode_auth_codes = OfflineVscodeAuthCodeProvider()
        self._collaboration_quota = OfflineCollaborationQuotaProvider()
        self._collaboration_requests = OfflineCollaborationRequestProvider()
        self._collaboration = OfflineCollaborationProvider()
        self._creator_program = OfflineCreatorProgramProvider()
        self._line = OfflineLineProvider()
        self._breakpoints = OfflineBreakpointProvider()

    # ------------------------------------------------------------------
    # Core providers — fully functional offline
    # ------------------------------------------------------------------

    @property
    def workflows(self) -> WorkflowProvider:
        """Return the offline workflow provider."""
        return self._workflows

    @property
    def templates(self) -> TemplateProvider:
        """Return the offline template provider."""
        return self._templates

    @property
    def users(self):
        """Return the offline user profile provider."""
        return self._users

    @property
    def notifications(self):
        """Return the offline notification provider."""
        return self._notifications

    @property
    def audit_logs(self):
        """Return the offline audit log provider."""
        return self._audit_logs

    # ------------------------------------------------------------------
    # Cloud-only providers — stub instances that raise NotImplementedError
    # ------------------------------------------------------------------

    @property
    def chat(self):
        """Return stub chat provider (cloud-only)."""
        return self._chat

    @property
    def storage(self):
        """Return stub storage provider (cloud-only)."""
        return self._storage

    @property
    def dashboard(self):
        """Return stub dashboard provider (cloud-only)."""
        return self._dashboard

    @property
    def admin(self):
        """Return stub admin provider (cloud-only)."""
        return self._admin

    @property
    def licenses(self):
        """Return stub license provider (cloud-only)."""
        return self._licenses

    @property
    def reviews(self):
        """Return stub review provider (cloud-only)."""
        return self._reviews

    @property
    def subscriptions(self):
        """Return stub subscription provider (cloud-only)."""
        return self._subscriptions

    @property
    def earnings(self):
        """Return stub earnings provider (cloud-only)."""
        return self._earnings

    @property
    def payments(self):
        """Return stub payment provider (cloud-only)."""
        return self._payments

    @property
    def per_call_settlement(self):
        """Return stub per-call settlement provider (cloud-only)."""
        return self._per_call_settlement

    @property
    def ai_usage(self):
        """Return stub AI usage provider (cloud-only)."""
        return self._ai_usage

    @property
    def telemetry(self):
        """Return stub telemetry provider (cloud-only)."""
        return self._telemetry

    @property
    def ai_insights(self):
        """Return stub AI insights provider (cloud-only)."""
        return self._ai_insights

    @property
    def trials(self):
        """Return stub cloud trial provider (cloud-only)."""
        return self._trials

    @property
    def feature_usage(self):
        """Return stub feature usage provider (cloud-only)."""
        return self._feature_usage

    @property
    def plan_config(self):
        """Return stub plan config provider (cloud-only)."""
        return self._plan_config

    @property
    def deletion_requests(self):
        """Return stub deletion request provider (cloud-only)."""
        return self._deletion_requests

    @property
    def user_deletion(self):
        """Return stub user deletion provider (cloud-only)."""
        return self._user_deletion

    @property
    def user_tools(self):
        """Return stub user tool provider (cloud-only)."""
        return self._user_tools

    @property
    def orders(self):
        """Return stub order provider (cloud-only)."""
        return self._orders

    @property
    def invite_keys(self):
        """Return stub invite key provider (cloud-only)."""
        return self._invite_keys

    @property
    def module_access(self):
        """Return stub module access provider (cloud-only)."""
        return self._module_access

    @property
    def reports(self):
        """Return stub report provider (cloud-only)."""
        return self._reports

    @property
    def api_keys(self):
        """Return stub API key provider (cloud-only)."""
        return self._api_keys

    @property
    def issues(self):
        """Return stub issue provider (cloud-only)."""
        return self._issues

    @property
    def pull_requests(self):
        """Return stub pull request provider (cloud-only)."""
        return self._pull_requests

    @property
    def template_issues(self):
        """Return stub template issue provider (cloud-only)."""
        return self._template_issues

    @property
    def wallet(self):
        """Return stub wallet provider (cloud-only)."""
        return self._wallet

    @property
    def webhooks(self):
        """Return stub webhook provider (cloud-only)."""
        return self._webhooks

    @property
    def schedules(self):
        """Return stub schedule provider (cloud-only)."""
        return self._schedules

    @property
    def devices(self):
        """Return stub device provider (cloud-only)."""
        return self._devices

    @property
    def desktop_oauth(self):
        """Return stub desktop OAuth provider (cloud-only)."""
        return self._desktop_oauth

    @property
    def vscode_auth_codes(self):
        """Return stub VSCode auth-code provider (cloud-only)."""
        return self._vscode_auth_codes

    @property
    def collaboration_quota(self):
        """Return stub collaboration quota provider (cloud-only)."""
        return self._collaboration_quota

    @property
    def collaboration_requests(self):
        """Return stub collaboration request provider (cloud-only)."""
        return self._collaboration_requests

    @property
    def collaboration(self):
        """Return stub collaboration provider (cloud-only)."""
        return self._collaboration

    @property
    def creator_program(self):
        """Return stub creator program provider (cloud-only)."""
        return self._creator_program

    @property
    def line(self):
        """Return stub LINE provider (cloud-only)."""
        return self._line

    @property
    def breakpoints(self):
        """Return stub durable breakpoint provider (cloud-only)."""
        return self._breakpoints

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close offline data provider resources."""
        from gateway.storage.offline_db import close_offline_db

        close_offline_db()
