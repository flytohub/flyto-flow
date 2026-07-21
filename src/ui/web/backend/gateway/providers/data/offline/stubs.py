"""
Offline Stub Providers

Cloud-only providers that are not available in offline/desktop mode.
Each raises NotImplementedError with a descriptive message.
"""

import inspect

from gateway.providers.data.providers.chat_provider import ChatProvider
from gateway.providers.data.providers.storage_provider import StorageProvider
from gateway.providers.data.providers.dashboard_provider import DashboardProvider
from gateway.providers.data.providers.admin_provider import AdminProvider
from gateway.providers.data.providers.license_provider import LicenseProvider
from gateway.providers.data.providers.review_provider import ReviewProvider
from gateway.providers.data.providers.subscription_provider import SubscriptionProvider
from gateway.providers.data.providers.earnings_provider import EarningsProvider
from gateway.providers.data.providers.payment_provider import PaymentProvider
from gateway.providers.data.providers.per_call_settlement_provider import PerCallSettlementProvider
from gateway.providers.data.providers.ai_usage_provider import AIUsageProvider
from gateway.providers.data.providers.telemetry_provider import TelemetryProvider
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
from gateway.providers.data.providers.wallet_provider import WalletProvider
from gateway.providers.data.providers.api_key_provider import ApiKeyProvider
from gateway.providers.data.providers.webhook_provider import WebhookProvider
from gateway.providers.data.providers.schedule_provider import ScheduleProvider
from gateway.providers.data.providers.ai_insights_provider import AIInsightsProvider
from gateway.providers.data.providers.trial_provider import TrialProvider
from gateway.providers.data.providers.feature_usage_provider import FeatureUsageProvider
from gateway.providers.data.providers.plan_config_provider import PlanConfigProvider
from gateway.providers.data.providers.device_provider import DeviceProvider
from gateway.providers.data.providers.desktop_oauth_provider import DesktopOAuthProvider
from gateway.providers.data.providers.vscode_auth_code_provider import VscodeAuthCodeProvider
from gateway.providers.data.providers.collaboration_quota_provider import CollaborationQuotaProvider
from gateway.providers.data.providers.collaboration_request_provider import CollaborationRequestProvider
from gateway.providers.data.providers.collaboration_provider import CollaborationProvider
from gateway.providers.data.providers.creator_program_provider import CreatorProgramProvider
from gateway.providers.data.providers.line_provider import LineProvider
from gateway.providers.data.providers.breakpoint_provider import BreakpointProvider


def _offline_stub(provider_name: str):
    """Create a method that raises NotImplementedError for offline mode."""

    def _raise(*args, **kwargs):
        raise NotImplementedError(
            f"{provider_name} is not available in offline mode. This feature requires cloud deployment."
        )

    return _raise


def _make_stub_class(name: str, base_class: type) -> type:
    """
    Dynamically create a stub class that inherits from the given abstract base
    and overrides every abstract method to raise NotImplementedError.

    This avoids repeating the same boilerplate for 20+ cloud-only providers.
    """
    # Collect all abstract methods from the base class and its parents
    abstract_methods = set()
    for cls in base_class.__mro__:
        for attr_name, attr_val in vars(cls).items():
            if getattr(attr_val, "__isabstractmethod__", False):
                abstract_methods.add(attr_name)

    def _sync_stub(method_name: str):
        def _raise(*args, _name=name, **kwargs):
            raise NotImplementedError(
                f"{_name} is not available in offline mode. This feature requires cloud deployment."
            )

        _raise.__name__ = method_name
        _raise.__qualname__ = f"Offline{name}.{method_name}"
        return _raise

    def _async_stub(method_name: str):
        async def _raise(*args, _name=name, **kwargs):
            raise NotImplementedError(
                f"{_name} is not available in offline mode. This feature requires cloud deployment."
            )

        _raise.__name__ = method_name
        _raise.__qualname__ = f"Offline{name}.{method_name}"
        return _raise

    def _property_stub(method_name: str):
        def _raise(self, _name=name):
            raise NotImplementedError(
                f"{_name} is not available in offline mode. This feature requires cloud deployment."
            )

        _raise.__name__ = method_name
        _raise.__qualname__ = f"Offline{name}.{method_name}"
        return property(_raise)

    # Build a namespace with stub implementations
    namespace = {}
    for method_name in abstract_methods:
        method = getattr(base_class, method_name)
        if isinstance(method, property):
            namespace[method_name] = _property_stub(method_name)
        elif inspect.iscoroutinefunction(method):
            namespace[method_name] = _async_stub(method_name)
        else:
            namespace[method_name] = _sync_stub(method_name)

    # Create the class dynamically
    return type(f"Offline{name}", (base_class,), namespace)


# ---------------------------------------------------------------------------
# Generate all stub classes
# ---------------------------------------------------------------------------

OfflineChatProvider = _make_stub_class("ChatProvider", ChatProvider)
OfflineStorageProvider = _make_stub_class("StorageProvider", StorageProvider)
OfflineDashboardProvider = _make_stub_class("DashboardProvider", DashboardProvider)
OfflineAdminProvider = _make_stub_class("AdminProvider", AdminProvider)
OfflineLicenseProvider = _make_stub_class("LicenseProvider", LicenseProvider)
OfflineReviewProvider = _make_stub_class("ReviewProvider", ReviewProvider)
OfflineSubscriptionProvider = _make_stub_class("SubscriptionProvider", SubscriptionProvider)
OfflineEarningsProvider = _make_stub_class("EarningsProvider", EarningsProvider)
OfflinePaymentProvider = _make_stub_class("PaymentProvider", PaymentProvider)
OfflinePerCallSettlementProvider = _make_stub_class(
    "PerCallSettlementProvider",
    PerCallSettlementProvider,
)
OfflineAIUsageProvider = _make_stub_class("AIUsageProvider", AIUsageProvider)
OfflineTelemetryProvider = _make_stub_class("TelemetryProvider", TelemetryProvider)
OfflineDeletionRequestProvider = _make_stub_class("DeletionRequestProvider", DeletionRequestProvider)
OfflineUserDeletionProvider = _make_stub_class("UserDeletionProvider", UserDeletionProvider)
OfflineUserToolProvider = _make_stub_class("UserToolProvider", UserToolProvider)
OfflineOrderProvider = _make_stub_class("OrderProvider", OrderProvider)
OfflineInviteKeyProvider = _make_stub_class("InviteKeyProvider", InviteKeyProvider)
OfflineModuleAccessProvider = _make_stub_class("ModuleAccessProvider", ModuleAccessProvider)
OfflineReportProvider = _make_stub_class("ReportProvider", ReportProvider)
OfflineIssueProvider = _make_stub_class("IssueProvider", IssueProvider)
OfflinePullRequestProvider = _make_stub_class("PullRequestProvider", PullRequestProvider)
OfflineTemplateIssueProvider = _make_stub_class("TemplateIssueProvider", TemplateIssueProvider)
OfflineWalletProvider = _make_stub_class("WalletProvider", WalletProvider)
OfflineApiKeyProvider = _make_stub_class("ApiKeyProvider", ApiKeyProvider)
OfflineWebhookProvider = _make_stub_class("WebhookProvider", WebhookProvider)
OfflineScheduleProvider = _make_stub_class("ScheduleProvider", ScheduleProvider)
OfflineAIInsightsProvider = _make_stub_class("AIInsightsProvider", AIInsightsProvider)
OfflineTrialProvider = _make_stub_class("TrialProvider", TrialProvider)
OfflineFeatureUsageProvider = _make_stub_class("FeatureUsageProvider", FeatureUsageProvider)
OfflinePlanConfigProvider = _make_stub_class("PlanConfigProvider", PlanConfigProvider)
OfflineDeviceProvider = _make_stub_class("DeviceProvider", DeviceProvider)
OfflineDesktopOAuthProvider = _make_stub_class(
    "DesktopOAuthProvider",
    DesktopOAuthProvider,
)
OfflineVscodeAuthCodeProvider = _make_stub_class(
    "VscodeAuthCodeProvider",
    VscodeAuthCodeProvider,
)
OfflineCollaborationQuotaProvider = _make_stub_class(
    "CollaborationQuotaProvider",
    CollaborationQuotaProvider,
)
OfflineCollaborationRequestProvider = _make_stub_class(
    "CollaborationRequestProvider",
    CollaborationRequestProvider,
)
OfflineCollaborationProvider = _make_stub_class(
    "CollaborationProvider",
    CollaborationProvider,
)
OfflineCreatorProgramProvider = _make_stub_class(
    "CreatorProgramProvider",
    CreatorProgramProvider,
)
OfflineLineProvider = _make_stub_class("LineProvider", LineProvider)
OfflineBreakpointProvider = _make_stub_class("BreakpointProvider", BreakpointProvider)


__all__ = [
    "OfflineChatProvider",
    "OfflineStorageProvider",
    "OfflineDashboardProvider",
    "OfflineAdminProvider",
    "OfflineLicenseProvider",
    "OfflineReviewProvider",
    "OfflineSubscriptionProvider",
    "OfflineEarningsProvider",
    "OfflinePaymentProvider",
    "OfflinePerCallSettlementProvider",
    "OfflineAIUsageProvider",
    "OfflineTelemetryProvider",
    "OfflineDeletionRequestProvider",
    "OfflineUserDeletionProvider",
    "OfflineUserToolProvider",
    "OfflineOrderProvider",
    "OfflineInviteKeyProvider",
    "OfflineModuleAccessProvider",
    "OfflineReportProvider",
    "OfflineIssueProvider",
    "OfflinePullRequestProvider",
    "OfflineTemplateIssueProvider",
    "OfflineWalletProvider",
    "OfflineApiKeyProvider",
    "OfflineWebhookProvider",
    "OfflineScheduleProvider",
    "OfflineAIInsightsProvider",
    "OfflineTrialProvider",
    "OfflineFeatureUsageProvider",
    "OfflinePlanConfigProvider",
    "OfflineDeviceProvider",
    "OfflineDesktopOAuthProvider",
    "OfflineVscodeAuthCodeProvider",
    "OfflineCollaborationQuotaProvider",
    "OfflineCollaborationRequestProvider",
    "OfflineCollaborationProvider",
    "OfflineCreatorProgramProvider",
    "OfflineLineProvider",
    "OfflineBreakpointProvider",
]
