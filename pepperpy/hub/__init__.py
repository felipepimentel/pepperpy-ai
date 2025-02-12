"""Pepper Hub - A centralized hub for managing AI artifacts.

This package provides a simple and consistent way to manage AI artifacts like agents,
prompts, and workflows in a local directory structure (.pepper_hub).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from structlog import get_logger

from pepperpy.core.base import BaseAgent
from pepperpy.core.client import PepperpyClient
from pepperpy.core.errors import ConfigurationError
from pepperpy.hub.agents import (
    Agent,
    AgentConfig,
    AgentRegistry,
    ResearchAssistantAgent,
)
from pepperpy.hub.prompts import PromptRegistry
from pepperpy.hub.storage import LocalStorage
from pepperpy.hub.teams import Team
from pepperpy.hub.workflow import WorkflowEngine
from pepperpy.hub.workflows import Workflow, WorkflowConfig, WorkflowRegistry
from pepperpy.monitoring import logger

# Configure logger
logger = get_logger()

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentRegistry",
    "PromptRegistry",
    "Workflow",
    "WorkflowConfig",
    "WorkflowRegistry",
    "PepperpyHub",
    "ResearchAssistantAgent",
]


class Hub:
    """Central hub for managing Pepperpy artifacts and workflows."""

    def __init__(self, storage_dir: Union[str, Path]) -> None:
        """Initialize the hub.

        Args:
        ----
            storage_dir: Directory for storing artifacts.

        """
        self.storage_dir = Path(storage_dir)
        self.storage = LocalStorage(self.storage_dir)
        self.workflow_engine = WorkflowEngine(self.storage_dir / "workflows")
        self.log = logger.bind(component="hub")

        # Ensure directories exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        (self.storage_dir / "workflows").mkdir(exist_ok=True)
        (self.storage_dir / "agents").mkdir(exist_ok=True)

    def save_artifact(
        self,
        artifact_type: str,
        artifact_id: str,
        data: Dict[str, Any],
        version: Optional[str] = None,
    ) -> None:
        """Save an artifact to the hub.

        Args:
        ----
            artifact_type: Type of artifact (e.g., "agents", "workflows").
            artifact_id: ID of the artifact.
            data: Artifact data to save.
            version: Optional version string.

        """
        self.storage.save_artifact(artifact_type, artifact_id, data, version)

    def load_artifact(
        self,
        artifact_type: str,
        artifact_id: str,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Load an artifact from the hub.

        Args:
        ----
            artifact_type: Type of artifact (e.g., "agents", "workflows").
            artifact_id: ID of the artifact.
            version: Optional version string.

        Returns:
        -------
            Dict[str, Any]: Loaded artifact data.

        Raises:
        ------
            ConfigurationError: If artifact cannot be loaded.

        """
        try:
            return self.storage.load_artifact(artifact_type, artifact_id, version)
        except Exception as e:
            raise ConfigurationError(f"Failed to load artifact {artifact_id}: {str(e)}")

    def list_artifacts(
        self,
        artifact_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List available artifacts of a given type.

        Args:
        ----
            artifact_type: Type of artifacts to list (optional).

        Returns:
        -------
            List[Dict[str, Any]]: List of artifact metadata including name,
            type, latest version, and all available versions.

        """
        return self.storage.list_artifacts(artifact_type)

    def delete_artifact(
        self,
        artifact_type: str,
        artifact_id: str,
        version: Optional[str] = None,
    ) -> None:
        """Delete an artifact from the hub.

        Args:
        ----
            artifact_type: Type of artifact to delete.
            artifact_id: ID of the artifact.
            version: Optional version to delete.

        """
        self.storage.delete_artifact(artifact_type, artifact_id, version)


class PepperpyHub:
    """Hub for managing Pepperpy components like agents and workflows."""

    def __init__(self, client: PepperpyClient):
        """Initialize the hub.

        Args:
            client: The Pepperpy client instance

        """
        self._client = client
        self._local_path = Path.home() / ".pepperpy" / "hub"
        self._local_path.mkdir(parents=True, exist_ok=True)

    async def agent(self, name: str) -> BaseAgent:
        """Load an agent from the hub.

        Args:
            name: Name of the agent to load

        Returns:
            The loaded agent instance

        Example:
            >>> researcher = await hub.agent("researcher")
            >>> result = await researcher.research("AI")

        """
        # First check local hub
        local_config = self._local_path / "agents" / f"{name}.yaml"
        if local_config.exists():
            return await self._load_local_agent(name, local_config)

        # Then try built-in agents
        if name == "researcher":
            return await self._client.create_agent("research_assistant")

        raise ValueError(f"Agent '{name}' not found in hub")

    async def team(self, name: str) -> "Team":
        """Load a team from the hub.

        Args:
            name: Name of the team to load

        Returns:
            The loaded team instance

        Example:
            >>> team = await hub.team("research-team")
            >>> result = await team.run("Research AI")

        """
        from pepperpy.hub.teams import Team

        # Check local hub
        local_config = self._local_path / "teams" / f"{name}.yaml"
        if local_config.exists():
            return await Team.from_config(self._client, local_config)

        raise ValueError(f"Team '{name}' not found in hub")

    async def workflow(self, name: str) -> "Workflow":
        """Load a workflow from the hub.

        Args:
            name: Name of the workflow to load

        Returns:
            The loaded workflow instance

        Example:
            >>> flow = await hub.workflow("research-flow")
            >>> result = await flow.run("Research AI")

        """
        from pepperpy.hub.workflows import Workflow

        # Check local hub
        local_config = self._local_path / "workflows" / f"{name}.yaml"
        if local_config.exists():
            return await Workflow.from_config(self._client, local_config)

        raise ValueError(f"Workflow '{name}' not found in hub")

    async def create_agent(
        self,
        name: str,
        base: Optional[str] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> BaseAgent:
        """Create a new agent in the hub.

        Args:
            name: Name for the new agent
            base: Optional base agent to inherit from
            config: Optional configuration for the agent

        Returns:
            The created agent instance

        Example:
            >>> agent = await hub.create_agent(
            ...     name="custom-researcher",
            ...     base="researcher",
            ...     config={"style": "technical"}
            ... )

        """
        # Validate name
        if "/" in name or "\\" in name:
            raise ValueError("Agent name cannot contain path separators")

        # Create agent directory
        agent_dir = self._local_path / "agents"
        agent_dir.mkdir(exist_ok=True)

        # Create config
        agent_config = {"name": name, "base": base, **(config or {})}

        # Save config
        config_path = agent_dir / f"{name}.yaml"
        import yaml

        with open(config_path, "w") as f:
            yaml.dump(agent_config, f)

        # Load and return agent
        return await self._load_local_agent(name, config_path)

    async def publish(self, name: str) -> None:
        """Publish a local component to the public hub.

        Args:
            name: Name of the component to publish

        Example:
            >>> await hub.publish("custom-researcher")

        """
        # TODO[v2.0]: Implement hub publishing
        raise NotImplementedError("Hub publishing not yet implemented")

    async def _load_local_agent(self, name: str, config_path: Path) -> BaseAgent:
        """Load an agent from a local configuration file."""
        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Get base agent if specified
        base = config.get("base")
        if base:
            base_agent = await self.agent(base)
            # TODO: Apply config overrides
            return base_agent

        # Create new agent
        return await self._client.create_agent(name)
