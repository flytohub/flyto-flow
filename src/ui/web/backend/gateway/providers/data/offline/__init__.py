"""
Offline Data Provider Package

SQLite-backed data operations for offline/desktop mode.
"""

from gateway.providers.data.offline.workflow import OfflineWorkflowProvider
from gateway.providers.data.offline.template import OfflineTemplateProvider
from gateway.providers.data.offline.user_profile import OfflineUserProfileProvider
from gateway.providers.data.offline.notification import OfflineNotificationProvider
from gateway.providers.data.offline.audit_log import OfflineAuditLogProvider
from gateway.providers.data.offline.provider import OfflineDataProvider

__all__ = [
    "OfflineWorkflowProvider",
    "OfflineTemplateProvider",
    "OfflineUserProfileProvider",
    "OfflineNotificationProvider",
    "OfflineAuditLogProvider",
    "OfflineDataProvider",
]
