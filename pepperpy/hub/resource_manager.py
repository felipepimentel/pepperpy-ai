"""Resource manager for loading Hub configurations.

This module provides functionality for loading and managing resource configurations
from the Hub directory structure.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from pepperpy.core.errors import NotFoundError


class ResourceManager:
    """Manager for Hub-based resource configurations.

    This class handles loading and managing resource configurations from
    the Hub directory structure.

    Attributes:
        hub_path: Path to the Hub directory
    """

    def __init__(self, hub_path: Optional[str] = None) -> None:
        """Initialize resource manager.

        Args:
            hub_path: Optional path to Hub directory
        """
        if hub_path is None:
            hub_path = os.path.join(os.getcwd(), ".pepper_hub")
        self.hub_path = Path(hub_path)

    def load_config(
        self,
        resource_type: str,
        name: str,
        version: str = "v1.0.0",
    ) -> Dict[str, Any]:
        """Load resource configuration from Hub.

        Args:
            resource_type: Type of resource (e.g. "agents", "memory")
            name: Name of the resource
            version: Version of the configuration

        Returns:
            Configuration dictionary

        Raises:
            NotFoundError: If configuration not found
        """
        # Try JSON first
        config_path = (
            self.hub_path / "resources" / resource_type / name / version / "config.json"
        )

        if config_path.exists():
            with config_path.open() as f:
                return json.load(f)

        # Try YAML next
        config_path = config_path.with_suffix(".yaml")
        if config_path.exists():
            with config_path.open() as f:
                return yaml.safe_load(f)

        raise NotFoundError(
            f"Configuration not found: {config_path.relative_to(self.hub_path)}"
        )


_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance.

    Returns:
        Global resource manager instance
    """
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager
