"""Local SQLite provider bundle used by CE."""

from gateway.providers.data.offline.template import OfflineTemplateProvider
from gateway.providers.data.offline.workflow import OfflineWorkflowProvider


class OfflineDataProvider:
    def __init__(self):
        self._workflows = OfflineWorkflowProvider()
        self._templates = OfflineTemplateProvider()

    @property
    def workflows(self):
        return self._workflows

    @property
    def templates(self):
        return self._templates

    async def close(self) -> None:
        from gateway.storage.offline_db import close_offline_db

        close_offline_db()
