"""Public, immutable CE runtime contract."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/runtime-config")
async def runtime_config():
    return {
        "deploymentMode": "local_offline",
        "edition": "ce",
        "accountRequired": False,
        "deploymentId": "local",
        "network": {
            "internetAllowed": False,
            "airgap": True,
            "implicitOutboundAllowed": False,
        },
    }
