"""Configuration exposed by the local CE appliance."""

from fastapi import APIRouter

router = APIRouter(prefix="/config", tags=["Config"])

from .modules import router as modules_router
router.include_router(modules_router)


@router.get("/all")
async def get_all_config():
    """Return only local workflow-builder configuration.

    Provider names are static choices for user-authored workflow nodes. Reading
    this endpoint never contacts any provider.
    """
    from .modules import get_llm_config

    llm = await get_llm_config()
    return {
        "ok": True,
        "config": {
            "llm": {
                "providers": llm["providers"],
                "defaults": llm["defaults"],
            },
        },
    }
