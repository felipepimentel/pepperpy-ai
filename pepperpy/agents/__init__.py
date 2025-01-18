"""Agent module for different AI frameworks."""

from pepperpy.agents.autogen_agent import AutoGenAgent
from pepperpy.agents.crewai_agent import CrewAIAgent
from pepperpy.agents.factory import AgentFactory
from pepperpy.agents.interfaces import AgentCapabilities, BaseAgent, Message
from pepperpy.agents.langchain_agent import LangChainAgent
from pepperpy.agents.semantic_kernel_agent import SemanticKernelAgent

# Main factory function for creating agents
create_agent = AgentFactory.create

__all__ = [
    "AgentCapabilities",
    # Factory class (if needed for registration)
    "AgentFactory",
    # Agent implementations
    "AutoGenAgent",
    # Base interfaces
    "BaseAgent",
    "CrewAIAgent",
    "LangChainAgent",
    "Message",
    "SemanticKernelAgent",
    # Main factory function
    "create_agent",
]
