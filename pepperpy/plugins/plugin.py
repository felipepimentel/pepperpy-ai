"""Plugin base class for PepperPy.

This module defines the base class for all PepperPy plugins.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

import yaml

from pepperpy.core.logging import get_logger


class PepperpyPlugin(ABC):
    """Base class for all PepperPy plugins.

    All plugins must inherit from this class and implement its abstract methods.
    This ensures consistent behavior across all plugins.

    Attributes:
        name: Plugin name
        version: Plugin version
        description: Plugin description
        author: Plugin author
    """

    name: str = ""
    version: str = "0.1.0"
    description: str = ""
    author: str = "PepperPy Team"

    def __init__(self, **config: Any) -> None:
        """Initialize plugin with configuration.

        Args:
            **config: Plugin configuration
        """
        self._config = config
        self._metadata = {}
        self.initialized = False
        self._logger = get_logger(self.__class__.__module__)

        # Load metadata and inject env variables
        self._load_metadata()
        self._inject_env_variables()

    def _load_metadata(self) -> None:
        """Load plugin metadata from plugin.yaml file."""
        try:
            # Get plugin directory from module path
            module_path = Path(self.__class__.__module__.replace(".", "/"))
            plugin_dir = Path(__file__).parent.parent.parent / "plugins"

            # Get plugin name from module path
            parts = module_path.parts
            if "plugins" in parts:
                plugin_idx = parts.index("plugins")
                if len(parts) > plugin_idx + 1:
                    plugin_name = parts[plugin_idx + 1]
                    yaml_path = plugin_dir / plugin_name / "plugin.yaml"

                    if yaml_path.exists():
                        with open(yaml_path) as f:
                            self._metadata = yaml.safe_load(f)

                            # Update class attributes from metadata
                            if "name" in self._metadata:
                                self.name = self._metadata["name"]
                            if "version" in self._metadata:
                                self.version = self._metadata["version"]
                            if "description" in self._metadata:
                                self.description = self._metadata["description"]
                            if "author" in self._metadata:
                                self.author = self._metadata["author"]
        except Exception as e:
            self._logger.warning(f"Failed to load metadata: {e}")

    def _inject_env_variables(self) -> None:
        """Inject environment variables into configuration."""
        if not self._metadata:
            return

        required_keys = self._metadata.get("required_config_keys", [])
        config_schema = self._metadata.get("config_schema", {})

        for key in required_keys:
            if key in self._config and self._config[key] is not None:
                continue

            # Try schema-defined env var
            if key in config_schema and "env_var" in config_schema[key]:
                env_var = config_schema[key]["env_var"]
                if env_var in os.environ:
                    self._config[key] = os.environ[env_var]
                    continue

            # Try standard patterns
            patterns = [
                f"PEPPERPY_{self.name.upper()}_{key.upper()}",
                f"{self.name.upper()}_{key.upper()}",
            ]

            for pattern in patterns:
                if pattern in os.environ:
                    self._config[key] = os.environ[pattern]
                    break

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self._config.get(key, default)

    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata.

        Returns:
            Dictionary with plugin metadata
        """
        return self._metadata

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize plugin.

        This method should be called before using the plugin.
        It should initialize any resources needed by the plugin.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up plugin resources.

        This method should be called when the plugin is no longer needed.
        It should clean up any resources allocated by the plugin.
        """
        pass

    async def __aenter__(self) -> "PepperpyPlugin":
        """Enter async context."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self.cleanup()
