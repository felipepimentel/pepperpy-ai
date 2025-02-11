"""Agent registry for managing and loading agents."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from pepperpy.hub.agents.base import BaseAgent
from pepperpy.hub.prompts import PromptRegistry


class AgentRegistry:
    """Registry for managing and loading agents."""

    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[str, Type[BaseAgent]] = {}

    def register_agent(
        self,
        name: str,
        agent_class_or_path: Union[Type[BaseAgent], str, Path],
    ) -> None:
        """Register an agent class or load from path.

        Args:
            name: Name to register the agent under
            agent_class_or_path: The agent class or path to agent definition

        """
        if isinstance(agent_class_or_path, type) and issubclass(
            agent_class_or_path, BaseAgent
        ):
            self._agents[name] = agent_class_or_path
        else:
            # TODO: Implement loading from path
            raise NotImplementedError("Loading agents from path not yet implemented")

    def load_agent(
        self,
        agent_id: str,
        config: Optional[Dict[str, Any]] = None,
        prompt_registry: Optional[PromptRegistry] = None,
    ) -> BaseAgent:
        """Load an agent by name.

        Args:
            agent_id: Name of the agent to load
            config: Optional configuration to override defaults
            prompt_registry: Optional prompt registry to use

        Returns:
            An initialized agent instance

        Raises:
            ValueError: If the agent is not found

        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent '{agent_id}' not found")

        agent_class = self._agents[agent_id]
        agent = agent_class(config=config or {}, prompt_registry=prompt_registry)
        return agent

    def has_agent(self, name: str) -> bool:
        """Check if an agent is registered.

        Args:
            name: Name of the agent to check

        Returns:
            True if the agent is registered, False otherwise

        """
        return name in self._agents

    def list_agents(self) -> List[str]:
        """Get a list of all registered agent names.

        Returns:
            List of registered agent names

        """
        return list(self._agents.keys())
