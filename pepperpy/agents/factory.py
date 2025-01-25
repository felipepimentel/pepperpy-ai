"""Agent factory module for Pepperpy framework."""

import logging
from typing import Any, Dict, Optional, Type

from ..common.errors import PepperpyError
from ..core.lifecycle import ComponentLifecycleManager
from .base import BaseAgent
from .chat import ChatAgent
from .rag import RAGAgent


logger = logging.getLogger(__name__)


class AgentFactoryError(PepperpyError):
    """Agent factory error class."""
    pass


class AgentFactory:
    """Factory class for creating and configuring agents."""
    
    def __init__(self) -> None:
        """Initialize agent factory."""
        self._lifecycle_manager = ComponentLifecycleManager()
        self._agent_types: Dict[str, Type[BaseAgent]] = {
            "chat": ChatAgent,
            "rag": RAGAgent,
        }
    
    def register_agent_type(self, name: str, agent_type: Type[BaseAgent]) -> None:
        """Register a new agent type.
        
        Args:
            name: Agent type name.
            agent_type: Agent class.
            
        Raises:
            AgentFactoryError: If agent type registration fails.
        """
        if name in self._agent_types:
            raise AgentFactoryError(f"Agent type {name} is already registered")
        
        if not issubclass(agent_type, BaseAgent):
            raise AgentFactoryError(
                f"Agent type {name} must be a subclass of BaseAgent"
            )
        
        self._agent_types[name] = agent_type
    
    def create_agent(
        self,
        agent_type: str,
        name: str,
        llm: Any,
        capabilities: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        dependencies: Optional[Dict[str, Any]] = None
    ) -> BaseAgent:
        """Create and configure an agent.
        
        Args:
            agent_type: Type of agent to create.
            name: Agent name.
            llm: LLM provider instance.
            capabilities: Agent capabilities.
            config: Optional agent configuration.
            dependencies: Optional agent dependencies.
            
        Returns:
            Configured agent instance.
            
        Raises:
            AgentFactoryError: If agent creation fails.
        """
        if agent_type not in self._agent_types:
            raise AgentFactoryError(f"Unknown agent type: {agent_type}")
        
        try:
            agent_class = self._agent_types[agent_type]
            agent = agent_class(
                name=name,
                llm=llm,
                capabilities=capabilities,
                config=config
            )
            
            if dependencies:
                for dep_name, dep in dependencies.items():
                    self._lifecycle_manager.register(
                        dep_name,
                        dep,
                        dependencies=None
                    )
                
                self._lifecycle_manager.register(
                    name,
                    agent,
                    dependencies=list(dependencies.keys())
                )
            else:
                self._lifecycle_manager.register(name, agent)
            
            return agent
            
        except Exception as e:
            raise AgentFactoryError(f"Failed to create agent {name}: {e}")
    
    async def initialize_agent(self, agent: BaseAgent) -> None:
        """Initialize an agent and its dependencies.
        
        Args:
            agent: Agent to initialize.
            
        Raises:
            AgentFactoryError: If agent initialization fails.
        """
        try:
            await self._lifecycle_manager.initialize()
        except Exception as e:
            raise AgentFactoryError(f"Failed to initialize agent: {e}")
    
    async def terminate_agent(self, agent: BaseAgent) -> None:
        """Terminate an agent and its dependencies.
        
        Args:
            agent: Agent to terminate.
            
        Raises:
            AgentFactoryError: If agent termination fails.
        """
        try:
            await self._lifecycle_manager.terminate()
        except Exception as e:
            raise AgentFactoryError(f"Failed to terminate agent: {e}") 