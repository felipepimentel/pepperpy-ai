"""
Agent Topology Base Module.

Defines core interfaces and factories for agent topologies.
"""

import importlib
import os
from abc import ABC, abstractmethod
from typing import Any

from pepperpy.agent.base import BaseAgentProvider
from pepperpy.core.base import PepperpyError
from pepperpy.core.logging import get_logger
from pepperpy.plugin import PepperpyPlugin

logger = get_logger(__name__)


class TopologyError(PepperpyError):
    """Base error for topology operations."""

    pass


class AgentTopologyProvider(PepperpyPlugin, ABC):
    """Base interface for agent topology providers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize topology provider.

        Args:
            config: Configuration dictionary
        """
        super().__init__()
        self.config = config or {}
        self.agents: dict[str, BaseAgentProvider] = {}
        self.agent_configs: dict[str, dict[str, Any]] = self.config.get("agents", {})
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize topology resources."""
        if self.initialized:
            return

        # Override in subclass with specific initialization

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        for agent in self.agents.values():
            await agent.cleanup()
        self.agents = {}
        self.initialized = False

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the topology with input data.

        Args:
            input_data: Input data for the topology

        Returns:
            Execution results
        """
        pass

    async def add_agent(self, agent_id: str, agent: BaseAgentProvider) -> None:
        """Add an agent to the topology.

        Args:
            agent_id: Unique identifier for the agent
            agent: Agent provider instance
        """
        if agent_id in self.agents:
            await self.agents[agent_id].cleanup()

        self.agents[agent_id] = agent
        # Always initialize the agent - the agent will handle if already initialized
        await agent.initialize()

    async def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the topology.

        Args:
            agent_id: Agent identifier
        """
        if agent_id in self.agents:
            await self.agents[agent_id].cleanup()
            del self.agents[agent_id]


# Dictionary to hold registered topology providers
_TOPOLOGY_PROVIDERS: dict[str, type[AgentTopologyProvider]] = {}


def register_topology_provider(
    name: str, provider_class: type[AgentTopologyProvider]
) -> None:
    """Register a topology provider class.

    Args:
        name: Name of the topology provider
        provider_class: Provider class to register
    """
    _TOPOLOGY_PROVIDERS[name] = provider_class
    logger.debug(f"Registered topology provider: {name}")


# Factory function pattern
def create_topology(
    topology_type: str | None = None, **config: Any
) -> AgentTopologyProvider:
    """Create a topology provider.

    Args:
        topology_type: Type of topology to create
        **config: Configuration parameters

    Returns:
        Configured topology provider

    Raises:
        TopologyError: If topology type is invalid
    """
    topology_type = topology_type or os.environ.get(
        "PEPPERPY_TOPOLOGY_TYPE", "orchestrator"
    )

    try:
        # First check built-in providers
        if topology_type == "orchestrator":
            from .orchestrator import OrchestratorTopology

            return OrchestratorTopology(config)
        elif topology_type == "mesh":
            from .mesh import MeshTopology

            return MeshTopology(config)
        elif topology_type == "event":
            from .event import EventTopology

            return EventTopology(config)
        elif topology_type == "hierarchy":
            from .hierarchy import HierarchyTopology

            return HierarchyTopology(config)
        elif topology_type == "mcp":
            from .mcp import MCPTopology

            return MCPTopology(config)
        elif topology_type == "observer":
            from .observer import ObserverTopology

            return ObserverTopology(config)
        elif topology_type == "federation":
            from .federation import FederationTopology
            
            return FederationTopology(config)

        # Check registered topology providers
        elif topology_type in _TOPOLOGY_PROVIDERS:
            provider_class = _TOPOLOGY_PROVIDERS[topology_type]
            return provider_class(config)

        # Check for plugin-based providers
        else:
            # Try to find from plugins
            try:
                # First check if plugin registry is available
                try:
                    from pepperpy.plugin.registry import plugin_registry

                    # Get topology plugins through direct import rather than registry methods
                    # This avoids relying on specific registry API methods
                    if hasattr(plugin_registry, "get_plugins"):
                        topology_plugins = plugin_registry.get_plugins(
                            plugin_type="agent", category="topology"
                        )
                    elif hasattr(plugin_registry, "find_plugins"):
                        topology_plugins = plugin_registry.find_plugins(
                            plugin_type="agent", category="topology"
                        )
                    else:
                        # Fallback to direct import if registry methods not available
                        raise ImportError("Plugin registry methods not available")

                    for plugin in topology_plugins:
                        if plugin.provider_name == topology_type:
                            # Import the provider class
                            module_name = (
                                f"plugins.agent.topology.{topology_type}.provider"
                            )
                            module = importlib.import_module(module_name)
                            provider_class = getattr(
                                module, f"{topology_type.title()}TopologyProvider"
                            )
                            return provider_class(config)
                except (ImportError, AttributeError):
                    logger.debug("Plugin registry not available, trying direct import")

                # If not found in plugins, fallback to dynamic import
                module = importlib.import_module(
                    f".{topology_type}", package=__package__
                )
                provider_class = getattr(module, f"{topology_type.title()}Topology")
                return provider_class(config)
            except (ImportError, AttributeError) as e:
                # Fallback to try direct import
                try:
                    module = importlib.import_module(
                        f".{topology_type}", package=__package__
                    )
                    provider_class = getattr(module, f"{topology_type.title()}Topology")
                    return provider_class(config)
                except (ImportError, AttributeError):
                    raise TopologyError(
                        f"Invalid topology type '{topology_type}': {e}"
                    ) from e
    except Exception as e:
        logger.error(f"Failed to create topology provider '{topology_type}': {e}")
        raise TopologyError(
            f"Failed to create topology provider '{topology_type}': {e}"
        ) from e
