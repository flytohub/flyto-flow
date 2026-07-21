"""Disabled AI insights compatibility surface for Cloud CE."""


class _DisabledAIInsightsService:
    enabled = False

    @staticmethod
    def _get_config() -> dict:
        return {"auto_root_cause": False}


_service = _DisabledAIInsightsService()


def get_ai_insights_service():
    return _service
