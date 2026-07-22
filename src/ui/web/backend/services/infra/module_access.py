"""CE module policy: every locally installed module is available."""

from typing import Iterable, Optional, Set


class LocalModuleAccessService:
    async def check_module_access(self, _actor, _module_id: str) -> bool:
        return True

    async def get_accessible_modules(
        self,
        _actor=None,
        include_all_ids: bool = False,
    ) -> Set[str]:
        return set()

    def filter_modules(self, modules: Iterable[dict], _accessible=None) -> list[dict]:
        return list(modules)


_service: Optional[LocalModuleAccessService] = None


def get_module_access_service() -> LocalModuleAccessService:
    global _service
    if _service is None:
        _service = LocalModuleAccessService()
    return _service
