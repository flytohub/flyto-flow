"""Flow has one deployment mode: a local offline appliance."""

from enum import Enum


class DeploymentMode(str, Enum):
    OFFLINE = "offline"
