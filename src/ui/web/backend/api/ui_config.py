"""Minimal local UI preferences for CE."""

from fastapi import APIRouter
from api.responses import success_response

router = APIRouter(prefix="/ui-config", tags=["UI Config"])


@router.get("")
@router.get("/")
async def get_ui_config():
    return success_response(config={"theme": "dark", "show_tutorials": False})


@router.get("/pages")
async def get_ui_pages():
    return success_response(pages=[])
