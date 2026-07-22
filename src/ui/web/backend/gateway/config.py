"""Immutable CE deployment configuration."""

from dataclasses import dataclass
from functools import lru_cache

from gateway.capabilities.definitions import DeploymentMode


@dataclass(frozen=True)
class GatewayConfig:
    deployment_mode: DeploymentMode = DeploymentMode.OFFLINE

    @property
    def is_offline(self) -> bool:
        return True

    @property
    def is_local(self) -> bool:
        return True

@lru_cache(maxsize=1)
def get_gateway_config() -> GatewayConfig:
    return GatewayConfig()


def reset_gateway_config() -> None:
    get_gateway_config.cache_clear()
