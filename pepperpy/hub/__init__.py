"""Pepper Hub - A centralized hub for managing AI artifacts.

This package provides a simple and consistent way to manage AI artifacts like agents,
prompts, and workflows in a local directory structure (.pepper_hub).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

import yaml
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
from pepperpy.hub.agents.base import Agent as BaseAgentImpl
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
    """Hub for managing Pepperpy components like agents and workflows.

    The hub provides easy access to:
    - Pre-configured agents
    - Workflow templates
    - Team compositions
    - Shared resources

    Example:
        >>> hub = pepper.hub
        >>> researcher = await hub.agent("researcher")
        >>> team = await hub.team("research-team")
        >>> flow = await hub.workflow("research-flow")

    """

    def __init__(self, client: PepperpyClient):
        """Initialize the hub."""
        self._client = client
        self._local_path = Path.home() / ".pepperpy" / "hub"
        self._local_path.mkdir(parents=True, exist_ok=True)

        # Create standard directories
        (self._local_path / "agents").mkdir(exist_ok=True)
        (self._local_path / "workflows").mkdir(exist_ok=True)
        (self._local_path / "teams").mkdir(exist_ok=True)
        (self._local_path / "templates").mkdir(exist_ok=True)

        # Initialize registries
        self._agent_registry = AgentRegistry()
        self._workflow_registry = WorkflowRegistry()

    async def agent(
        self,
        name: str,
        *,
        config: dict[str, Any] | None = None,
        capabilities: list[str] | None = None,
        **kwargs: Any,
    ) -> BaseAgent:
        """Load an agent from the hub."""
        # First check local hub
        local_config = self._local_path / "agents" / f"{name}.yaml"
        if local_config.exists():
            agent = await self._load_local_agent(name, local_config, **kwargs)
            if capabilities and isinstance(agent, BaseAgentImpl):
                self._validate_agent_capabilities(agent, capabilities)
            return agent

        # Then try built-in agents
        if name == "researcher":
            agent = await self._client.create_agent("research_assistant", **kwargs)
            if capabilities and isinstance(agent, BaseAgentImpl):
                self._validate_agent_capabilities(agent, capabilities)
            return agent

        raise ValueError(f"Agent '{name}' not found in hub")

    def _validate_agent_capabilities(
        self,
        agent: BaseAgentImpl,
        required_capabilities: list[str],
    ) -> None:
        """Validate that an agent has the required capabilities."""
        agent_caps = set(agent.capabilities)
        missing = [cap for cap in required_capabilities if cap not in agent_caps]
        if missing:
            raise ValueError(
                f"Agent missing required capabilities: {', '.join(missing)}"
            )

    async def team(self, name: str) -> "Team":
        """Load a team from the hub.

        Args:
            name: Name of the team to load

        Returns:
            The loaded team instance

        Example:
            >>> team = await hub.team("research-team")
            >>> async with team.run("Research AI") as session:
            ...     print(session.current_step)
            ...     print(session.thoughts)
            ...     if session.needs_input:
            ...         session.provide_input("More details")

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
            >>> async with flow.run("Research AI") as session:
            ...     print(session.current_step)
            ...     print(session.progress)

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
        *,
        base: str | None = None,
        config: dict[str, Any] | None = None,
        capabilities: list[str] | None = None,
    ) -> BaseAgent:
        """Create a new agent in the hub."""
        # Validate name
        if "/" in name or "\\" in name:
            raise ValueError("Agent name cannot contain path separators")

        # Create agent directory
        agent_dir = self._local_path / "agents"
        agent_dir.mkdir(exist_ok=True)

        # Create config
        agent_config = {
            "name": name,
            "base": base,
            "version": "0.1.0",
            "capabilities": capabilities or [],
            **(config or {}),
        }

        # Save config
        config_path = agent_dir / f"{name}.yaml"
        with open(config_path, "w") as f:
            yaml.dump(agent_config, f)

        # Load and return agent
        agent = await self._load_local_agent(name, config_path)
        if capabilities and isinstance(agent, BaseAgentImpl):
            self._validate_agent_capabilities(agent, capabilities)
        return agent

    async def publish(self, name: str, type: str = "agent") -> None:
        """Publish a component to make it available for sharing.

        Args:
            name: Name of the component to publish
            type: Type of component ("agent", "workflow", "team")

        Example:
            >>> await hub.publish("custom-researcher")  # Share agent
            >>> await hub.publish("research-flow", type="workflow")

        """
        # Validate type
        if type not in ["agent", "workflow", "team"]:
            raise ValueError(f"Invalid component type: {type}")

        # Get component path
        component_dir = self._local_path / f"{type}s"
        component_path = component_dir / f"{name}.yaml"

        if not component_path.exists():
            raise ValueError(f"{type.title()} '{name}' not found")

        # TODO: Implement sharing mechanism
        logger.info(f"Publishing {type} '{name}'... (Not implemented yet)")

    async def list_agents(
        self,
        *,
        capabilities: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List available agents.

        Args:
            capabilities: Optional list of required capabilities to filter by

        Returns:
            List of agent metadata including name, version, and capabilities

        Example:
            >>> agents = await hub.list_agents(
            ...     capabilities=["research", "summarize"]
            ... )
            >>> for agent in agents:
            ...     print(f"{agent['name']} ({agent['version']})")
            ...     print(f"Capabilities: {agent['capabilities']}")

        """
        agents = []

        # List local agents
        agent_dir = self._local_path / "agents"
        if agent_dir.exists():
            for config_file in agent_dir.glob("*.yaml"):
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                    if capabilities:
                        agent_caps = set(config.get("capabilities", []))
                        if not all(cap in agent_caps for cap in capabilities):
                            continue
                    agents.append(config)

        # Add built-in agents
        built_in = [
            {
                "name": "researcher",
                "version": "0.1.0",
                "capabilities": ["research", "analyze", "summarize"],
            },
            {
                "name": "writer",
                "version": "0.1.0",
                "capabilities": ["write", "edit", "adapt"],
            },
        ]
        for agent in built_in:
            if capabilities:
                agent_caps = set(agent["capabilities"])
                if not all(cap in agent_caps for cap in capabilities):
                    continue
            agents.append(agent)

        return agents

    async def _load_local_agent(
        self,
        name: str,
        config_path: Path,
        **kwargs: Any,
    ) -> BaseAgent:
        """Load an agent from a local configuration file."""
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Apply runtime configuration
        if kwargs:
            config.update(kwargs)

        # Create agent
        if config.get("base"):
            # Load base agent first
            base_agent = await self.agent(config["base"])
            # Extend base agent with custom config
            if isinstance(base_agent, BaseAgentImpl):
                return cast(BaseAgent, await base_agent.extend(config))
            return base_agent
        else:
            # Create new agent
            return await self._client.create_agent(name, **config)
