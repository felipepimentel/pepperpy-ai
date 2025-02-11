"""Agent registry for managing agent configurations and versions.

This module provides a centralized registry for managing agent configurations
and handling semantic versioning of agents.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from packaging import version
from pydantic import BaseModel

from pepperpy.core.errors import ConfigurationError
from pepperpy.monitoring import logger

log = logger.bind(module="registry")


class AgentMetadata(BaseModel):
    """Metadata for an agent version."""

    name: str
    description: str
    version: str
    config: Dict[str, Any]


class AgentRegistry:
    """Registry for managing agent configurations and versions.

    This class handles:
    - Loading agent configurations from the hub
    - Managing semantic versioning
    - Providing access to agent configurations
    """

    def __init__(self, hub_path: Optional[Path] = None):
        """Initialize the agent registry.

        Args:
        ----
            hub_path: Optional path to the hub directory. If not provided,
                     will use PEPPERPY_HUB_PATH env var or default to ~/.pepper_hub

        """
        self.hub_path = hub_path or Path(
            os.getenv("PEPPERPY_HUB_PATH", str(Path.home() / ".pepper_hub"))
        )
        self._cache: Dict[str, Dict[str, AgentMetadata]] = {}

    async def get_agent_config(
        self, agent_type: str, version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get the configuration for an agent.

        Args:
        ----
            agent_type: Type of agent to get config for
            version: Optional specific version to get. If not provided,
                    will return the latest version.

        Returns:
        -------
            Agent configuration dictionary

        Raises:
        ------
            ValueError: If agent_type is invalid or version not found
            ConfigurationError: If configuration is invalid

        """
        # Load configurations if not cached
        if agent_type not in self._cache:
            await self._load_agent_configs(agent_type)

        if not self._cache.get(agent_type):
            raise ValueError(f"Invalid agent type: {agent_type}")

        # Get specific version or latest
        if version:
            if version not in self._cache[agent_type]:
                raise ValueError(f"Version {version} not found for agent {agent_type}")
            agent_meta = self._cache[agent_type][version]
        else:
            # Get latest version using semantic versioning
            latest = self._get_latest_version(agent_type)
            agent_meta = self._cache[agent_type][latest]

        return agent_meta.config

    def _get_latest_version(self, agent_type: str) -> str:
        """Get the latest version for an agent type using semantic versioning.

        Args:
        ----
            agent_type: Type of agent to get latest version for

        Returns:
        -------
            Latest version string

        Raises:
        ------
            ValueError: If no versions found for agent type

        """
        if not self._cache.get(agent_type):
            raise ValueError(f"No versions found for agent type: {agent_type}")

        # Sort versions using packaging.version
        versions = sorted(
            self._cache[agent_type].keys(), key=lambda v: version.parse(v), reverse=True
        )
        return versions[0]

    async def _load_agent_configs(self, agent_type: str) -> None:
        """Load all configurations for an agent type.

        Args:
        ----
            agent_type: Type of agent to load configs for

        Raises:
        ------
            ConfigurationError: If configurations cannot be loaded

        """
        agent_dir = self.hub_path / "agents" / agent_type
        if not agent_dir.exists():
            log.warning(f"Agent directory not found: {agent_dir}")
            return

        try:
            # Initialize cache for this agent type
            self._cache[agent_type] = {}

            # Load each version's config
            for config_file in agent_dir.glob("*.yaml"):
                try:
                    with open(config_file) as f:
                        config_data = yaml.safe_load(f)

                    metadata = AgentMetadata(**config_data)
                    self._cache[agent_type][metadata.version] = metadata

                except Exception as e:
                    log.error(
                        "Failed to load agent config",
                        file=str(config_file),
                        error=str(e),
                    )

        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configurations for {agent_type}: {str(e)}"
            )
