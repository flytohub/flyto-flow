"""CE environment settings with offline-safe defaults."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional


ENV_REGISTRY = {
    "DEPLOYMENT_MODE": {"default": "offline", "required": False},
    "DEBUG": {"default": "false", "required": False},
    "API_HOST": {"default": "localhost", "required": False},
    "API_PORT": {"default": "9000", "required": False},
    "CORS_ORIGINS": {"default": "", "required": False},
    "FLYTO_OFFLINE_DB_PATH": {"default": "", "required": False},
    "FLYTO_BACKEND_URL": {"default": "http://127.0.0.1:9000", "required": False},
    "FLYTO_FLOW_MCP_TOKEN": {"default": "", "required": False},
    "FLYTO_FLOW_MCP_TRUST_LOOPBACK_PROXY": {"default": "false", "required": False},
    "FLYTO_MCP_CACHE_TTL": {"default": "30", "required": False},
    "FLYTO_MCP_MAX_WAIT": {"default": "300", "required": False},
    "PLAYWRIGHT_BROWSERS_PATH": {"default": "", "required": False},
    "QUEUE_BACKEND": {"default": "sqlite", "required": False},
}


def validate_env(mode: str = "offline", *, fail_on_missing: bool = False) -> list[str]:
    del mode
    missing = [
        name
        for name, spec in ENV_REGISTRY.items()
        if spec.get("required") and not os.environ.get(name)
    ]
    if missing and fail_on_missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(sorted(missing)))
    return missing


try:
    from dotenv import load_dotenv

    env_file = Path(__file__).resolve().parents[1] / ".env"
    if env_file.is_file():
        load_dotenv(env_file)
except ImportError:
    pass


class Settings:
    def __init__(self):
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.deployment_mode = "offline"
        self.api_host = os.getenv("API_HOST", "localhost")
        self.api_port = int(os.getenv("API_PORT", "9000"))
        self.cors_origins = self._parse_cors_origins(os.getenv("CORS_ORIGINS", ""), self.debug)

    @staticmethod
    def _parse_cors_origins(value: str, debug: bool) -> list[str]:
        defaults = [
            "http://localhost:3000",
            "http://localhost:9000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:9000",
        ]
        if value == "*":
            if debug:
                return ["*"]
            logging.getLogger(__name__).warning("CORS wildcard rejected outside debug mode")
            return defaults
        if not value:
            return defaults
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        valid = [origin for origin in origins if origin.startswith(("http://", "https://"))]
        return valid or defaults

    @property
    def is_selfhosted(self) -> bool:
        return True

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
