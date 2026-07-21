"""Disabled hosted usage meter for Cloud CE."""


class _LocalMeteringService:
    async def get_current_usage(self, user_id: str) -> dict:
        del user_id
        return {"total_points": 0}


_service = _LocalMeteringService()


def get_metering_service():
    return _service


def init_metering_service():
    return _service
