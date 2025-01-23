"""Agent factory for creating different types of agents."""

from typing import Any, ClassVar

from pepperpy.agents.interfaces import BaseAgent
from pepperpy.agents.providers.autogen_agent import AutoGenAgent
from pepperpy.agents.providers.crewai_agent import CrewAIAgent
from pepperpy.agents.providers.langchain_agent import LangChainAgent
from pepperpy.agents.providers.semantic_kernel_agent import SemanticKernelAgent


class AgentFactory:
    """Factory for creating agents."""

    _registry: ClassVar[dict[str, type[BaseAgent]]] = {
        "autogen": AutoGenAgent,
        "langchain": LangChainAgent,
        "crewai": CrewAIAgent,
        "semantic-kernel": SemanticKernelAgent,
    }

    @classmethod
    def register(cls, name: str, agent_class: type[BaseAgent]) -> None:
        """Register a new agent type."""
        cls._registry[name] = agent_class

    @classmethod
    async def create(
        cls, agent_type: str, config: dict[str, Any] | None = None
    ) -> BaseAgent:
        """Create an agent of the specified type."""
        config = config or {}

        if agent_type not in cls._registry:
            raise ValueError(
                f"Unknown agent type: {agent_type}. "
                f"Available types: {list(cls._registry.keys())}"
            )

        agent = cls._registry[agent_type]()
        await agent.initialize(**config)
        return agent
