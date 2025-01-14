"""Agent loader implementation."""

from pathlib import Path
from typing import Any

import yaml

from .types import AgentConfig


class AgentLoader:
    """Agent loader for loading agent definitions from YAML files."""

    def __init__(self, base_path: str | Path | None = None) -> None:
        """Initialize agent loader.

        Args:
            base_path: Base path for agent definitions. Defaults to assets/agents.
        """
        self.base_path = Path(base_path or "assets/agents")

    def load(self, agent_path: str) -> AgentConfig:
        """Load agent configuration from YAML file.

        Args:
            agent_path: Path to agent YAML file, relative to base_path.

        Returns:
            AgentConfig: Loaded agent configuration.

        Raises:
            FileNotFoundError: If agent file doesn't exist.
            ValueError: If agent configuration is invalid.
        """
        full_path = self._resolve_path(agent_path)
        if not full_path.exists():
            raise FileNotFoundError(f"Agent file not found: {full_path}")

        with open(full_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return self._parse_config(data)

    def discover(self, pattern: str | None = None) -> list[str]:
        """Discover available agent definitions.

        Args:
            pattern: Optional glob pattern to filter agents.

        Returns:
            List of available agent paths relative to base_path.
        """
        pattern = pattern or "**/*.yml"
        agents = []
        for path in self.base_path.glob(pattern):
            if path.is_file():
                rel_path = path.relative_to(self.base_path)
                agents.append(str(rel_path))
        return agents

    def _resolve_path(self, agent_path: str) -> Path:
        """Resolve full path for agent file.

        Args:
            agent_path: Relative path to agent file.

        Returns:
            Full path to agent file.
        """
        if agent_path.endswith(".yml"):
            return self.base_path / agent_path
        return self.base_path / f"{agent_path}.yml"

    def _parse_config(self, data: dict[str, Any]) -> AgentConfig:
        """Parse YAML data into agent configuration.

        Args:
            data: Raw YAML data.

        Returns:
            Parsed agent configuration.

        Raises:
            ValueError: If required fields are missing.
        """
        required_fields = {
            "name",
            "version",
            "description",
            "role",
            "capabilities",
            "tools",
            "settings",
            "metadata",
        }

        missing = required_fields - set(data.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        return AgentConfig(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            role=data["role"],
            capabilities=data["capabilities"],
            tools=data["tools"],
            settings=data["settings"],
            metadata=data["metadata"],
        )
