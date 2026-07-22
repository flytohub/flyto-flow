"""Single-workspace CE access policy."""


class SimpleAccessProvider:
    @property
    def name(self) -> str:
        return "local-workspace"

    async def check_permission(self, _actor, _permission: str, resource: str | None = None) -> bool:
        del resource
        return True

    async def get_accessible_pages(self, _actor) -> list[str]:
        return [
            "/",
            "/my-templates",
            "/templates/builder",
            "/variables",
            "/observability",
        ]
