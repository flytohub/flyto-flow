"""
Hot Updater Configuration

Configuration management for the updater.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load user configuration from file."""
    default_config = {
        "auto_update": True,
        "check_interval_hours": 1,
        "include_prereleases": False,
        "pinned_version": None,
        "last_check": None,
        "current_version": None,
        # Frontend hot update
        "frontend_auto_update": True,
        "frontend_version": None,
    }

    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                loaded = json.load(f)
                default_config.update(loaded)
        except Exception as e:
            logger.warning("Failed to load config: %s", e)

    return default_config


def save_config(config_path: Path, config: Dict[str, Any]) -> None:
    """Save user configuration to file."""
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error("Failed to save config: %s", e)
