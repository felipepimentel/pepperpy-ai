"""Plugin configuration for Pepperpy CLI.

This module provides functionality to manage plugin configurations.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Type definitions
PluginConfig = Dict[str, Any]


def get_plugin_config_path(plugin_id: str) -> Path:
    """Get the path to the plugin configuration file.

    Args:
        plugin_id: Plugin identifier

    Returns:
        Path to the plugin configuration file

    """
    return Path.home() / ".pepperpy" / "config" / "plugins" / f"{plugin_id}.json"


def load_plugin_config(plugin_id: str) -> PluginConfig:
    """Load configuration for a plugin.

    Args:
        plugin_id: Plugin identifier

    Returns:
        Plugin configuration dictionary

    """
    config_path = get_plugin_config_path(plugin_id)
    if not config_path.exists():
        logger.debug(f"No configuration found for plugin {plugin_id}")
        return {}

    try:
        with open(config_path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration for plugin {plugin_id}: {e}")
        return {}


def save_plugin_config(plugin_id: str, config: PluginConfig) -> bool:
    """Save configuration for a plugin.

    Args:
        plugin_id: Plugin identifier
        config: Plugin configuration dictionary

    Returns:
        True if successful, False otherwise

    """
    config_path = get_plugin_config_path(plugin_id)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration for plugin {plugin_id}: {e}")
        return False


def get_enabled_plugins() -> List[str]:
    """Get list of enabled plugins.

    Returns:
        List of plugin identifiers

    """
    config_dir = Path.home() / ".pepperpy" / "config" / "plugins"
    if not config_dir.exists():
        return []

    enabled_plugins = []
    for config_file in config_dir.glob("*.json"):
        plugin_id = config_file.stem
        try:
            with open(config_file) as f:
                config = json.load(f)
                if config.get("enabled", True):
                    enabled_plugins.append(plugin_id)
        except Exception:
            # Skip invalid config files
            pass

    return enabled_plugins


def is_plugin_enabled(plugin_id: str) -> bool:
    """Check if a plugin is enabled.

    Args:
        plugin_id: Plugin identifier

    Returns:
        True if the plugin is enabled, False otherwise

    """
    config = load_plugin_config(plugin_id)
    return config.get("enabled", True)


def enable_plugin(plugin_id: str) -> bool:
    """Enable a plugin.

    Args:
        plugin_id: Plugin identifier

    Returns:
        True if successful, False otherwise

    """
    config = load_plugin_config(plugin_id)
    config["enabled"] = True
    return save_plugin_config(plugin_id, config)


def disable_plugin(plugin_id: str) -> bool:
    """Disable a plugin.

    Args:
        plugin_id: Plugin identifier

    Returns:
        True if successful, False otherwise

    """
    config = load_plugin_config(plugin_id)
    config["enabled"] = False
    return save_plugin_config(plugin_id, config)
