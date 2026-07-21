"""CE provider assembly. Only the offline provider bundle is available."""

from functools import lru_cache

from gateway.providers.access.simple import SimpleAccessProvider
from gateway.providers.audit.noop import NoopAuditProvider
from gateway.providers.auth.offline import OfflineAuthProvider
from gateway.providers.data.offline.provider import OfflineDataProvider


class ProviderHub:
    def __init__(self, mode=None):
        del mode
        self._auth_provider = OfflineAuthProvider()
        self._access_provider = SimpleAccessProvider()
        self._audit_provider = NoopAuditProvider()
        self._data_provider = OfflineDataProvider()

    @property
    def mode(self):
        from gateway.capabilities.definitions import DeploymentMode

        return DeploymentMode.OFFLINE

    @property
    def is_cloud(self) -> bool:
        return False

    @property
    def is_local(self) -> bool:
        return False

    @property
    def is_offline(self) -> bool:
        return True

    @property
    def is_enterprise(self) -> bool:
        return False

    @property
    def auth(self):
        return self._auth_provider

    @property
    def access(self):
        return self._access_provider

    @property
    def audit(self):
        return self._audit_provider

    @property
    def data(self):
        return self._data_provider

    def get_provider_info(self) -> dict:
        return {
            "mode": "offline",
            "auth": self.auth.provider_name,
            "access": self.access.name,
            "audit": self.audit.name,
            "data": self.data.__class__.__name__,
        }

    async def health_check(self) -> dict:
        return {
            "ok": True,
            "mode": "offline",
            "providers": {"offline": {"healthy": True}},
        }

    async def close(self) -> None:
        close = getattr(self.data, "close", None)
        if callable(close):
            result = close()
            if hasattr(result, "__await__"):
                await result


@lru_cache(maxsize=1)
def get_provider_hub() -> ProviderHub:
    return ProviderHub()


def reset_provider_hub() -> None:
    get_provider_hub.cache_clear()


def get_auth_provider():
    return get_provider_hub().auth


def get_access_provider():
    return get_provider_hub().access


def get_audit_provider():
    return get_provider_hub().audit


def get_data_provider():
    return get_provider_hub().data


def _data_provider(name: str):
    provider = get_data_provider()
    value = getattr(provider, name, None)
    if value is None:
        raise RuntimeError(f"offline data provider {name!r} is not available")
    return value


def get_chat_provider():
    return _data_provider("chat")


def get_user_profile_provider():
    return _data_provider("users")


def get_notification_provider():
    return _data_provider("notifications")


def get_storage_provider():
    return _data_provider("storage")


def get_webhook_provider():
    return _data_provider("webhooks")


def get_schedule_provider():
    return _data_provider("schedules")


def get_line_provider():
    return _data_provider("line")


def get_collaboration_provider():
    return _data_provider("collaboration")


def get_creator_program_provider():
    return _data_provider("creator_program")


async def check_providers_health() -> dict:
    return await get_provider_hub().health_check()


async def shutdown_providers() -> None:
    await get_provider_hub().close()
